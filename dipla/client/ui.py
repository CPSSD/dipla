import tkinter

class DiplaClientUI:
    def __init__(self, config, service_creator):
        self.config = config
        self.service_creator = service_creator
        self.client = None

    def run(self):
        self.client = Client(
            'ws://{}:{}'.format(
                self.config.params['server_ip'],
                self.config.params['server_port']),
            password=config.params['password']
        )
        services = self.service_creator(client)
        self.client.inject_services(services)
        self.client.start()