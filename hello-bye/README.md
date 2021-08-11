Branch based on user function output with `Conditional`.

The `Start` function should return the value of the `Value` field of the input event JSON. The unum runtime on `Start` should branch based on the user function's return value. The branch is a string comparison.

Branches are expressed as a list in unum config. Only the taken branch function will be invoked and its input will have a `Fan-out` field whose `Index` is the branch's position in the list.

The `World` function has `Pop` as a `Fan-out Modifier`.