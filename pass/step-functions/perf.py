'''
Run the map workflow at different fan-out size: 2,4,8,16,32, 64, 128,256, 512

Each fan-out function (F1) only gets a single byte of input and F1 simply
return event.

Measure the end-to-end latency by looking at the Step Function logs
'''

import time
import subprocess
import json
from datetime import datetime
import pytz

LOCAL_TZ = pytz.timezone('America/Chicago')

STEP_FUNCTIONS_ARN = "arn:aws:states:us-west-1:746167823857:stateMachine:PassMicroSF-n4WvP8A2AQiW"

NANO_TO_MILLI = 1000000
NUM_RUNS =10


def main():
    # Lambda's input payload size limit: 256 KB for async invocations
    sizes = [5*i for i in range(0,52)]

    final_result = {}

    for sz in sizes:
        print(f'\n*************Payload Size: {sz}KB*************\n')

        # create payload
        input_payload = "b"*sz*1024
        with open('input-tmp.json', 'w') as f:
                f.write(json.dumps(input_payload))

        # invoke the step functions NUM_RUNS times
        start_tsp = datetime.now(LOCAL_TZ) # will only consider executions that happen after this timestamp

        for i in range(NUM_RUNS):
            time.sleep(1)

            ret = subprocess.run(["aws", "stepfunctions", "start-execution",
                                      "--state-machine-arn", STEP_FUNCTIONS_ARN,
                                      "--input", f'file://input-tmp.json'
                                      ],
                                      capture_output=True)
            if ret.returncode != 0:
                print(f'Step Functions invocation failed: {ret.stderr.decode("utf-8")}')
            else:
                print(f'Iteration {i}: \n\t{json.loads(ret.stdout)}')

        time.sleep(10)
        # Get the execution history
        # The execution history follows the general format below:
        # TaskStateEntered          First       2
        # LambdaFunctionScheduled   First       3
        # LambdaFunctionStarted     First       4
        # LambdaFunctionSucceeded   First       5
        # TaskStateExited           First       6
        # TaskStateEntered          Second      7
        # LambdaFunctionScheduled   Second      8
        # LambdaFunctionStarted     Second      9
        # LambdaFunctionSucceeded   Second      10
        # TaskStateExited           Second      11
        # 
        # We measure from
        #   LambdaFunctionSucceeded   First     5
        # to
        #   LambdaFunctionScheduled   Second    8
        #
        # And from
        #   LambdaFunctionSucceeded   First     5
        # to
        #   LambdaFunctionStarted   Second      9
        #
        # Which presumbly involves:
        #   1. First persists its output
        #   2. invoking Second
        #
        # This is possibly a underestimate of the true latency of persisting
        # the result of First and invoking Second. It's likely that somewhere
        # between
        #
        #   LambdaFunctionStarted     First
        #
        # and
        #
        #   LambdaFunctionSucceeded   First
        #
        # First's result is persisted.
        #
        # But the goal is to be generous when estimating Step Function's
        # performance


        ret = subprocess.run(["aws", "stepfunctions", "list-executions",
                              "--state-machine-arn", STEP_FUNCTIONS_ARN
                              ],
                              capture_output=True)
        if ret.returncode != 0:
            print(f'Step Functions list-executions failed: {ret.stderr.decode("utf-8")}')

        all_executions = json.loads(ret.stdout.decode("utf-8"))['executions']
        my_executions = [e for e in all_executions if datetime.fromisoformat(e['startDate']) > start_tsp ]
        # print(my_executions)

        # extract end-to-end latency from the execution history

        my_executions_arns = [e['executionArn'] for e in my_executions]

        result = {
            'success to scheduled':[],
            'success to start':[],
        }

        for a in my_executions_arns:

            ret = subprocess.run(["aws", "stepfunctions", "get-execution-history",
                                  "--execution-arn", a
                                  ],
                                  capture_output=True)
            if ret.returncode != 0:
                print(f'Step Functions get-execution-history failed: {ret.stderr.decode("utf-8")}')

            events = json.loads(ret.stdout.decode("utf-8"))['events']
            
            success_tsp = list(filter(lambda x: x['id']==5, events))[0]
            success_tsp = datetime.fromisoformat(success_tsp['timestamp'])

            scheduled_tsp = list(filter(lambda x: x['id']==8, events))[0]
            scheduled_tsp = datetime.fromisoformat(scheduled_tsp['timestamp'])

            diff = scheduled_tsp - success_tsp

            result['success to scheduled'].append(diff.seconds*1000 + diff.microseconds / 1000)

            start_tsp = list(filter(lambda x: x['id']==9, events))[0]
            start_tsp = datetime.fromisoformat(start_tsp['timestamp'])

            diff = start_tsp - success_tsp

            result['success to start'].append(diff.seconds*1000 + diff.microseconds / 1000)

        final_result[sz] = result
        print(final_result)
        with open('final_result.json', 'w') as f:
            f.write(json.dumps(final_result))

    


if __name__ == '__main__':
    main()