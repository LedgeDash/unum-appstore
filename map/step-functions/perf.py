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

STEP_FUNCTIONS_ARN = "arn:aws:states:us-west-1:746167823857:stateMachine:MapNoWaitSF-6MtNkoXCguVS"

NANO_TO_MILLI = 1000000
NUM_RUNS =20


def main():
    fan_out_sizes = [2**i for i in range(7, 10)]

    final_result = {}

    for sz in fan_out_sizes:
        print(f'\n*************Fan-out Size: {sz}*************\n')

        # create payload
        input_payload = ["b" for _ in range(sz)]

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

        if sz == 2**7:
            time.sleep(20)
        elif sz ==2**8:
            time.sleep(40)
        elif sz ==2**9:
            time.sleep(80)
        else:
            time.sleep(10)

        # Get the execution history
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

        result = {
            "start tsp": [],
            "end tsp": [],
            "e2e latency":[]
        }

        for ex in my_executions:
            if ex['status'] == "SUCCEEDED":
                start_tsp = datetime.fromisoformat(ex['startDate'])
                end_tsp = datetime.fromisoformat(ex['stopDate'])
                diff = end_tsp -start_tsp
                e2e_latency = diff.seconds*1000 + diff.microseconds / 1000 # convert to milliseconds

                result['start tsp'].append(ex['startDate'])
                result['end tsp'].append(ex['stopDate'])
                result['e2e latency'].append(e2e_latency)

        print(result)
        final_result[sz] = result

    print(final_result)
    with open('final_result-add.json', 'w') as f:
        f.write(json.dumps(final_result))


if __name__ == '__main__':
    main()