#!/usr/bin/env python

from derp_me.client import DerpMeClient
from derp_me.derp_me import DerpMe


if __name__ == '__main__':
    client = DerpMeClient()
    client.flush()
    client.set('k1', 1)
    k = client.get('k1')
    print(k)
    client.lset('k2', [1])
    client.lset('k2', [2])
    client.lset('k2', [3])
    l = client.lget('k2', 0, -2)
    print('Response: {}'.format(l))
    client.set('k1', 1, True)
    k = client.get('k1', True)
