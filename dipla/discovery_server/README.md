# Dipla Discovery Server

The Discovery Server is a directory server, keeping a list of currently active pprojects. A potential volunteer to a project does not need to know the specific address and port of the project they want to contribute to if they instead connect to an always-on discovery server, as it will be able to provide that information.

The discovery server provides the following REST endpoints. Every response should be in Json format, and should contain a `success` field with a boolean value to signify if the operation had any errors or not. If `success` is `false`, the response should also include a string field `error` with human-readable information about what went wrong.

## /get_servers

This is a GET request that takes no parameters, and returns a json document like the following:

```js
{
	"success": true,
	"servers": [
		{
			"address": "123.56.67.89:9876",
			"title": "Laundry Folding",
			"description": "Protein folding is so 2007, it's time to fold some laundry"
		}
	]
}
```

An example request is `curl discovery.server.nu/get_servers`.

## /add_server

This is a POST request that requires the following fields:

- `address`: a valid address of a dipla project server, in the form `protocol:host:port`.
- `title`: the human-readable title of the gievn project.
- `description`: more information about the project.

It returns a json document that looks like the following:

```js
{
	"success": true
}
```

If there is already a project registered at the given address, a HTTP error 409 will be returned. If the given address is not resolvable, a HTTP error 400 will be returned

An example request is `curl -XPOST discovery.server.solutions/add_server -F address="http://dipla.website:90210" -F title="bitcoin4me" -F description="Contribute your resources to my bitcoin wallet"`.
