This map workflow takes an array as its input. For every element of the array,
it executes one instance of the `F1` function. When all `F1` functions
complete, it invokes one instance of the `Summary` function. The `Summary`
function's input is the `F1` functions' outputs in an array with the same
order as the input array (i.e., the 1st item in `Summary`'s input array is the
output of the `F1` function whose input is the 1st item of the initial
workflow input array).

`F1` function simply reads a local file and returns the file content. We can
increase or decrease `F1`'s runtime and memory footprint by changing the file
size.

In this `map-wait` version, the unum implementation is hand-written as opposed
to be compiled from a Step Functions state machine. You'll see a `UnumMap0`
Lambda that serves as the workflow entry function, as well as
`unum_config.json` for every Lambda functions in the workflow. Note that
`f1/unum_config.json` as the `Wait` option turned on and the continuation
conditional set to `$0 == $size-1` such that the last `F1` Lambda instance
will wait for all the other `F1` instances to finish and perform and the
fan-in.

To run this workflow, use the `test-client.py --skip_frontend` option to skip
running the frontend compiler. To restore, use `test-client.py -r
--skip_frontend`