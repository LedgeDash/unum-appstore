
# Original ExCamera



# gg's Implementation of ExCamera



# Binaries and Usage in the Step Function Implementation

The commands are based on makefiles generated by `gen_makefile.py`:

```bash
python gen_makefile.py 0 15 16 22 > excamera.mk
```

## Lessons from implementing ExCamera with Step Functions

Limited semantics/programmability of aggregation

1. Map states have to fan-in all branches. Dependency based graphs are more
   flexible and supercedes states with predefined behavior

No states for fold

1. The rebase step is a fold on an array. To make this workflow work on Step
   Functions, the rebase function has to be written as a recursive function
   that explicitly controls the stopping criteron in the user function code.
   unum can lift the fold/recursion logic up to the workflow level.




## vpxenc:

Input: `y4m` files

Input event: `{"bucket":"excamera-input", "file": "x.y4m"}`

Binary: `vpxenc` and `xc-terminate-chunk`

Commands: 

```bash
./vpxenc --ivf --codec=vp8 --good --cpu-used=0 --end-usage=cq --min-q=0 --max-q=63 --cq-level=22 --buf-initial-sz=10000 --buf-optimal-sz=20000 --buf-sz=40000 --undershoot-pct=100 --passes=2 --auto-alt-ref=1 --threads=1 --token-parts=0 --tune=ssim --target-bitrate=4294967295 -o /tmp/1-vpxenc.ivf /tmp/1.y4m

./xc-terminate-chunk /tmp/1-vpxenc.ivf /tmp/1-0.ivf
```

`vpxenc` is google's encoder. The `x-vpxenc.ivf` file produced is one key
frame followed by N interframes.

`xc-terminate-chunk` is a simple utility that modifies the metadata so that
things are not corrupt. The `x-0.ivf` files produced are essentially the same
as the `x-vpxenc.ivf` files; Still one key frame followed by N interframes.

Output: `x-0.ivf`

If the input is `1.y4m`, the output file uploaded to S3 is `1-0.ivf`. If the
input is `2.y4m`, the output file uploaded to S3 is `2-0.ivf`. So on and so
forth.

Return Value: `{"bucket": <bucket-name>, "file": <x-0.ivf>}`

## xcdec

Input: `x-0.ivf` files

Input event: `{"bucket": <bucket-name>, "file": <x-0.ivf>}`

Binary: `xc-dump`

Commands:

```bash
./xc-dump /tmp/1-0.ivf /tmp/1-0.state
```

Output: `x-0.state`

If the input is `1-0.ivf`, the output file uploaded to S3 is `1-0.state`. If the
input is `2-0.ivf`, the output file uploaded to S3 is `2-0.state`. So on and so
forth.

Return Value: `{"bucket":  <bucket-name>, "ivf file": <x-0.ivf>, "state": <x-0.state>}`

The `"ivf file"` field in the return value is the input file to `xcdec`.


## group

Group takes the output from the Step Functions Map state, which is an array of
`xcdec`'s return values.

Input event: 

```json
[
	{
      "bucket": "excamera-input",
      "ivf file": "1-0.ivf",
      "state": "1-0.state"
    },
    {
      "bucket": "excamera-input",
      "ivf file": "2-0.ivf",
      "state": "2-0.state"
    },
    {
      "bucket": "excamera-input",
      "ivf file": "3-0.ivf",
      "state": "3-0.state"
    },
    {
      "bucket": "excamera-input",
      "ivf file": "4-0.ivf",
      "state": "4-0.state"
    }
]
```

Binary: none

Commands: none

Return Value: 

```json
[
	{
      "bucket": "excamera-input",
      "prev state": "1-0.state",
      "ivf file": "2-0.ivf"
    },
    {
      "bucket": "excamera-input",
      "prev state": "2-0.state",
      "ivf file": "3-0.ivf"
    },
    {
      "bucket": "excamera-input",
      "prev state": "3-0.state",
      "ivf file": "4-0.ivf"
    }
]
```

