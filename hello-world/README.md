

Scenario: chain (`hello` function is `Scalar`, single next). 

No fan-in, no propagating runtime metadata additional to the intermediary session context.

# Execution

Execute gmaithe `hello-world` workflow by invoking the `hello` function.

## Input

This workflow doesn't require any input data. See `events/trigger.json` for an example of an empty unum input.

Alternatively, you can specify a SQS queue and the `world` will write its final outputs to the SQS queue.

## Output

Optionally, the `world` function writes to a SQS queue.