#API for Server-Client Communications

All messages between the server and client (in both directions) should be in JSON format, in the following pattern:

```js
{
	"label": "example_label",
	"data": {
		"example_field": "example_value",
	},
}
```

`label` should contain the type of message that is being sent. This can be used by the receiver to figure out how or where it should be processed.

`data` should contain the actual data of the message. The `data` field can have a different format for each kind of message, and this format should be explained in a separate document for that service. Every message with the same `label` should have the `data` in the same format.

To ease parsing, all messages should include both of the above fields, even if they are empty. 

There is no `"success" : true"` or equivalent field, as if an error needs to be transmitted, the format above can be used to signal that.
