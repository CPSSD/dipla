# get_binary service

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
