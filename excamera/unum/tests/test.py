#!/usr/bin/env python
import argparse
import subprocess
import json
from datetime import datetime
import numpy as np
import time

EXCAMERA_S3 = "excamera-input-6frames-16chunks"
SINTEL_4K_RAW_S3 = "sintel-4k-y4m-6frames-880"
UNUM_MAP_0_NAME = "unum-excamera-dynamodb-UnumMap0Function-GuvVGT56dpRV"
REBASE_NAME = "unum-excamera-dynamodb-rebaseFunction-Of71i3oykEzK"
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


    # Save the UnumMap0 function's invocation ID, the last chunk of that batch
    # and the local (local to the client) start time
    execution_arns = []

    for b in range(NUM_BATCHES):
        # create input payload
        input_payload = {
            "Data": {
                "Source": "http",
                "Value": {
                    "chunks":[{"bucket":EXCAMERA_S3,"file":f'{b*NUM_CHUNKS+i:08d}.y4m'} for i in range(NUM_CHUNKS)]
                }
            }
        }

        # invoke the Step Function
        print(f'aws lambda invoke --function-name {UNUM_MAP_0_NAME} --cli-binary-format raw-in-base64-out --payload {json.dumps(input_payload)} tmp')

        ret = subprocess.run(["aws", "lambda", "invoke",
                              "--function-name", UNUM_MAP_0_NAME,
                              "--cli-binary-format", "raw-in-base64-out",
                              "--payload", json.dumps(input_payload), 'tmp'
                              ],
                              capture_output=True)

        if ret.returncode != 0:
            print(f'Invocation failed: {ret.stderr.decode("utf-8")}')
        else:
            # invocation succeeds
            # record the executionArn
            lambda_ret = json.loads(ret.stdout.decode("utf-8"))
            print(f'{lambda_ret}')

    # return the execution name of all Step Function invocations
    return execution_arns

def check_excamera_complete():
    ret = subprocess.run(["aws", "s3api", "list-objects",
                              "--bucket", EXCAMERA_S3
                              ],
                              capture_output=True)

    if ret.returncode != 0:
        print(f'aws s3api list-objects failed: {ret.stderr.decode("utf-8")}')
    else:
        # invocation succeeds
        s3_ret = json.loads(ret.stdout.decode("utf-8"))
        # print(f'{s3_ret["NextMarker"]}')
        all_files = [e['Key'] for e in s3_ret['Contents']]

        for i in range(NUM_CHUNKS * NUM_BATCHES):
            if i % 16 ==0:
                target_file = f'{i:08d}-0.ivf'
            else:
                target_file = f'{i:08d}.ivf'

            if target_file not in all_files:
                print(f'{target_file} not found')
                return False
    return True

def main():
    # clean_excamera_s3()
    # reload_excamera_s3()

    # run()

    # time.sleep(300)

    if check_excamera_complete():
        print(f'excamera completed')
        # download all all streams of Cloudwatch logs for UnumMap0 and Rebase. 

        # UnumMap0
        ret = subprocess.run(["aws", "logs", "describe-log-streams",
                              "--log-group-name", f'/aws/lambda/{UNUM_MAP_0_NAME}'],
                              capture_output=True)

        if ret.returncode != 0:
            print(f'Failed to get log streams for {UNUM_MAP_0_NAME}')
            print(f'{ret.stderr.decode("utf-8")}')
            return None

        streams = json.loads(ret.stdout.decode("utf-8"))
        streams = streams["logStreams"]
        print(f'Found {len(streams)} log streams for {UNUM_MAP_0_NAME}')

        unum_map_log_group_events = []

        for s in streams:
            ret = subprocess.run(["aws", "logs", "get-log-events",
                                  "--log-group-name", f'/aws/lambda/{UNUM_MAP_0_NAME}',
                                  "--log-stream-name", s["logStreamName"]],
                                  capture_output=True)
            
            if ret.returncode != 0:
                print(f'Failed to get events from log stream {s["logStreamName"]} for {UNUM_MAP_0_NAME}')
                unum_map_log_group_events.append({"error": ret.stderr.decode("utf-8")})
            else:
                events = json.loads(ret.stdout.decode("utf-8"))
                events = events["events"] # a list of dict
                unum_map_log_group_events = unum_map_log_group_events + events

        # Rebase
        ret = subprocess.run(["aws", "logs", "describe-log-streams",
                              "--log-group-name", f'/aws/lambda/{REBASE_NAME}'],
                              capture_output=True)

        if ret.returncode != 0:
            print(f'Failed to get log streams for {REBASE_NAME}')
            print(f'{ret.stderr.decode("utf-8")}')
            return None

        streams = json.loads(ret.stdout.decode("utf-8"))
        streams = streams["logStreams"]
        print(f'Found {len(streams)} log streams for {REBASE_NAME}')

        rebase_log_group_events = []

        for s in streams:
            ret = subprocess.run(["aws", "logs", "get-log-events",
                                  "--log-group-name", f'/aws/lambda/{REBASE_NAME}',
                                  "--log-stream-name", s["logStreamName"]],
                                  capture_output=True)
            
            if ret.returncode != 0:
                print(f'Failed to get events from log stream {s["logStreamName"]} for {REBASE_NAME}')
                rebase_log_group_events.append({"error": ret.stderr.decode("utf-8")})
            else:
                events = json.loads(ret.stdout.decode("utf-8"))
                events = events["events"] # a list of dict
                rebase_log_group_events = rebase_log_group_events + events # a list of list of dict.

        # get the START tsp of UnumMap0

        start_tsp = []

        for e in unum_map_log_group_events:
            if e['message'].startswith("START"):
                start_tsp.append(e['timestamp'])
        print(start_tsp)

        # get '[Unum] Rebase of chunk 00000815 completed' event

        end_tsp = []

        for e in rebase_log_group_events:
            if e['message'].startswith("[Unum] Rebase"):
                chunk_num = e['message'].split(' ')[4]
                end_tsp.append({'chunk': int(chunk_num), 'timestamp': e['timestamp']})

        end_tsp = sorted(end_tsp, key=lambda d: d['chunk']) 
        print(end_tsp)

        # compute the difference to get e2e latency
        if len(start_tsp) != len(end_tsp):
            print('len(start_tsp) != len(end_tsp')

        e2e_latency = [end_tsp[i]['timestamp'] - start_tsp[i] for i in range(len(start_tsp))] # in milliseconds

        # compute mean and std
        e2e_latency_np = np.array(e2e_latency)
        avg = np.mean(e2e_latency_np)
        std = np.std(e2e_latency_np)

        print(e2e_latency)
        print(f'average: {avg}, std: {std}')

    else:
        print(f'excamera still not done...')

    # record raw data, the average and std of e2e runtime in excel



if __name__ == '__main__':
    main()