# get_binary service

## client to server

This is the message from the client to the server asking for it to send a binary.

The format of the message is as follows:

```js
{
    "label": "get_binary",
    "data": {
        "platform":"win32",
    }
}
```

The `platform` field should have an identifier for the OS and architecture the client is running on, so the server knows what binary version to send - eg `win32`, `Linux x86-64`, etc.

## server to client

The server sends the following to the client in response:

```js
{
    "label":"get_binary",
    "data": {
         "base64_binary": "sdfskfhlskfh",
     }
}
```

The field `base64_binary` here holds the raw binary data encoded in base64.
