# Error Codes

This document explains the error codes contained in the shared folder of dipla

0 - User ID is already taken. This means that an attempt has been made to add a new worker to the collection on the server, but the chosen UID is already in use
1 - Server websocket loop. This error can only occur because some kind of unexpected error has occured in the websocket recevie loop
2 - Invalid Binary Key. This means that the client or server has attempted to access a binary, but the ID that it used to identify the binary was not present in the key -> binary map
3 - Password Required. This error occurs when a client tries to download one or more binaries from a server that requires a password, but the client did not provide any password
4 - Password Invalid. This error occurs when a client tries to download one or more binaries from a server that requires a password, but the password provided by the client did not match the password on the server
5 - No Binaries Present. This occurs if the key -> binary map does not exist on a machine
