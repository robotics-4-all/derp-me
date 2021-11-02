#!/usr/bin/env python3
"""Main module."""

import os

from derp_me import DerpMe


def main():
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
    else:
        raise ValueError('Broker type not valid!')

    bparams = comm.ConnectionParameters(
        host=broker_host,
        port=broker_port
    )

    derp = DerpMe(broker_params=bparams, debug=True)
    derp.run_forever()
