# client_result service

## client to server

This is the message from the client to the server giving it the result of its computation.

The format of the message is as follows:

```js
{
    "label": "client_result",
    "data": {
        "type": "scraper_result",
        "value": {}
    }
}
```

The `type` field defines what kind of data this is. This will decide if it is used as the input to another task.

The `value` field can be of any shape, and is the actual value of the response.
