This hello world example consists of two functions: `Hello` and `World`.
`Hello` simply returns the string "Hello", and `World` takes the output of `Hello`
and concatenates the string "world".

This workflow doesn't require any input data.

Alternatively, you can specify a SQS queue and the `World` function will write its final
output to the SQS queue. See `events/sqs.json` for an example.

`events` directory contains example inputs to the application.
