import tempfile
import re
import Kubernetes
import oyaml as yaml
import os
import logging
import base64

logging.basicConfig(filename='std.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s')
logging.getLogger().setLevel(logging.INFO)


def write_rules_config(operatorlist):
    values = [operator.get_application() for operator in operatorlist]
    # Check if all values are the same
    if all(v == values[0] for v in values):
        namespace= values[0]
        configure_rabbitmq_connection(namespace)
    else:
        logging.info("Namespace cannot be different between the operators")
    for operator in operatorlist:
        deployment = operator.get_name()
        rule_list = operator.get_scale()
        if rule_list is not None:
            for rule in rule_list:
                rule['deployment'] = deployment
                logging.info(rule)
                deployment_name = rule.get('deployment')
                scale_name = deployment_name +"scale-rule-"+str(rule.get('rule'))
                logging.info(scale_name)
                condition = rule.get('condition')
                scale_up = rule.get('scale')
                if rule.get('output_queue'):
                    queue = rule.get('output_queue')
                if rule.get('input_queue'):
                    queue = rule.get('input_queue')
                if 'QueueLength' in condition:
                    condition_name = 'QueueLength'
                if 'MessageRate' in condition:
                    condition_name = 'MessageRate'
                value = int(re.search(r'\d+', condition).group())
                scale_object = {'apiVersion': 'keda.sh/v1alpha1',
                                'kind': 'ScaledObject',
                                'metadata': {'name': scale_name, 'namespace': namespace},
                                'spec': {'scaleTargetRef': {'name': deployment_name}, 'pollingInterval': 5, 'cooldownPeriod': 10,
                                         'minReplicaCount': 1, 'maxReplicaCount': scale_up,
                                         'triggers': [
                                             {'type': 'rabbitmq',
                                              'metadata': {'protocol': 'http', 'queueName': queue,
                                                           'mode': condition_name,
                                                           'value': str(value)},
                                              'authenticationRef': {'name': 'keda-trigger-auth-rabbitmq-conn'}}]}}
                logging.info(scale_object)
                Kubernetes.apply(scale_object)

def configure_rabbitmq_connection(namespace):

    password = os.getenv("RABBITMQ_PASSWORD", "password")
    ip = os.getenv("POD_IP", "ip")
    username = 'user'
    uri = 'http://' + username + ":" + password + "@"+ip+":15672/" + namespace

    uri_bytes = uri.encode('ascii')
    base64_uri = base64.b64encode(uri_bytes)
    credentials = base64_uri.decode('ascii')

    secret_config = {'apiVersion': 'v1',
                             'kind': 'Secret',
                             'metadata': {'name': 'keda-rabbitmq-secret', 'namespace': namespace},
                             'data': {'host': credentials}}
    Kubernetes.apply(secret_config)
    trigger_auth = {'apiVersion': 'keda.sh/v1alpha1',
                            'kind': 'TriggerAuthentication',
                            'metadata': {'name': 'keda-trigger-auth-rabbitmq-conn', 'namespace': namespace},
                            'spec': {
                                'secretTargetRef': [
                                    {'parameter': 'host', 'name': 'keda-rabbitmq-secret', 'key': 'host'}]}}
    Kubernetes.apply(trigger_auth)
