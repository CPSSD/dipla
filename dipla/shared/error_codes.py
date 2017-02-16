from enum import IntEnum


class ErrorCodes(IntEnum):
    """
    An enum shared between client and server used to represent errors
    that are transmitted between them

    0 - User ID is already taken. 1 - Server websocket loop. This error
    can only occur because some kind of unexpected error has occured in
    the websocket recevie loop
    2 - Invalid Binary Key. This means that the client or server has
    attempted to access a binary, but the ID that it used to identify
    the binary was not present in the key -> binary map
    3 - Password Required. This error occurs when a client tries to
    download one or more binaries from a server that requires a
    password, but the client did not provide any password
    4 - Password Invalid. This error occurs when a client tries to
    download one or more binaries from a server that requires a
    password, but the password provided by the client did not match
    the password on the server
    5 - No Binaries Present. This occurs if the key -> binary map does
    not exist on a machine
    """
    user_id_already_taken = 0
    server_websocket_loop = 1
    invalid_binary_key = 2
    password_required = 3
    invalid_password = 4
    no_binaries_present = 5
