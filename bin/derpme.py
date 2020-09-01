#!/usr/bin/env python

"""Main module."""

import redis
import json
import time
import re
from enum import Enum

from derp_me import DerpMe
import commlib.transports.redis as rcomm


if __name__ == '__main__':
    derp = DerpMe(local_broker_params=rcomm.ConnectionParameters(host='localhost', port=6379))
    derp.run_forever()
