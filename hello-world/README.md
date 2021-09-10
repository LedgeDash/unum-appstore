This hello-world workflow consists of two functions: `hello` and `world`.
`hello` simply returns the string `"Hello"`; `world` takes the output of `hello`
and concatenates the string `"world"`.

## Input

This workflow doesn't require any input data.

Alternatively, you can specify a SQS queue and the `world` will write its final
outputs to the SQS queue.

## Output

Optionally, the `world` function writes to a SQS queue.
