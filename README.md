# unum-appstore

## Test cases

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
