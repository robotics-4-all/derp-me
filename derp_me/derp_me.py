"""Main module."""

import redis
import json
import time
import re
from enum import Enum

from commlib.logger import Logger
import commlib.transports.redis as rcomm


def camelcase_to_snakecase(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


class RedisMemParams(rcomm.ConnectionParameters):
    def __init___(self, *args, **kwargs):
        super(RedisMemParams, self).__init__(*args, **kwargs)


class InterfaceProtocolType(Enum):
    AMQP = 1
    REDIS = 2


class DerpMe(object):
    """

    KeyVal Mem mechanism. Implemented using Redis as the backend db.
    Supports the following operations:
        - Simple Key-Val storage
        - List Key-Val storage. Where key points to a list
    """

    def __init__(self, mem_conn_params=None,
                 iface_protocol=InterfaceProtocolType.REDIS,
                 broker_conn_params=None,
                 list_size=10, namespace='device'):
        self.mem_conn_params = mem_conn_params if mem_conn_params is not None \
            else RedisMemParams()
        self.l_size = list_size
        self.namespace = namespace
        self.node_name = camelcase_to_snakecase(self.__class__.__name__)
        self.logger = Logger(namespace=self.node_name, debug=True)

        self._get_uri = '{}.{}.{}'.format(self.namespace, 'derpme', 'get')
        self._set_uri = '{}.{}.{}'.format(self.namespace, 'derpme', 'set')
        self._mget_uri = '{}.{}.{}'.format(self.namespace, 'derpme', 'mget')
        self._mset_uri = '{}.{}.{}'.format(self.namespace, 'derpme', 'mset')
        self._lget_uri = '{}.{}.{}'.format(self.namespace, 'derpme', 'lget')
        self._lset_uri = '{}.{}.{}'.format(self.namespace, 'derpme', 'lset')
        self._flush_uri = '{}.{}.{}'.format(self.namespace, 'derpme', 'flush')

        if iface_protocol == InterfaceProtocolType.AMQP:
            import commlib.transports.amqp as comm
        elif iface_protocol == InterfaceProtocolType.REDIS:
            import commlib.transports.redis as comm
        else:
            raise TypeError()

        self._conn_params = broker_conn_params if broker_conn_params \
            is not None else comm.ConnectionParameters()

        self._get_rpc = comm.RPCService(conn_params=self._conn_params,
                                       rpc_name=self._get_uri,
                                       on_request=self._callback_get)
        self._set_rpc = comm.RPCService(conn_params=self._conn_params,
                                       rpc_name=self._set_uri,
                                       on_request=self._callback_set)
        self._mget_rpc = comm.RPCService(conn_params=self._conn_params,
                                        rpc_name=self._mget_uri,
                                        on_request=self._callback_mget)
        self._mset_rpc = comm.RPCService(conn_params=self._conn_params,
                                        rpc_name=self._mset_uri,
                                        on_request=self._callback_mset)
        self._lget_rpc = comm.RPCService(conn_params=self._conn_params,
                                        rpc_name=self._lget_uri,
                                        on_request=self._callback_lget)
        self._lset_rpc = comm.RPCService(conn_params=self._conn_params,
                                        rpc_name=self._lset_uri,
                                        on_request=self._callback_lset)
        self._flush_rpc = comm.RPCService(conn_params=self._conn_params,
                                         rpc_name=self._flush_uri,
                                         on_request=self._callback_flush)

        self.init_redis()
        self._init_broker_endpoints()

    def _init_broker_endpoints(self):
        self._get_rpc.run()
        self._set_rpc.run()
        self._lget_rpc.run()
        self._lset_rpc.run()
        self._mget_rpc.run()
        self._mset_rpc.run()
        self._flush_rpc.run()

    def _callback_get(self, msg, meta):
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
        #self.log('MSET: {}'.format(_d))
        self.redis.mset(_d)
        return resp

    def _callback_mget(self, msg, meta):
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
        #self.log("LSET - key={}, vals={}".format(key, vals))
        self.redis.lpush(key, *vals)
        self.redis.ltrim(key, 0, self.l_size - 1)
        return resp

    def _callback_flush(self, msg, meta):
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
        self.redis = redis.Redis(host=self.mem_conn_params.host,
                                 port=self.mem_conn_params.port,
                                 db=self.mem_conn_params.db,
                                 decode_responses=True)

    def run_forever(self):
        while True:
            time.sleep(0.001)
