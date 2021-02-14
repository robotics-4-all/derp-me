FROM python:3.7

RUN pip install redis paho-mqtt pika ujson

COPY ./third_party/commlib-py /commlib

RUN cd /commlib && pip install .

COPY . /derpme

RUN cd /derpme && pip install .

WORKDIR /derpme/bin

CMD ["python", "-u", "derpme.py"]
