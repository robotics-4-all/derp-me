#!/usr/bin/env python

"""Main module."""

import redis
import json
import time
import re
from enum import Enum

from derp_me import DerpMe


if __name__ == '__main__':
    transport = 'redis'
    if transport == 'redis':
        import commlib.transports.redis as comm
    elif transport == 'amqp':
        import commlib.transports.amqp as comm

    derp = DerpMe(broker_params=comm.ConnectionParameters(
        host='tektrain-redis', port=6379), debug=True)
    derp.run_forever()