The purpose of this group function is to take the array returned by the Map
state of `vpxenc` and `xcdec` and arrange it in the correct grouping and order
for the `reencode` function. Specifically, it groups the ith `.ivf` file from
`vpxenc` with the (i-1)th `.state` file from `xcdec`. The 1st `.ivf` file is
therefore skipped for reencode.

## reencode

Input: `x.y4m`, `x-0.ivf`,`(x-1)-0.state`

Input event: 

```json
{
	"bucket": "excamera-input",
	"prev state": "1-0.state",
	"ivf file": "2-0.ivf"
}
```

Binary: `xc-enc`

Commands:

```bash
./xc-enc -W -w 0.75 -i y4m -o /tmp/2-1.ivf -r -I /tmp/1-0.state -p /tmp/2-0.ivf -O /tmp/2-1.state /tmp/2.y4m
```

1. `-o /tmp/2-1.ivf` produces an interframe-only `ivf` file

2. `-O /tmp/2-1.state` produces new decoder state corresponding to the
   interframe-only `ivf` file

3. `-I /tmp/1-0.state` takes the previous chunk's `ivf` files decoder state
   (produced by running `x-0.ivf` through `xcdec`)

4. `/tmp/2.y4m` take the original raw video chunk as input

Output:

  1. `x-1.ivf`, this is the new interframe only ivf file

  2. `x-1.state`, this is the decoder state corresponding to the interframe
     only ivf file.

`x` is the number of the `ivf` file, e.g., 2 in `2-0.ivf`.

Both files are uploaded to S3.

Return Value:

```json
{
	"bucket": "excamera-input",
	"interframe-only ivf file": "2-1.ivf",
	"new decoder state": "2-1.state"
}
```

## rebase

rebase takes the output of the Map state of reencode functions, which is an
array.

rebase calls itself recursively each time with the array minus the 1st element
from the previous call (`event[1:]`).

Input:

1. The interframe-only decoder state in the 0th index of the array (e.g., `2-1.state`)

2. The interframe-only `ivf` file in the 1st index of the array (e.g., `3-1.ivf`)

3. The keyframe+interframe state in the 0th index of the array (e.g., `2-0.state`)

4. The original raw video in the 1st index of the array (e.g., `3.y4m`)

Input event:

```json
[
    {
      "bucket": "excamera-input",
      "interframe-only ivf file": "2-1.ivf",
      "new decoder state": "2-1.state"
    },
    {
      "bucket": "excamera-input",
      "interframe-only ivf file": "3-1.ivf",
      "new decoder state": "3-1.state"
    },
    {
      "bucket": "excamera-input",
      "interframe-only ivf file": "4-1.ivf",
      "new decoder state": "4-1.state"
    }
  ]
```

Binary: `xc-enc`

Command:

```bash
./xc-enc -W -w 0.75 -i y4m -o /tmp/3.ivf -r -I /tmp/2-1.state -p /tmp/3-1.ivf -S /tmp/2-0.state -O /tmp/3-1.state /tmp/3.y4m
```

Output:

1. `x.ivf` where x is the filename at the 1st index of the array

2. `x-1.state` where x is the filename at the 1st index of the array

Both files are uploaded to S3.

`x-1.state` overwrites the `x-1.state` file produced by the reencode function
in the previous step.

Return Value: None


# Binaries and Usage in the manual serverless implementation

## Lessons from manually implementing ExCamera in a purely serverless style

Programming aggregation is difficult:

1. For `xcdec` to invoke `xcenc`, both `xcdec` and the next chunk's `vpxenc`
   need to finish

2. We need to pick whether we want `xcdec` to invoke `xcenc` or `vpxenc` to
   invoke `xcenc` a prior. There's no mechanism for `xcdec` and `vpxenc` to
   synchronize at runtime.

3. Fold

Expressing conditions on whether to invoke the downstream function is manual.

1. The reencode function needs to manually check that it's the 2nd in the
   fan-out before invoking rebase



# Binaries and Usage in the unum Implementation

## vpxenc

Input event:

