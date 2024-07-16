import os

import Converter
import Host
import MessageBroker
import Operator
from Operator import Operator
import KEDA

home = str(os.getcwd())


def ReadFile(json):
    operator_list = []
    host_list = []

    topology = json.get('topology_template')
    node_template = topology.get('node_templates')
    node_names = node_template.keys()
    for x in node_names:
        node = node_template.get(x)
        type = node.get('type')
        properties = node.get('properties')
        if 'Operator' in type:
            name = properties.get('name')
            application = properties.get('application')
            operator_type = properties.get('operator_type')
            port = properties.get('port')
            image = properties.get('image')
            order = properties.get('order')
            scale = properties.get('scale')
            queues = properties.get('queues')
            persistent_volume = properties.get('persistent_volume')
            dependencies = properties.get('dependencies',None)
            submodel = properties.get('submodel')
            requirements = node.get('requirements')
            host = requirements[0].get('host')
            operator_list.append(
                Operator(image, type, name, application, operator_type, port, arch, os, host, scale, queues, order, persistent_volume,dependencies, submodel))
        if 'tosca.nodes.Compute' in type:
            capabilities = node.get('capabilities')
            instance = capabilities.get('host')
            host_properties = instance.get('properties')
            cpu = host_properties.get('num_cpus')
            if not cpu:
                cpu = 0.5
            ram = host_properties.get('mem_size')
            disk = host_properties.get('disk_size')
            os_system = capabilities.get('os')
            os_properties = os_system.get('properties')
            arch = os_properties.get('architecture')
            os_value = os_properties.get('type')
            host_list.append(Host.Host(type, x, cpu, ram, disk, arch, os_value))

    operator_list.sort(key=lambda x: x.order)

    Host.sort_hosts(host_list, operator_list)
    return operator_list, host_list, application
