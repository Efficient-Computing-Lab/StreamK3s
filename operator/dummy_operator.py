import json
import os
import subprocess
import threading
import time
import logging
import flask
from flask import Flask
import requests as requests

pod_ip = os.getenv("MY_POD_IP", "192.168.1.2")
api_port = os.getenv("API_PORT", "4321")
publish_path = os.getenv("PUBLISH_PATH", "/post_message")
consume_path = os.getenv("CONSUME_PATH", "/get_message")
model_distributor_ip = os.getenv("MODEL_DISTRIBUTOR_IP")
model_distributor_port = os.getenv("MODEL_DISTRIBUTOR_PORT")
model_distributor_path = os.getenv("MODEL_DISTRIBUTOR_PATH")
submodel = os.getenv("SUBMODEL")
logging.getLogger().setLevel(logging.INFO)


def start_service():
    subprocess.call(['python3', 'Interface.py'])


def download_submodel():
    ip = 'http://' + model_distributor_ip + ':' + model_distributor_port + model_distributor_path + '/' + submodel
    save_path = '/opt/model/' + submodel
    try:
        # Send the GET request to download the file
        response = requests.get(ip, stream=True)

        # Check if the request was successful
        if response.status_code == 200:
            # Open a file in write-binary mode to save the downloaded content
            with open(save_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)
            print(f"File '{submodel}' downloaded successfully and saved to '{save_path}'.")
        else:
            print(f"Failed to download the file. Status code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")


def receive_connection():
    ip = 'http://' + pod_ip + ':' + api_port + consume_path
    logging.info(ip)
    get_message = requests.get(ip)
    if get_message.status_code == 200:
        response = "successfully received message from API"
    else:
        response = "couldn't reach API, status error code: " + str(get_message.status_code)
    logging.info(response)


start_download = threading.Thread(target=download_submodel)
start_download.start()
start_flask_service = threading.Thread(target=start_service)
start_flask_service.start()
time.sleep(15)
start_receive_connection = threading.Thread(target=receive_connection)
start_receive_connection.start()
