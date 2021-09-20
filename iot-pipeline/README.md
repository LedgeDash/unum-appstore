This iot-pipeline workflow consists of two functions: `aggregator` and
`hvac_controller`. `aggregator` takes an array of timestamped power usage data
as input, such as the following,

```json
[
  {"2021-02-20T08:30:00.000":120},
  {"2021-02-20T09:30:00.000":25.0},
  {"2021-02-20T10:30:00.000":211.2},
  {"2021-02-20T11:30:00.000":10}
]
```

and returns some aggregate statistics, for example,

```json
{
    "starting_tsp": "2021-02-20T08:30:00",
    "ending_tsp": "2021-02-20T11:30:00",
    "total_time": 240,
    "total_power_consumption": 366.2,
    "average_power_consumption": 1.5258333333333334
}

```

`hvac_controller` function takes the aggregate statistics and output a control
command on whether or not to reduce power, for example,

```json
{
    "timestamp": "2021-09-20T02:27:37.313",
    "reduce_power": 1
}

```

You can optionally pass in an SQS queue for the workflow's end result.
`hvac_controller` will write its results to that queue. See
`unum/events/sqs.json` and `step-functions/events/sqs.json` for examples.