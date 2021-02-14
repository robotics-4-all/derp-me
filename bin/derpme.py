#!/usr/bin/env python

"""Main module."""

import os
import redis
import json
import time
import re
from enum import Enum

from derp_me import DerpMe


if __name__ == '__main__':
    try:
        broker_type = os.environ['DERPME_BROKER_TYPE']
    except KeyError as e:
        broker_type = 'REDIS'
    try:
        broker_host = os.environ['DERPME_BROKER_HOST']
    except KeyError as e:
        broker_host = 'localhost'
    try:
        broker_port = os.environ['DERPME_BROKER_PORT']
    except KeyError as e:
        broker_port = None
    try:
        broker_username = os.environ['DERPME_BROKER_USERNAME']
    except KeyError as e:
        broker_username = ''
    try:
        broker_password = os.environ['DERPME_BROKER_PASSWORD']
    except KeyError as e:
        broker_password = ''

    if broker_type in ('redis', 'REDIS', 'Redis'):
        import commlib.transports.redis as comm
        if broker_port is None:
            broker_port = 6379
    elif broker_type in ('amqp', 'AMQP'):
        import commlib.transports.amqp as comm
        if broker_port is None:
            broker_port = 5672
    elif broker_type in ('mqtt', 'MQTT'):
        import commlib.transports.mqtt as comm
        if broker_port is None:
            broker_port = 1883

    bparams = comm.ConnectionParameters(
        host=broker_host,
        port=broker_port
    )
    print(bparams.host)

    derp = DerpMe(broker_params=bparams, debug=True)
    derp.run_forever()
