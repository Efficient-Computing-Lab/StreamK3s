import os
import sys
import time
import logging
import json
import pika
import requests
from requests.auth import HTTPBasicAuth
import subprocess
from subprocess import PIPE

# from MessageThread import CustomThread
consumer_list = []
message_list = []
logging.getLogger().setLevel(logging.INFO)
user = os.getenv("RABBITMQ_USERNAME", "name")
rabbit_ip = os.getenv("POD_IP", "ip")
password = os.getenv("RABBITMQ_PASSWORD", "password")
application = "experiment-ais"
credentials = pika.PlainCredentials(user, password)
consume_connection = pika.BlockingConnection(
    pika.ConnectionParameters(host=rabbit_ip,
                              credentials=credentials,
                              virtual_host=application,
                              ))


def callback(ch, method, properties, body):
    # thread = CustomThread()
    # thread.start()
    # thread.join()

    my_json = body.decode('utf8')
    data = json.loads(my_json)
    ch.basic_ack(delivery_tag=method.delivery_tag)
    namespace = data.get("namespace")
    pod = data.get("pod")
    x = subprocess.Popen(["kubectl delete -n "+namespace+" pod "+pod],shell=True,stdout=PIPE,stderr=PIPE)
    stdout, stderr = x.communicate()
    if not "not found" in stderr.decode("utf-8"):
    	message = "pod "+ pod+ " deleted"
    else:
       message= "looking for pods"
    print(message)
    return message


def consume_message(topic):
    channel = consume_connection.channel()
    channel.basic_qos(prefetch_count=10)
    result = channel.basic_consume(queue=topic,
                                   auto_ack=False,
                                   on_message_callback=callback)
    print(' [*] Waiting for messages.')
    channel.start_consuming()
    return result

