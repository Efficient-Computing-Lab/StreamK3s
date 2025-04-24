## TOSCA
The StreamK3s platform utilizes an extension of the TOSCA open standard by OASIS to outline the deployment and scaling of applications in Kubernetes and KEDA, respectively. TOSCA, on its own, can describe application components, as well as their deployment and runtime adaptation hosts, within topologies.

### TOSCA extension
Within this framework, two essential entities are required:

* A new entity named `Operator` was introduced to depict operators on our platform. It is derived from the default `tosca.nodes.SoftwareComponent`, which initially described software components.
* The default entity to describe hosts, including their hardware and OS capabilities in TOSCA, is `tosca.nodes.Compute`.

You can find the definitions of our custom extended language <a href=https://github.com/f-coda/Stream-Processing/tree/main/converter_streams/definitions>here</a>.
#### example
The following example is describing the deployment and scaling of two operators (Operator-1 and Operator-2) in our platform.
Operator-1 is connected with Host-1 via host requirement. Similarly, Operator-2 is connected with Host-2 with the usage of the same requirement.

<b>Operator Descriptions:</b>

| Properties    | Meaning                                                                                                                                                 |
|---------------|---------------------------------------------------------------------------------------------------------------------------------------------------------|
| image         | Name of the Docker image                                                                                                                                |
| name          | Name of the operator                                                                                                                                    |
| operator_type | An operator can be producer or subscriber                                                                                                               |
| order         | The deployment order of operators                                                                                                                       |
| queues        | Specify the queues with which the operator should establish communication. Each operator may have zero or one input_queue and zero or one output_queue. |
| scale         | It includes rules based on conditions supported by KEDA, which are associated with either MessageRate or QueueLength.                                   |
| port          | It lists the ports utilized by an operator.                                                                                                             |
| requirements  | It encompasses the host requirement linking an Operator with a Host, detailing the hardware prerequisites of the Operator.r                   |

<b>Host Descriptions:</b>

| Capabilities | Meaning                                                                       |
|--------------|-------------------------------------------------------------------------------|
| host         | It describes the computing power of a host in matters of CPU, RAM and disk    |
| os           | It describes the desired operating system in matters of architecture and type |


``` yaml
tosca_definitions_version: tosca_simple_yaml_1_2

description: Application model for streams architecture

imports:
  - /definitions/custom_types.yaml

topology_template:

  node_templates:

    Host-1:
      type: tosca.nodes.Compute
      capabilities:
        host:
          properties:
            num_cpus: 1
            mem_size: 512MB
            disk_size: 10GB
        os:
          properties:
            architecture: x86_64
            type: linux

    Host-2:
      type: tosca.nodes.Compute
      capabilities:
        host:
          properties:
            num_cpus: 1
            mem_size: 512MB
            disk_size: 2GB
        os:
          properties:
            architecture: x86_64
            type: linux



    Operator-1:
      type: Operator
      properties:
        image: gkorod/generator:v0.7
        name: generator
        application: experiment-ais
        operator_type: producer
        persistent_volume: true
        order: 1
        queues:
          properties:
            output_queue: queue-1
        port:
          - 20766
      requirements:
        - host: Host-1

    Operator-2:
      type: Operator
      properties:
        image: gkorod/grouper:v1.8
        name: grouper
        application: experiment-ais
        operator_type: subscriber
        persistent_volume: false
        order: 2
        dependencies:
          - operator_name: generator
        queues:
          properties:
            input_queue: queue-1
            output_queue: queue-2
        scale:
          - rule: 1
            condition: MessageRate = 16
            input_queue: queue-1
            scale: 3
          - rule: 2
            condition: QueueLength = 16
            input_queue: queue-1
            scale: 3
        port:
          - 20766
      requirements:
        - host: Host-2
```
The above example can be also found <a href=https://github.com/f-coda/Stream-Processing/tree/main/converter_streams/tosca_extension_example>here</a>.

**Important Note**: For cases where multiple scaling rules apply to the same operator—such as Operator-2 
in the example above—ensure that the scale value is consistent across all rules. This restriction exists
because the Converter generates KEDA ScaledObjects, which in turn create Kubernetes HPAs. 
Both definitions must share the same maxReplica value. Kubernetes does not support different maxReplica values
for each rule within the same HPA. Additionally, while Kubernetes may technically allow the creation
of multiple HPAs for the same deployment, this is generally considered bad practice and 
can lead to undesirable, hard-to-debug scaling behavior. It is recommended to use only one HPA per deployment.