```json
{"bucket":"excamera-input-6frames-16chunks", "file": "00000000.y4m"}

{"bucket":"excamera-input-6frames-16chunks", "file": "00000001.y4m"}

{"bucket":"excamera-input-6frames-16chunks", "file": "00000002.y4m"}

{"bucket":"excamera-input-6frames-16chunks", "file": "00000003.y4m"}
```

Upload:

```bash
00000000-0.ivf
00000001-0.ivf
00000002-0.ivf
00000003-0.ivf
```

Return value:

```json
{"bucket":"excamera-input-6frames-16chunks", "file":"00000000-0.ivf"}

{"bucket":"excamera-input-6frames-16chunks", "file":"00000001-0.ivf"}

{"bucket":"excamera-input-6frames-16chunks", "file":"00000002-0.ivf"}

{"bucket":"excamera-input-6frames-16chunks", "file":"00000003-0.ivf"}
```


### Invocation of vpxenc

By UnumMap0:

```json
{
  "Name": "vpxenc",
  "InputType": "Map"
}
```

## xcdec

Input:

```json
{"bucket":"excamera-input-6frames-16chunks", "file":"00000000-0.ivf"}

{"bucket":"excamera-input-6frames-16chunks", "file":"00000001-0.ivf"}

{"bucket":"excamera-input-6frames-16chunks", "file":"00000002-0.ivf"}

{"bucket":"excamera-input-6frames-16chunks", "file":"00000003-0.ivf"}
```

Upload:

```bash
00000000-0.state
00000001-0.state
00000002-0.state
00000003-0.state
```

Return value:

```json
{"bucket": "excamera-input-6frames-16chunks", "ivf file": "00000000-0.ivf", "state": "00000000-0.state"}

{"bucket": "excamera-input-6frames-16chunks", "ivf file": "00000001-0.ivf", "state": "00000001-0.state"}

{"bucket": "excamera-input-6frames-16chunks", "ivf file": "00000002-0.ivf", "state": "00000002-0.state"}

{"bucket": "excamera-input-6frames-16chunks", "ivf file": "00000003-0.ivf", "state": "00000003-0.state"}
```



### Invocation of xcdec

By vpxenc:

```json
{
  "Name": "xcdec",
  "InputType": "Scalar",
  "Conditional": "$0 < $size-1"
}
```

## reencode

Input:

```json
[
    {"bucket":"excamera-input-6frames-16chunks", "file":"00000002-0.ivf"},
    {"bucket": "excamera-input-6frames-16chunks", "ivf file": "00000001-0.ivf", "state": "00000001-0.state"}
]

[
    {"bucket":"excamera-input-6frames-16chunks", "file":"00000003-0.ivf"},
    {"bucket": "excamera-input-6frames-16chunks", "ivf file": "00000002-0.ivf", "state": "00000002-0.state"}
]
```



Upload:

```bash
00000002-1.ivf
00000002-1.state

00000003-1.ivf
00000003-1.state
```



Return value:

```json
{"bucket": "excamera-input-6frames-16chunks", "interframe-only ivf file": "00000002-1.ivf", "new decoder state": "00000002-1.state"}

{"bucket": "excamera-input-6frames-16chunks", "interframe-only ivf file": "00000003-1.ivf", "new decoder state": "00000003-1.state"}
```



### Invocation of reencode

1. By vpxenc:

```json
{
    "Name": "reencode",
    "InputType": {
        "Fan-in": {
            "Values": [
                "vpxenc-unumIndex-$0",
                "xcdec-unumIndex-($0-1)" 
            ]
        }
    },
    "Conditional": "$0 > 1"
}
```

2. By xcdec:

```json
{
    "Name": "reencode",
    "InputType": {
        "Fan-in": {
            "Values": [
                "vpxenc-unumIndex-($0+1)",
                "xcdec-unumIndex-$0"
            ]
        }
    },
    "Conditional": "$0<$size-1 and $0>0"
}

"Next Payload Modifiers": ["$0=$0+1"]
```



## rebase

Input:

