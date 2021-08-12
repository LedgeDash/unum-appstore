# unum-appstore

## Test cases

### hello-world

Simple chaining. No fan-out metadata propagation.

Creation of session by `Start` function.

`NextInput: Scalar` 

### iot-pipeline

Simple chaining. No fan-out metadata propagation.

Creation of session by `Start` function.

`NextInput: Scalar` 

### hello-bye

`Start`' config:

Branching based on user function return value.

```json
"Next": [
		{
			"Name": "Hello",
			"Conditional": "$ret == 'hello'"
		},
		{
			"Name": "Bye",
			"Conditional": "$ret == 'bye'"
		}
	],
```

### text-processing

Parallel pipelines of different length

`Start`'s config:

`"Next": [{"Name": "UserMention"},{"Name": "FindUrl"}]`. Runtime metadata for parallel fan-out

`FindUrl`'s config:

Chaining inside a parallel fan-out. Runtime metadata propagated correctly.

`UserMention` and `ShortenUrl`'s config:

Parallel fan-in. Explicit function output name (e.g., "UserMention-unumIndex-0", "ShortenUrl-unumIndex-1").

Invoking fan-in function with the correct input

`CreatePost`'s input. Correct input for parallel fan-in function.

`CreatePost`'s config:

`Fan-out Modifiers` removing the runtime fan-out metadata.

### map

`UnumMap`'s config:

`"NextInput": "Map"`. Runtime metadata for map fan-out.

`F1`'s config:

`F1-unumIndex-*`. Fan-in on `*`. Expanding `*`.

Any one of the `F1` instances can invoke `Summary`. Multiple instances of `Summary` might run, *each with a different unum index and therefore outputing return values into the intermediary data store with different id*. For instance, with s3, we might see `Summary-unumIndex-0-output.json` and `Summary-unumIndex-1-output.json`.

### map-wait

`F1`'s config:

`Conditional: $0 == $size - 1`.

`Wait = true`

### parallel-pipeline

F3

only the last one performs the fan-in `Conditional: $0 == $size - 1`

Propagation of fan-out metadata within chains in a map fan-out.


### wordcount

Chain of map fan-outs.

`Partition` function has a `Fan-out Modifiers: ["Pop"]` and therefore should not embed the `Fan-out` field from its input to its output.

`Partition` function's return value can be named `Partition-unumIndex-5` but the `Reducer` function's return value cannot be `Reducer-unumIndex-5.0`. It should simply be `Reducer-unumIndex-0`.