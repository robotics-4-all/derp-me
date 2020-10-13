"""Main module."""

import redis
import json
import time
import re
from enum import IntEnum

from commlib.logger import RemoteLogger
from commlib.node import Node, TransportType


def camelcase_to_snakecase(name):
    """camelcase_to_snakecase.
    Converts a camelcase string to snakecase.

    Args:
        name: String
    """
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


class LocalMemType(IntEnum):
    """LocalMemType.
    """

    REDIS = 1


class Memory:
    def __init__(self, list_size=10):
        self.list_size = list_size

    def set(self, key: str, val: str) -> None:
        raise NotImplementedError()

    def get(self, key: str):
        raise NotImplementedError()

    def mset(self, keys: list, vals: list) -> None:
        raise NotImplementedError()

    def mget(self, keys: list):
        raise NotImplementedError()

    def lset(self, key: str, vals: list) -> None:
        raise NotImplementedError()

    def lget(self, key: str, from_idx: int, to_idx: int) -> list:
        raise NotImplementedError()

    def llen(self, key) -> int:
        raise NotImplementedError()


class RuntimeMemory(Memory):
    def __init__(self, *args, **kwargs):
        super(RuntimeMemory, self).__init__(*args, **kwargs)


class PersistentMemory(Memory):
    def __init__(self, *args, **kwargs):
        super(PersistentMemory, self).__init__(*args, **kwargs)


class RedisRuntimeMem(RuntimeMemory):
    def __init__(self, host='localhost', port=6379, db=1, *args, **kwargs):
        super(RedisRuntimeMem, self).__init__(*args, **kwargs)
        self._redis = redis.Redis(
            host=host,
            port=port,
            db=db,
            decode_responses=True
        )

    def set(self, key: str, val: str) -> None:
        self._redis.set(key, val)

    def get(self, key: str):
        val = self._redis.get(key)
        return val

    def mset(self, keys: list, vals: list) -> None:
        _d = {}
        for i in range(len(keys)):
            _d[keys[i]] = vals[i]
        self._redis.mset(_d)

    def mget(self, keys: list):
        vals = self._redis.mget(keys)
        return vals

    def lset(self, key: str, vals: list) -> None:
        self._redis.lpush(key, *vals)
        self._redis.ltrim(key, 0, self.list_size - 1)

    def lget(self, key: str, from_idx: int, to_idx: int) -> list:
        r_start = -1 * from_idx
        r_stop = -1 * to_idx
        res = self._redis.lrange(key, r_start, r_stop)
        return res

    def llen(self, key: str) -> int:
        return self._redis.llen(key)

    def flush(self) -> None:
        self._redis.flushdb()


class RedisPersistentMem(PersistentMemory):
    def __init__(self, host='localhost', port=6379, db=2, *args, **kwargs):
        super(RedisPersistentMem, self).__init__(*args, **kwargs)
        self._redis = redis.Redis(
            host=host,
            port=port,
            db=db,
            decode_responses=True
        )

    def set(self, key: str, val: str) -> None:
        self._redis.set(key, val)
        try:
            self._redis.bgsave()
        except Exception as exc:
            print(exc)

    def get(self, key: str):
        val = self._redis.get(key)
        return val

    def mset(self, keys: list, vals: list) -> None:
        _d = {}
        for i in range(len(keys)):
            _d[keys[i]] = vals[i]
        self._redis.mset(_d)
        try:
            self._redis.bgsave()
        except Exception as exc:
            print(exc)

    def mget(self, keys: list):
        vals = self._redis.mget(keys)
        return vals

    def lset(self, key: str, vals: list) -> None:
        self._redis.lpush(key, *vals)
        self._redis.ltrim(key, 0, self.list_size - 1)
        try:
            self._redis.bgsave()
        except Exception as exc:
            print(exc)

    def lget(self, key: str, from_idx: int, to_idx: int) -> list:
        r_start = -1 * from_idx
        r_stop = -1 * to_idx
        res = self._redis.lrange(key, r_start, r_stop)
        return res

    def llen(self, key: str) -> int:
        return self._redis.llen(key)


