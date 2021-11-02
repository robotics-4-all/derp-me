FROM python:3.7

RUN pip install redis paho-mqtt pika ujson

COPY ./third_party/commlib-py /commlib

RUN cd /commlib && pip install .

COPY . /derpme

RUN cd /derpme && pip install .

WORKDIR /derpme/bin

ENV DERPME_BROKER_TYPE "REDIS"
ENV DERPME_BROKER_HOST "localhost"
ENV DERPME_BROKER_PORT 6379
ENV DERPME_BROKER_USERNAME ""
ENV DERPME_BROKER_PASSWORD ""

CMD ["derp_me"]
