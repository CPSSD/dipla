def start_server(server):
    server.should_distribute_tasks = True
    server.distribute_tasks()


def stop_server(exit_function):
    exit_function()
