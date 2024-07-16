## Description

This dummy operator, intended for deployment in StreamK3s, is meant to be placed within the same container as the companion container in a pod. Its sole purpose is to facilitate the exchange of messages on a RabbitMQ broker and does not involve any sophisticated operations since our primary objective is to test communication between the two containers.

## dummy_operator.py
This represents the main script within the example container, employing a function named `receive_connection()`. This function is crafted to establish a connection with the queue specified in the TOSCA model, enabling the retrieval of messages. The companion container's endpoint details are provided via environment variables: `MY_POD_IP`, `API_PORT`, and `CONSUME_PATH`.

To facilitate message reception, the operator container must feature an HTTP Post endpoint. To meet this requirement, the <a href=https://github.com/f-coda/Stream-Processing/blob/main/operator/dummy_operator.py>dummy_operator</a> operates <a href=https://github.com/f-coda/Stream-Processing/blob/main/operator/Interface.py>Interface.py</a> as a separate thread, employing the `start_service()` function.

## Interface.py

This script is designed to support two essential functions: sending and receiving messages. The sending process is executed through the `send(message)` function, which sends messages individually. For message reception, the example container employs a function called `post()`, establishing an HTTP Post endpoint named `/post_message`. This endpoint handles messages one at a time, storing them in a list.

### Messages
Our platform necessitates operators to exchange messages for effective communication. There are two message types within our platform:

1. Messages exchanged between operators.
2. Reporting messaged on the termination topic. 

The output topic is meant to store the operation results. Developers are expected to utilize the JSON format, although there is no fixed structure they must follow. For example, an operator responsible for compression could send a message resembling the following format:

``` json
{"pod": "compressor","operation": "compressed messages"}
```
The termination message, found in the termination topic, should include the pod's name, its parent namespace, and the operation status marked as `ended`. The structure is as follows:
``` json
 {"pod": "compressor", "namespace": "test", "status": "ended"}
 ```
Developers can extract the pod name and namespace from the `MY_POD_NAME` and `MY_POD_NAMESPACE` environment variables.

### How to send messages
The provided code serves as an illustration of how to modify Interface.py to create a custom operator. In our specific scenario, this code successfully executed compression when the message count reached 1000. Additionally, it performed another compression when it received the message `{"transmission":"ended"}` from its input queue. This particular message indicated that there was no more data to be transmitted, as communicated by the preceding operator.

During the final compression process, the operator dispatched both messages to its designated output queue and the termination queue. Developers are not required to specify the destination queue for the messages; this task is autonomously handled by the companion container.

Using the sleep command after dispatching a message on the termination queue is essential. This measure acts as a failsafe, guaranteeing that the operator refrains from processing any additional messages.
``` python
import logging
import os
import time
import threading
from multiprocessing import Process

import ais_manipulator
import flask
from flask import Flask
import dummy_operator
import json

app = Flask(__name__)
message_list = []
logging.getLogger().setLevel(logging.INFO)
pod_name = os.getenv("MY_POD_NAME", "#name")
namespace = os.getenv("MY_POD_NAMESPACE", "#namespace")


def data_format(dict_from_string):
    mmsi = dict_from_string.get('mmsi')
    imo = dict_from_string.get('imo')
    dict_from_string["imo"] = int(imo)
    navigational_status = dict_from_string.get('navigational_status')
    dict_from_string["navigational_status"] = int(navigational_status)
    longitude = dict_from_string.get('longitude')
    dict_from_string["longitude"] = float(longitude)
    latitude = dict_from_string.get('latitude')
    dict_from_string["latitude"] = float(latitude)
    heading = dict_from_string.get('heading')
    dict_from_string["heading"] = float(heading)
    cog = dict_from_string.get('cog')
    dict_from_string["cog"] = float(cog)
    sog = dict_from_string.get('sog')
    dict_from_string["sog"] = float(sog)
    ship_type = dict_from_string.get('ship_type')
    dict_from_string["ship_type"] = int(ship_type)
    draught = dict_from_string.get('draught')
    dict_from_string["draught"] = float(draught)
    size_bow = dict_from_string.get('size_bow')
    dict_from_string["size_bow"] = int(size_bow)
    size_stern = dict_from_string.get('size_stern')
    dict_from_string["size_stern"] = int(size_stern)
    size_port = dict_from_string.get('size_port')
    dict_from_string["size_port"] = int(size_port)
    size_starboard = dict_from_string.get('size_starboard')
    dict_from_string["size_starboard"] = int(size_starboard)
    anchored = dict_from_string.get('anchored')
    dict_from_string["anchored"] = float(anchored)
    manoeuvring = dict_from_string.get('manoeuvring')
    dict_from_string["manoeuvring"] = float(manoeuvring)
    moored = dict_from_string.get('moored')
    dict_from_string["moored"] = float(moored)
    underway = dict_from_string.get('underway')
    dict_from_string["underway"] = float(underway)

    return dict_from_string


def handle_request(dict_from_string):
    message_list.append(dict_from_string)
    # [dict(t) for t in {tuple(d.items()) for d in message_list}]
    logging.info('message_list_size: ' + str(len(message_list)))
    if len(message_list) > 1000:
        ais_manipulator.compression_procedure(message_list)
        logging.info('compression ended')
        dummy_operator.send(
            {'pod': pod_name, 'namespace': namespace 'status': 'compression ended'})
        dummy_operator.send({'pod':pod_name,'operation': 'compressed ' + str(len(message_list)) + " messages"})
        message_list.clear()
        time.sleep(200)


@app.route("/post_message", methods=["POST"])
def post():
    json_data = flask.request.get_json()
    logging.info(type(json_data))
    if json_data != '{"transmission": "ended"}':
        dict_from_string = json.loads(json_data)
        dict_from_string = data_format(dict_from_string)
        handle_request(dict_from_string)
        return 'message received'

    if json_data == '{"transmission": "ended"}':
        logging.info('transmission ended')
        if len(message_list) > 0:
            ais_manipulator.compression_procedure(message_list)
            logging.info('compression ended')
            dummy_operator.send(
                {'pod': pod_name, 'namespace': namespace, 'status': 'ended'})
            dummy_operator.send({'pod':pod_name,'operation': 'compressed ' + str(len(message_list)) + " messages"})
            message_list.clear()
            time.sleep(200)
        return 'transmission ended'



app.run(host="0.0.0.0", port=4322, debug=False, use_reloader=False, threaded=False)

```
## Build image

Each operator needs to be dockerized and hosted in a public repository. Otherwise, our Stream Processing Platform will not be able to access it.

``` shell
docker build -f Dockerfile -t operator:v0.1 .
docker tag operator:v0.1 gkorod/operator:v0.1
docker push gkorod/operator:v0.1
```
