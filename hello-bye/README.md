This workflow takes a string of either `hello` or `bye` as input, and returns
`Hello world!` or `Bye world!`. It tests branching capability.

The Step Functions implementation uses the `Choice` state. The unum
implementation uses `Conditional`.

The unum implementation uses hand-written configurations. To test it using the
test client, run `test-client.py --skip_frontend`. To restore, use
`test-client.py --skip_frontend -r`.