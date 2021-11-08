#!/usr/bin/env python
import argparse
import subprocess
import json
from datetime import datetime
import numpy as np
import time

EXCAMERA_S3 = "excamera-input-6frames-16chunks"
SINTEL_4K_RAW_S3 = "sintel-4k-y4m-6frames-880"
EXCAMERA_SP_ARN = "arn:aws:states:us-west-1:746167823857:stateMachine:ExCameraSF-rjidtO8s4jmA"
NUM_CHUNKS = 16
NUM_BATCHES = 55 # 1 batch = 16 chunks



def clear_excamera_s3():
    # delete all files in the excamera s3 bucket
    print(f'Delete all files from the {EXCAMERA_S3} bucket')
    ret = subprocess.run(["aws", "s3",
        "rm",
        f"s3://{EXCAMERA_S3}",
        "--recursive"],
        capture_output=True)



def clean_excamera_s3():
    # delete *.state files and *.ivf files from the excamera s3 bucket
    print(f'Clean the {EXCAMERA_S3} bucket of .state and .ivf files')
    ret = subprocess.run(["aws", "s3",
        "rm",
        f"s3://{EXCAMERA_S3}/",
        "--exclude",
        "*",
        "--include",
        "*.ivf",
        "--recursive"],
        capture_output=True)
    ret = subprocess.run(["aws", "s3",
        "rm",
        f"s3://{EXCAMERA_S3}/",
        "--exclude",
        "*",
        "--include",
        "*.state",
        "--recursive"],
        capture_output=True)



def reload_excamera_s3():
    # reload the s3 bucket
    print(f'Reloading the {EXCAMERA_S3} bucket from {SINTEL_4K_RAW_S3}')
    print(f'Copying from {0:08d}.y4m to {NUM_CHUNKS*NUM_BATCHES-1:08d}.y4m')
    for i in range(NUM_CHUNKS*NUM_BATCHES):
        print(f'aws s3 cp s3://{SINTEL_4K_RAW_S3}/{i:08d}.y4m s3://{EXCAMERA_S3}')
        ret = subprocess.run(["aws", "s3",
            "cp",
            f"s3://{SINTEL_4K_RAW_S3}/{i:08d}.y4m",
            f"s3://{EXCAMERA_S3}"],
            capture_output=True)


def run():
    # {NUM_BATCHES} iterations of 16 chunks each, e.g.,
    # 00000000.y4m-00000015.y4m
    # 00000016.y4m-00000031.y4m
    # no wait between invocations.
    # record the execution name for getting the e2e runtime later
    # for b in range(NUM_BATCHES):

    execution_arns = []

    # for b in range(1):
    for b in range(NUM_BATCHES):
        # create input payload
        input_payload = {"chunks":[{"bucket":EXCAMERA_S3,"file":f'{b*NUM_CHUNKS+i:08d}.y4m'} for i in range(NUM_CHUNKS)]}

        # invoke the Step Function
        print(f'aws stepfunctions start-execution --state-machine-arn {EXCAMERA_SP_ARN} --input {json.dumps(input_payload)}')

        # with open('payload_tmp.json', 'w') as f:
        #     f.write(json.dumps(input_payload))

        # ret = subprocess.run(["aws", "stepfunctions", "start-execution",
        #                       "--state-machine-arn", EXCAMERA_SP_ARN,
        #                       "--input", f'file://payload_tmp.json'
        #                       ],
        #                       capture_output=True)

        ret = subprocess.run(["aws", "stepfunctions", "start-execution",
                              "--state-machine-arn", EXCAMERA_SP_ARN,
                              "--input", json.dumps(input_payload)
                              ],
                              capture_output=True)

        if ret.returncode != 0:
            print(ret.stderr.decode("utf-8"))
        else:
            # invocation succeeds
            # record the executionArn
            sf_ret = json.loads(ret.stdout.decode("utf-8"))
            execution_arns.append(sf_ret["executionArn"])

    # return the execution name of all Step Function invocations
    return execution_arns

def main():
    clean_excamera_s3()
    # reload_excamera_s3()

    execution_arns = run()
    print(execution_arns)

    time.sleep(300)

    # get the e2e runtime
    e2e_latency = []
    for arn in execution_arns:
        ret = subprocess.run(["aws", "stepfunctions", "describe-execution",
                              "--execution-arn", arn],
                              capture_output=True)

        if ret.returncode != 0:
            print(ret.stderr.decode("utf-8"))
        else:
            execution_desc = json.loads(ret.stdout.decode("utf-8"))
            start_tsp = datetime.fromisoformat(execution_desc['startDate'])

            # if an execution hasn't finished, wait for another 60 seconds
            try:
                end_tsp = datetime.fromisoformat(execution_desc['stopDate'])
            except KeyError as e:
                time.sleep(60)
                ret = subprocess.run(["aws", "stepfunctions", "describe-execution",
                              "--execution-arn", arn],
                              capture_output=True)
                execution_desc = json.loads(ret.stdout.decode("utf-8"))
                try:
                    end_tsp = datetime.fromisoformat(execution_desc['stopDate'])
                except KeyError as e:
                    e2e_latency.append(-1)
                    continue 

            diff = end_tsp - start_tsp
            e2e_latency.append(diff.seconds*1000 + diff.microseconds / 1000)

    # compute the average and std of e2e runtime
    e2e_latency_np = np.array(e2e_latency)
    avg = np.mean(e2e_latency_np)
    std = np.std(e2e_latency_np)
    print(e2e_latency)
    print(f'average: {avg}, std: {std}')

    # record raw data, the average and std of e2e runtime in excel



if __name__ == '__main__':
    main()