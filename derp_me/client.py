from typing import Any

from commlib.logger import Logger

from commlib.endpoints import TransportType


class DerpMeClient(object):
    def __init__(self,
                 iface_protocol: TransportType = TransportType.REDIS,
                 conn_params: Any = None,
                 namespace: str = 'device'):
        """__init__.

        Args:
            iface_protocol: Interface protocol (REDIS/AMQP)
            conn_params: Broker Connection Parameters
            namespace: Global namespace
        """
        self.namespace = namespace
        self.logger = Logger(namespace=self.__class__.__name__)

        if iface_protocol == TransportType.AMQP:
            import commlib.transports.amqp as comm
        elif iface_protocol == TransportType.REDIS:
            import commlib.transports.redis as comm
        else:
            raise TypeError()
        self._conn_params = conn_params if conn_params \
            is not None else comm.ConnectionParameters()

        self._get_uri = '{}.{}.{}'.format(self.namespace, 'derpme', 'get')
        self._set_uri = '{}.{}.{}'.format(self.namespace, 'derpme', 'set')
        self._mget_uri = '{}.{}.{}'.format(self.namespace, 'derpme', 'mget')
        self._mset_uri = '{}.{}.{}'.format(self.namespace, 'derpme', 'mset')
        self._lget_uri = '{}.{}.{}'.format(self.namespace, 'derpme', 'lget')
        self._lset_uri = '{}.{}.{}'.format(self.namespace, 'derpme', 'lset')
        self._flush_uri = '{}.{}.{}'.format(self.namespace, 'derpme', 'flush')

        self._get_rpc = comm.RPCClient(conn_params=self._conn_params,
                                       rpc_name=self._get_uri)
        self._set_rpc = comm.RPCClient(conn_params=self._conn_params,
                                       rpc_name=self._set_uri)
        self._mget_rpc = comm.RPCClient(conn_params=self._conn_params,
                                        rpc_name=self._mget_uri)
        self._mset_rpc = comm.RPCClient(conn_params=self._conn_params,
                                        rpc_name=self._mset_uri)
        self._lget_rpc = comm.RPCClient(conn_params=self._conn_params,
                                        rpc_name=self._lget_uri)
        self._lset_rpc = comm.RPCClient(conn_params=self._conn_params,
                                        rpc_name=self._lset_uri)
        self._flush_rpc = comm.RPCClient(conn_params=self._conn_params,
                                         rpc_name=self._flush_uri)

    def get(self, key: str, persistent: bool = False):
        """get.
        Get value of a key.

        Args:
            key (str): key
            persistent (bool): persistent
        """
        req = {
            'key': key,
            'persistent': persistent
        }
        return self._get_rpc.call(req)

    def set(self, key: str, val: Any, persistent: bool = False):
        """set.
        Set the value of a key.

        Args:
            key:
            val:
        """
        req = {
            'key': key,
            'val': val,
            'persistent': persistent
        }
        return self._set_rpc.call(req)

    def mget(self, key: str, persistent: bool = False):
        """mget.

        Args:
            key (str): key
            persistent (bool): persistent
        """
        req = {
            'key': key,
            'persistent': persistent
        }
        return self._mget_rpc.call(req)

    def mset(self, keys: list, vals: list, persistent: bool = False):
        """mset.

        Args:
            keys (list): keys
            vals (list): vals
            persistent (bool): persistent
        """
        req = {
            'keys': keys,
            'vals': vals,
            'persistent': persistent
        }
        return self._mset_rpc.call(req)

    def lget(self, key: str, l_from: int, l_to: int, persistent: bool = False):
        """lget.

        Args:
            key (str): key
            l_from (int): l_from
            l_to (int): l_to
            persistent (bool): persistent
        """
        req = {
            'key': key,
            'l_from': l_from,
            'l_to': l_to,
            'persistent': persistent
        }
        return self._lget_rpc.call(req)

    def lset(self, key: str, vals: list, persistent: bool = False):
        """lset.

        Args:
            key (str): key
            vals (list): vals
            persistent (bool): persistent
        """
        req = {
            'key': key,
            'vals': vals,
            'persistent': persistent
        }
        return self._lset_rpc.call(req)

    def flush(self):
        """flush.
        Flush data currently stored in db.
        """
        return self._flush_rpc.call({})
