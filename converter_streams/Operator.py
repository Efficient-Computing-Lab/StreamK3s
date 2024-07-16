class Operator:

    def __init__(self, image, type, name, application, operator_type, port, arch, os, host, scale, queues, order, persistent_volume, dependencies, submodel):
        self.image = image
        self.type = type
        self.name = name
        self.application = application
        self.operator_type = operator_type
        self.port = port
        self.arch = arch
        self.os = os
        self.host = host
        self.scale = scale
        self.queues = queues
        self.order = order
        self.persistent_volume = persistent_volume,
        self.dependencies = dependencies
        self.submodel = submodel
    def get_host(self):
        return self.host

    def get_operator_type(self):
        return self.operator_type

    def get_port(self):
        return self.port

    def get_name(self):
        return self.name

    def get_application(self):
        return self.application

    def get_image(self):
        return self.image

    def get_order(self):
        return self.order

    def get_scale(self):
        return self.scale

    def get_queues(self):
        return self.queues

    def get_persistent_volume(self):
        return self.persistent_volume[0]

    def get_dependencies(self):
        return self.dependencies

    def get_submodel(self):
        return self.submodel