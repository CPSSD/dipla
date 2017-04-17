def start_server(server):
    server.distribute_tasks()


def stop_server(exit_function):
    exit_function()
