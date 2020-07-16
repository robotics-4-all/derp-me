#!/usr/bin/env python

"""Main module."""

import redis
import json
import time
import re
from enum import Enum

from derp_me import DerpMe, RedisMemParams
import commlib_py.transports.redis as rcomm


if __name__ == '__main__':
    derp = DerpMe(mem_conn_params=RedisMemParams(host='localhost', port=6379, db=1),
                  broker_conn_params=rcomm.ConnectionParameters(host='localhost', port=6379))
    derp.run_forever()
