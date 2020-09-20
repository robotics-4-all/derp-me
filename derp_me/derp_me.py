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


class DerpMe(object):
    """

    KeyVal Mem mechanism. Implemented using Redis as the backend db.
    Supports the following operations:
        - Simple Key-Val storage
        - List Key-Val storage. Where key points to a list
    """

    def __init__(self,
                 local_mem: LocalMemType = LocalMemType.REDIS,
                 broker_type: TransportType = TransportType.REDIS,
                 broker_params=None,
                 list_size: int = 10,
                 namespace: str = 'device',
                 debug: bool = False):
        if local_mem == LocalMemType.REDIS:
            from commlib.transports.redis import ConnectionParameters
            self.mem_conn_params = ConnectionParameters()
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

        self.init_redis()
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
        resp = {
            'status': 1,
            'val': None,
            'error': ''
        }
        if not 'key' in msg:
            resp['error'] = 'Missing <key> parameter'
            resp['status'] = 0
        key = msg['key']
        self.logger.debug('GET <{}>'.format(key))
        val = self.redis.get(key)
        resp['val'] = val
        return resp

    def _callback_set(self, msg, meta):
        """_callback_set.
        Set the value of a key.

        Args:
            msg: Request Message
            meta: Message Meta-Information
        """
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
        key = msg['key']
        val = msg['val']
        self.logger.debug('SET <{},{}>'.format(key, val))
        self.redis.set(key, val)
        return resp

    def _callback_mset(self, msg, meta):
        """_callback_mset.
        Store Multiple sets of [keys, values]

        Args:
            msg: Request Message
            meta: Message Meta-Information
        """
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
        keys = msg['keys']
        vals = msg['vals']
        self.logger.debug('MSET <{},{}>'.format(keys, vals))
        _d = {}
        for i in range(len(keys)):
            _d[keys[i]] = vals[i]
        self.redis.mset(_d)
        return resp

    def _callback_mget(self, msg, meta):
        """_callback_mget.

        Args:
            msg: Request Message
            meta: Message Meta-Information
        """
        resp = {
            'status': 1,
            'error': '',
            'vals': []
        }
        if not 'keys' in msg:
            resp['status'] = 0
            resp['error'] = 'Missing <keys> parameter'
            return resp
        keys = msg['keys']
        self.logger.debug('MGET <{}>'.format(keys))
        try:
            vals = self.redis.mget(keys)
            resp['vals'] = vals
        except Exception as e:
            resp['status'] = 0
            resp['error'] = str(e)
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
        _from = msg['l_from']
        _to = msg['l_to']
        _key = msg['key']

        if self.redis.llen(_key) == 0:
            # Check if list exists: https://redis.io/commands/llen
            resp['status'] = 0
            resp['error'] = 'List <{}> does not exist'.format(_key)
            return resp
        # Reverse indexing
        r_start = -1 * _from
        r_stop = -1 * _to
        self.logger.debug('LGET <{},[{},{}]>'.format(_key, _from, _to))
        res = self.redis.lrange(_key, r_start, r_stop)
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
        key = msg['key']
        vals = msg['vals']
        vals = [json.dumps(x) for x in vals]
        self.logger.debug('LSET <{},{}>'.format(key, vals))
        self.redis.lpush(key, *vals)
        self.redis.ltrim(key, 0, self.l_size - 1)
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
            self.redis.flushdb()
        except Exception as exc:
            resp['status'] = 0
            resp['error'] = str(exc)
        return resp

    def init_redis(self):
        """init_redis.
        Initialize redis db instance for data storage.
        """
        self.redis = redis.Redis(host=self.mem_conn_params.host,
                                 port=self.mem_conn_params.port,
                                 db=self.mem_conn_params.db,
                                 decode_responses=True)

    def run_forever(self):
        """run_forever.
        """
        while True:
            time.sleep(0.001)
