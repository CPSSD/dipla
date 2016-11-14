# runtime\_error message format

All errors sent betweent the client and server should adhere to the following format.

```js
{
	"label": "runtime_error",
	"data": {
		"details": "Exception occured trying to run binary X",
		"code": 8,
	}
}
```

The `details` field should contain some human-readable information giving a clue where to start looking for the cause of the error, eg. the contents of an exception.
The `code` field should contain a unique numerical code for the given error type, that can be used by the receiver to figure out how to respond.
