#!/usr/bin/env python

from derp_me.client import DerpMeClient
from derp_me.derp_me import DerpMe


if __name__ == '__main__':
    derp = DerpMe()
    # derp.run_forever()
    client = DerpMeClient()
    print('xccc')
    client.flush()
    print('xccc')
    client.set('k1', 1)
    client.set('k1', 2)
    client.set('k1', 3)
    l = client.lget('k1', 0, -1)
