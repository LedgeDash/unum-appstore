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

STEP_FUNCTIONS_ARNS = [
    "arn:aws:states:us-west-1:746167823857:stateMachine:Chain2-KefH4Vp4NP6y",
    "arn:aws:states:us-west-1:746167823857:stateMachine:Chain3-HHuWSCyyqK1f",
    "arn:aws:states:us-west-1:746167823857:stateMachine:Chain4-XCCadIrEkhSh",
    "arn:aws:states:us-west-1:746167823857:stateMachine:Chain5-0JjIzbugIFwW",
    "arn:aws:states:us-west-1:746167823857:stateMachine:Chain6-KOcNw5JjfBxv",
    "arn:aws:states:us-west-1:746167823857:stateMachine:Chain7-Ds7u0MJViL69",
    "arn:aws:states:us-west-1:746167823857:stateMachine:Chain8-mBpUef2iBDPk",
    "arn:aws:states:us-west-1:746167823857:stateMachine:Chain9-GfiNzCaRLvI0",
    "arn:aws:states:us-west-1:746167823857:stateMachine:Chain10-4Labc6aiYX13"
]

NANO_TO_MILLI = 1000000
NUM_RUNS =20


def main():
    # Lambda's input payload size limit: 256 KB for async invocations
    sizes = [1, 5, 50]

    final_result = {
        "chain2": {},
        "chain3": {},
        "chain4": {},
        "chain5": {},
        "chain6": {},
        "chain7": {},
        "chain8": {},
        "chain9": {},
        "chain10": {}
    }

    for chain_depth,sf_arn in enumerate(STEP_FUNCTIONS_ARNS):
        print(f'\n*************Chain Depth: {chain_depth+2}*************\n')



        for sz in sizes:
            print(f'\n*************Payload Size: {sz}KB*************\n')

            # create payload
            input_payload = "b"*sz*1024
            with open('input-tmp.json', 'w') as f:
                    f.write(json.dumps(input_payload))

            # invoke the step functions NUM_RUNS times
            start_tsp = datetime.now(LOCAL_TZ) # will only consider executions that happen after this timestamp

            # repeat the experiment NUM_RUNS times
            for i in range(NUM_RUNS):
                time.sleep(1)

                ret = subprocess.run(["aws", "stepfunctions", "start-execution",
                                          "--state-machine-arn", sf_arn,
                                          "--input", f'file://input-tmp.json'
                                          ],
                                          capture_output=True)
                if ret.returncode != 0:
                    print(f'Step Functions invocation failed: {ret.stderr.decode("utf-8")}')
                else:
                    print(f'Iteration {i}: \n\t{json.loads(ret.stdout)}')

            # Get the execution history
            time.sleep(10)

            ret = subprocess.run(["aws", "stepfunctions", "list-executions",
                                  "--state-machine-arn", sf_arn
                                  ],
                                  capture_output=True)
            if ret.returncode != 0:
                print(f'Step Functions list-executions failed: {ret.stderr.decode("utf-8")}')

            all_executions = json.loads(ret.stdout.decode("utf-8"))['executions']
            my_executions = [e for e in all_executions if datetime.fromisoformat(e['startDate']) > start_tsp ]
           
            # extract end-to-end latency from the execution history
            # result for this payload size
            payload_size_result = []

            for ex in my_executions:
                if ex['status'] == "SUCCEEDED":
                    start_tsp = datetime.fromisoformat(ex['startDate'])
                    end_tsp = datetime.fromisoformat(ex['stopDate'])
                    diff = end_tsp -start_tsp
                    e2e_latency = diff.seconds*1000 + diff.microseconds / 1000 # convert to milliseconds

                    payload_size_result.append(e2e_latency)

            final_result[f'chain{chain_depth+2}'][sz] = payload_size_result


            print(final_result)
            with open('final_result.json', 'w') as f:
                f.write(json.dumps(final_result))

    


if __name__ == '__main__':
    main()