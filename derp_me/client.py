import commlib.transports.redis as rcomm
import commlib.transports.amqp as acomm
from commlib.logger import Logger

from .derp_me import TransportType


class DerpMeClient(object):
    def __init__(self, iface_protocol=TransportType.REDIS,
                 conn_params=None, namespace='device'):
        """__init__.

        Args:
            iface_protocol: Interface protocol (REDIS/AMQP)
            conn_params: Broker Connection Parameters
            namespace: Global namespace
        """
        self.namespace = namespace
        self.logger = Logger(namespace=self.__class__.__name__)

        if iface_protocol == TransportType.AMQP:
            comm = acomm
        elif iface_protocol == TransportType.REDIS:
            comm = rcomm
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

    def get(self, key):
        """get.
        Get value of a key.

        Args:
            key:
        """
        req = {
            'key': key
        }
        return self._get_rpc.call(req)

    def set(self, key, val):
        """set.
        Set the value of a key.

        Args:
            key:
            val:
        """
        req = {
            'key': key,
            'val': val
        }
        return self._set_rpc.call(req)

    def mget(self, key):
        """mget.

        Args:
            key:
        """
        req = {
            'key': key
        }
        return self._mget_rpc.call(req)

    def mset(self, keys, vals):
        """mset.

        Args:
            keys:
            vals:
        """
        req = {
            'keys': keys,
            'vals': vals
        }
        return self._mset_rpc.call(req)

    def lget(self, key, l_from, l_to):
        """lget.

        Args:
            key:
            l_from:
            l_to:
        """
        req = {
            'key': key,
            'l_from': l_from,
            'l_to': l_to
        }
        return self._lget_rpc.call(req)

    def lset(self, key, vals):
        """lset.

        Args:
            key:
            vals:
        """
        req = {
            'key': key,
            'vals': vals
        }
        return self._lset_rpc.call(req)

    def flush(self):
        """flush.
        Flush data currently stored in db.
        """
        return self._flush_rpc.call({})