### Converter
The Converter component functions as a reasoner tool capable of both reading and generating Kubernetes definition YAML files. It is seamlessly integrated with the Sommelier Validator. Initially, Sommelier Validator is employed to validate our TOSCA extension. Upon confirming the validity of the provided model, Converter is then able to generate the necessary files.

### Sommelier Validator

Sommelier is a tool capable of validating TOSCA application topologies. The introduction of Sommelier was initially documented in the following research paper:
 > _A. Brogi, A. Di Tommaso, J. Soldani. <br>
 > **Sommelier: A Tool for Validating TOSCA Application Topologies.** <br>
 > In: Pires L., Hammoudi S., Selic B. (eds) Model-Driven Engineering and Software Development. MODELSWARD 2017. Communications in Computer and Information Science, vol 880. Springer, Cham_


The code for Sommelier can be found in this <a href=https://github.com/di-unipi-socc/Sommelier>repository</a>.

### How Sommelier & Converter works in our Platform

1. An HTTP Post endpoint `\submit` within the `validate()` function is being provided by <a href=https://github.com/f-coda/Stream-Processing/blob/main/converter_streams/REST-API.py>REST-API.py</a>. This endpoint expects TOSCA data in JSON format from NodeRED. Upon receiving the TOSCA model, it is temporarily stored as a YAML file.
2. The temporary file is sent to Sommelier Validator through the `validation(path)` function in the <a href=https://github.com/f-coda/Stream-Processing/blob/main/converter_streams/sommelier.py>sommelier.py</a> script. This function validates TOSCA models in YAML format. Sommelier is capable of validating TOSCA models based on the definitions of the objects it recognizes.
3. If the submitted model is valid, the `ReadFile(content)` function from the <a href=https://github.com/f-coda/Stream-Processing/blob/main/converter_streams/Parser.py>Parser.py</a> script is invoked by REST-API.py. This function parses the model and creates lists containing the corresponding semantics.
4. Following this, REST-API.py invokes two functions from <a href=https://github.com/f-coda/Stream-Processing/blob/main/converter_streams/Converter.py>Converter.py</a> to produce the relevant Kubernetes YAML files. The first function, `namespace(namespace)`, generates the namespace responsible for hosting the application and sets up the necessary vhost on RabbitMQ. The second function, called `Converter.tosca_to_k8s(operator_list, host_list, namespace)`, retrieves lists of semantics describing operators/applications and hosts, in addition to the generated namespace. These details are utilized to deploy applications along with companion containers on the platform.
5. In the preceding phase, the Converter additionally creates a virtual host on RabbitMQ, segregating RabbitMQ for each application. It generates the designated output and input queues outlined in the TOSCA model, along with a termination queue. Each streaming application will possess its own termination queue, through which it will signal whether an operator has executed at least one of time its operation.
6. Subsequently, REST-API.py repeatedly invokes the `apply(data)` function from <a href=https://github.com/f-coda/Stream-Processing/blob/main/converter_streams/Kubernetes.py>Kubernetes.py</a> to deploy the generated files onto the Kubernetes cluster. The same function is being utilized to create configmaps that will configure the deployed containers to communicate with their companion container pair.
7. REST-API.py employs the `write_rules_config(operator_list)` function from the <a href=https://github.com/f-coda/Stream-Processing/blob/main/converter_streams/KEDA.py>KEDA.py</a> script. This function generates KEDA YAML files, encapsulating scale rules for the operators derived from the description provided in TOSCA models.
8. In the final step, REST-API.py utilizes its custom function called `edit_instancemanager_list(operator_list, output_queue_list)` to determine which operators need to scale and what their corresponding output queues are. Subsequently, it executes the `configure_instancemanager(list)` function to organize the output_list. It then sends each JSON object from the list, containing the application's namespace, output queue, operator's position in the workflow, and the operator's name, to the Instancemanager. Each K3s namespace has its dedicated vhost on RabbitMQ. The Instance Manager subscribes to this vhost and monitors the reported queues, identifying the instance pod that has completed its computations. Subsequently, it terminates this specific pod.