```json
[
    {"bucket":"excamera-input-6frames-16chunks", "file":"00000001-0.ivf"},
    {"bucket": "excamera-input-6frames-16chunks", "ivf file": "00000000-0.ivf", "state": "00000000-0.state"}
]

[
    {"bucket": "excamera-input-6frames-16chunks", "interframe-only ivf file": '00000001.ivf', "new decoder state": '00000001-1.state'},
    {"bucket": "excamera-input-6frames-16chunks", "interframe-only ivf file": "00000002-1.ivf", "new decoder state": "00000002-1.state"}
]

[
     {"bucket": "excamera-input-6frames-16chunks", "interframe-only ivf file": '00000002.ivf', "new decoder state": '00000002-1.state'},
    {"bucket": "excamera-input-6frames-16chunks", "interframe-only ivf file": "00000003-1.ivf", "new decoder state": "00000003-1.state"}
]
```



Upload:

```bash
00000001.ivf
00000001-1.state

00000002.ivf
00000002-1.state

00000003.ivf
00000003-1.state
```



Return value:

```json
 {"bucket": "excamera-input-6frames-16chunks", "interframe-only ivf file": '00000001.ivf', "new decoder state": '00000001-1.state'}

 {"bucket": "excamera-input-6frames-16chunks", "interframe-only ivf file": '00000002.ivf', "new decoder state": '00000002-1.state'}

{"bucket": "excamera-input-6frames-16chunks", "interframe-only ivf file": "00000003.ivf", "new decoder state": "00000003-1.state"}
```



### Invocation of rebase

1. By vpxenc:

```json
{
    "Name": "rebase",
    "InputType": {
        "Fan-in": {
            "Values": [
                "vpxenc-unumIndex-$0",
                "xcdec-unumIndex-($0-1)" 
            ]
        }
    },
    "Conditional": "$0 == 1"
}
```

2. By xcdec:

```json
{
    "Name": "rebase",
    "InputType": {
        "Fan-in": {
            "Values": [
                "vpxenc-unumIndex-($0+1)",
                "xcdec-unumIndex-$0"
            ]
        }
    },
    "Conditional": "$0==0"
}
```

3. By reencode:

```json
{
    "Name": "rebase",
    "InputType": {
        "Fan-in": {
            "Values": [
                "rebase-unumIndex-($0-1)",
                "reencode-unumIndex-$0"
            ]
        }
    },
}
```

4. By rebase

```json
{
    "Name": "rebase",
    "InputType": {
        "Fan-in": {
            "Values": [
                "rebase-unumIndex-$0",
                "reencode-unumIndex-($0+1)"
            ]
        }
    },
    "Conditional": "$0 < $size-1",
}
```

# Input for Experiments

Sadjad has a bucket of 6-frame chunks (`y4m` files) of the `sintel-1k` video
that was used in the original ExCamera paper:

https://s3.console.aws.amazon.com/s3/buckets/excamera-us-west-2?region-use-west-2%3Fregion=us-west-2&prefix=sintel-1k-y4m_06%2F&region=us-west-2



# Comparison with Step Functions implementation

User functions are exactly the same between the Step Function implementation
and the unum implementation



# Comparison with the original ExCamera and gg

The original excamera, each function outputs results (`.ivf`, and `.s` files)
to s3? The paper didn't talk about this explicitly. In fact, it's more likely
that the `.ivf` files are sent as binary from one worker to the other (when
necessary) via the rendezvous server.

The gg paper mentioned the communication aspect with more details:

"The original ExCamera communicated video-codec states over TCP between
workers. gg routes thunks to workers that already have the necessary data, but
brokers inter-worker communication through S3." (Section 4.3)

So similar to our implementation, gg also uses s3 for sending data between
Lambdas but it has more smarts in placement.

## Experimental setup

Input data: 6 frames per chunk, 16 chunks per batch.

The gg evaluation's input is a video with 888 *chunks*. All chunks were
uploaded to S3 as `y4m` files prior to execution.

The original ExCamera used a 64-core VM (`m4.16xlarge`) as the rendezvous
server to broker TCP streams between Lambda workers.

I couldn't find the Lambda memory size gg or ExCamera used for their
experiments.

See Section 5.4 of gg for details and the results.
