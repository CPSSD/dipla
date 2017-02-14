from enum import Enum


class ErrorCodes(Enum):
    """
    An enum shared between client and server used to represent errors
    that are transmitted between them
    """
    user_id_already_taken = 0
    server_websocket_loop = 1
    invalid_binary_key = 2
    password_required = 3
    invalid_password = 4