class DerpMe(object):
    """

    KeyVal Mem mechanism. Implemented using Redis as the backend db.
    Supports the following operations:
        - Simple Key-Val storage
        - List Key-Val storage. Where key points to a list
    """

    def __init__(self,
                 runtime_mem: LocalMemType = LocalMemType.REDIS,
                 persistent_mem: LocalMemType = LocalMemType.REDIS,
                 broker_type: TransportType = TransportType.REDIS,
                 broker_params=None,
                 list_size: int = 10,
                 namespace: str = 'device',
                 debug: bool = False):
        """__init__.

        Args:
            local_mem (LocalMemType): local_mem
            broker_type (TransportType): broker_type
            broker_params:
            list_size (int): list_size
            namespace (str): namespace
            debug (bool): debug
        """
        self.l_size = list_size
        self.namespace = namespace
        self._debug = debug
        self._broker_type = broker_type
        self._broker_params = broker_params
        self.node_name = camelcase_to_snakecase(self.__class__.__name__)

        self._get_uri = '{}.{}.{}'.format(self.namespace, 'derpme', 'get')
        self._set_uri = '{}.{}.{}'.format(self.namespace, 'derpme', 'set')
        self._mget_uri = '{}.{}.{}'.format(self.namespace, 'derpme', 'mget')
        self._mset_uri = '{}.{}.{}'.format(self.namespace, 'derpme', 'mset')
        self._lget_uri = '{}.{}.{}'.format(self.namespace, 'derpme', 'lget')
        self._lset_uri = '{}.{}.{}'.format(self.namespace, 'derpme', 'lset')
        self._flush_uri = '{}.{}.{}'.format(self.namespace, 'derpme', 'flush')

        if runtime_mem == LocalMemType.REDIS:
            self._runtime_mem = RedisRuntimeMem()
        else:
            raise ValueError()
        if persistent_mem == LocalMemType.REDIS:
            self._persistent_mem = RedisPersistentMem()
        else:
            raise ValueError()
        self._init_endpoints()

    def _init_endpoints(self):
        """_init_endpoints.
        Initialize remote node and it's interfaces.
        """
        thing_id = self._broker_params.credentials.username
        self._node = Node(
            self.node_name, transport_type=self._broker_type,
            transport_connection_params=self._broker_params,
            remote_logger=False,
            debug=self._debug
        )
        self.logger = self._node.get_logger()
        self._get_rpc = self._node.create_rpc(
            rpc_name=self._get_uri, on_request=self._callback_get)
        self._set_rpc = self._node.create_rpc(
            rpc_name=self._set_uri, on_request=self._callback_set)
        self._lget_rpc = self._node.create_rpc(
            rpc_name=self._lget_uri, on_request=self._callback_lget)
        self._lset_rpc = self._node.create_rpc(
            rpc_name=self._lset_uri, on_request=self._callback_lset)
        self._mget_rpc = self._node.create_rpc(
            rpc_name=self._mget_uri, on_request=self._callback_mget)
        self._mset_rpc = self._node.create_rpc(
            rpc_name=self._mset_uri, on_request=self._callback_mset)
        self._flush_rpc = self._node.create_rpc(
            rpc_name=self._flush_uri, on_request=self._callback_flush)
        self._get_rpc.run()
        self._set_rpc.run()
        self._lget_rpc.run()
        self._lset_rpc.run()
        self._mget_rpc.run()
        self._mset_rpc.run()
        self._flush_rpc.run()

    def _callback_get(self, msg, meta):
        """_callback_get.
        Returns the value of a key.

        Args:
            msg: Request Message
            meta: Message Metainformation
        """
        persistent = False
        resp = {
            'status': 1,
            'val': None,
            'error': ''
        }
        if not 'key' in msg:
            resp['error'] = 'Missing <key> parameter'
            resp['status'] = 0
        if 'persistent' in msg:
            if msg['persistent']:
                persistent = True
        key = msg['key']
        if persistent:
            self.logger.debug('[Persistent Mem]: GET <{}>'.format(key))
            val = self._persistent_mem.get(key)
        else:
            self.logger.debug('[Runtime Mem]: GET <{}>'.format(key))
            val = self._runtime_mem.get(key)
        resp['val'] = val
        return resp

    def _callback_set(self, msg, meta):
        """_callback_set.
        Set the value of a key.

        Args:
            msg: Request Message
            meta: Message Meta-Information
        """
        persistent = False
        resp = {
            'status': 1,
            'error': ''
        }
        if not 'key' in msg:
            resp['status'] = 0
            resp['error'] = 'Missing <key> parameter'
            return resp
        if not 'val' in msg:
            resp['status'] = 0
            resp['error'] = 'Missing <key> parameter'
            return resp
        if 'persistent' in msg:
            if msg['persistent']:
                persistent = True
        key = msg['key']
        val = msg['val']
        if persistent:
            self.logger.debug('[Persistent Mem]: SET <{},{}>'.format(key, val))
            self._persistent_mem.set(key, val)
            try:
                self._persistent_mem.bgsave()
            except Exception:
                pass
        else:
            self.logger.debug('[Runtime Mem]: SET <{},{}>'.format(key, val))
            self._runtime_mem.set(key, val)
        return resp

    def _callback_mset(self, msg, meta):
        """_callback_mset.
        Store Multiple sets of [keys, values]

        Args:
            msg: Request Message
            meta: Message Meta-Information
        """
        persistent = False
        resp = {
            'status': 1,
            'error': ''
        }
        if not 'keys' in msg:
            resp['status'] = 0
            resp['error'] = 'Missing <keys> parameter'
            return resp
        if not 'vals' in msg:
            resp['status'] = 0
            resp['error'] = 'Missing <vals> parameter'
            return resp
        if 'persistent' in msg:
            if msg['persistent']:
                persistent = True
        keys = msg['keys']
        vals = msg['vals']
        _d = {}
        for i in range(len(keys)):
            _d[keys[i]] = vals[i]
        if persistent:
            self.logger.debug('[Persistent Mem]: MSET <{},{}>'.format(keys, vals))
            self._persistent_mem.mset(_d)
            try:
                self._persistent_mem.bgsave()
            except Exception:
                pass
        else:
            self.logger.debug('[Runtime Mem]: MSET <{},{}>'.format(keys, vals))
            self._runtime_mem.mset(_d)
        return resp

    def _callback_mget(self, msg, meta):
        """_callback_mget.

        Args:
            msg: Request Message
            meta: Message Meta-Information
        """
        persistent = False
        resp = {
            'status': 1,
            'error': '',
            'vals': []
        }
        if not 'keys' in msg:
            resp['status'] = 0
            resp['error'] = 'Missing <keys> parameter'
            return resp
        if 'persistent' in msg:
            if msg['persistent']:
                persistent = True
        keys = msg['keys']
        if persistent:
            self.logger.debug('[Persistent Mem]: MGET <{}>'.format(keys))
            vals = self._persistent_mem.mget(keys)
        else:
            self.logger.debug('[Runtime Mem]: MGET <{}>'.format(keys))
            vals = self._runtime_mem.mget(keys)
        resp['vals'] = vals
        return resp

    def _callback_lget(self, msg, meta):
        """_callback_lget.
        Modified Redis LGET operation. Returns a list given its key.

        Args:
            msg: Request Message
            meta: Message Meta-Information
        """
        # from: 0 0
        # to:   0 -1
        persistent = False
        resp = {
            'status': 1,
            'error': '',
            'val': []
        }
        if not 'key' in msg:
            resp['status'] = 0
            resp['error'] = 'Missing <key> parameter'
            return resp
        if not 'l_from' in msg:
            resp['status'] = 0
            resp['error'] = 'Missing <l_from> parameter'
            return resp
        if not 'l_to' in msg:
            resp['status'] = 0
            resp['error'] = 'Missing <l_to> parameter'
            return resp
        if 'persistent' in msg:
            if msg['persistent']:
                persistent = True
        _from = msg['l_from']
        _to = msg['l_to']
        _key = msg['key']

        if self._runtime_mem.llen(_key) == 0:
            # Check if list exists: https://redis.io/commands/llen
            resp['status'] = 0
            resp['error'] = 'List <{}> does not exist'.format(_key)
            return resp
        if persistent:
            self.logger.debug(
                '[Persistent Mem]: LGET <{},[{},{}]>'.format(_key, _from, _to))
            res = self._persistent_mem.lget(_key, _from, _to)
        else:
            self.logger.debug(
                '[Runtime Mem]: LGET <{},[{},{}]>'.format(_key, _from, _to))
            res = self._runtime_mem.lget(_key, _from, _to)
        res = [json.loads(x) for x in res]
        resp['val'] = res
        return resp

    def _callback_lset(self, msg, meta):
        """_callback_lset.
        Modified Redis LSET operation

        Args:
            msg: Request Message
            meta: Message Meta-Information
        """
        persistent = False
        resp = {
            'status': 1,
            'error': ''
        }
        if not 'key' in msg:
            resp['status'] = 0
            resp['error'] = 'Missing <key> parameter'
            return resp
        if not 'vals' in msg:
            resp['status'] = 0
            resp['error'] = 'Missing <vals> parameter'
            return resp
        if 'persistent' in msg:
            if msg['persistent']:
                persistent = True
        key = msg['key']
        vals = msg['vals']
        vals = [json.dumps(x) for x in vals]
        if persistent:
            self.logger.debug(
                '[Persistent Mem]: LSET <{},{}>'.format(key, vals))
            self._persistent_mem.lset(key, vals)
        else:
            self.logger.debug('[Runtime Mem]: LSET <{},{}>'.format(key, vals))
            self._runtime_mem.lset(key, vals)
        return resp

    def _callback_flush(self, msg, meta):
        """_callback_flush.
        Force to flush data currently stored in db.

        Args:
            msg: Request Message
            meta: Message Meta-Information
        """
        resp = {
            'status': 1,
            'error': ''
        }
        self.logger.debug('Flushing db...')
        try:
            self._runtime_mem.flush()
        except Exception as exc:
            print(exc)
            resp['status'] = 0
            resp['error'] = str(exc)
        return resp

    def run_forever(self):
        """run_forever.
        """
        while True:
            time.sleep(0.001)
