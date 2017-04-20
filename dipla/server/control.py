def start_server(server):
    server.should_distribute_tasks = True


def stop_server(exit_function):
    exit_function()
