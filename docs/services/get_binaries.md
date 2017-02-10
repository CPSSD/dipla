# get_binaries service

## client to server

This is the message from the client to the server asking for it to send the binaries.

The format of the message is as follows:

```js
{
    "label": "get_binaries",
    "data": {
        "platform":"win32",
        "quality": 0.31242089,
        "password": "dipla4ever"
    }
}
```

The `platform` field should have an identifier for the OS and architecture the client is running on, so the server knows what binary version to send - eg `win32`, `Linux x86-64`, etc.

The `quality` field should have a floating point value that gives an estimate of the quality of the client. Lower is better.

The `password` field is only required if the server has been set up to require a password. If the client does not send a password an appropriate ServiceError will be raised.

## server to client

The server sends the following to the client in response:

```js
{
    "label":"get_binaries",
    "data": {
        "base64_binaries": {
        	"add": "QVlZWVkgbG1hbw==",
        	"sub": "ZnVjayBhbGwgdGhlIG90aGVyIHRlYW1zLCBkaXBsYSBpcyB0b3A="
     	}
     }
}
```

The field `base64_binaries` here holds a dictionary that contains the task name paired with the base64'd binary.
