# run_instructions service

## server to client

This message is sent to a client by the server to tell it to execute something on some input values. These messages are sent to multiple clients to distribute the processing demands.

The format of the message is as follows:

```js
{
    "label": "run_instructions",
    "data": {
         "task_instructions": "task_name",
         "task_uid": "ae54nsao2",
         "data": [1, 2, 3, 4, 5]
    }
}
```

The `task_instructions` field contains the name of the task, which the client can use to work out which binary it should run

The `task_uid` field is the identifier of the particular instance of the task that this message corresponds to. The results from this should be returned to that task instance

The `data` field is the set of actual values that should be used in executing the the binary to get results
