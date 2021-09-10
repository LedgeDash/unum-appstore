# unum-appstore

Each application contains a unum implementation (under directory `unum`) and a
Step Functions implementation (under directory `step-functions`).

## Step Functions Implementations

Step Functions implementations contain

  1. User functions, each in its own directory
  2. An `events` directory with example workflow inputs
  3. A `template.yaml` for deploying the user functions and the Step Functions
     state machine with AWS SAM.

Note that the Step Functions state machine definition is in `template.yaml` and
is deployed using AWS SAM as a Cloudformation stack along with the user Lambda
functions. The advantage of defining state machines inside `template.yaml` is
that we can *programmatically insert Lambda ARNs into the state machine
definitions as SAM deploys the stack*.

As an example, let's look at the `hello-world` app. The state machine is named
`HelloWorldSF` under `Resources`. Its `Type: AWS::StepFunctions::StateMachine`
indicates that it's a Step Functions state machine. The `DefinitionString` under
`Properties` defines the state machine.  The definition string starts with
`!Sub` which is a Cloudformation intrinsic function (see
[here](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/intrinsic-function-reference-sub.html)
for more details). It replaces `${helloArn}` with `!GetAtt [ HelloFunction, Arn
]` and `${worldArn}` with `!GetAtt [ WorldFunction, Arn ]` during the
Cloudformation stack creation process.  `!GetAtt [ HelloFunction, Arn ]` will
get `HelloFunction`'s Arn once it's deployed.

After deployment completes, you'll find a Step Function whose name starts with
`HelloWorldSF` on AWS.

### How to deploy

To deploy a Step Functions workflow, use AWS SAM.

Make sure you have the aws cli, aws sam cli and an AWS account correctly created
and configured. Then use

```bash
sam build
```

to build the stack. You'll see a `.aws-sam` directory after build succeeds.

Then use the `sam deploy` command to deploy your stack to AWS. You can either
run

```bash
sam deploy --guided
```

which guides you through the deployment process. Make sure you pick a unique
name for your stack (by default, SAM uses the generic name `sam-app`).

Or you can specify deployment options directly, for example,

```bash
sam deploy --stack-name hello-world-sf --capabilities CAPABILITY_AUTO_EXPAND CAPABILITY_IAM --s3-bucket aws-sam-cli-managed-default-samclisourcebucket-1p6wkdqwc2lfe --region us-west-1 --s3-prefix hello-world-sf
```


## unum Implementations

## User Functions

User functions in both implementations are identical.

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

### excamera

`Vpxenc`'s config

`Conditional: $0 <$size -1`. The last `Vpxenc` does not invoke its continuation (which is `Xcdec`)

`Xcdec`'s config

`Fan-out Modifiers: [$0 = $0+1]`, increments the Fan-out Index so that the invoked `Reencode` function's input is `event["Fan-out"]["Index"]` is 1 greater than the invoker `Xcdec`'s `event["Fan-out"]["Index"]`.

```
"NextInput": {
        "Fan-in": {
            "Values": [
                "Xcdec-unumIndex-$0",
                "Vpxenc-unumIndex-($0+1)"
            ]
        }
}
```

`($0+1)` expressions when expanding value names.



`Reencode`'s config

`Conditional: $0 == 1` only the first `Reencode` function invokes the `Rebase` function.

`Fan-in: Values: [Reencode-unumIndex-$0, Reencode-unumIndex-($0+1)]`







