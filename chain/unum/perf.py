import time
import subprocess
import json
import numpy as np

CHAIN_PASS_FUNCTION_ARN = "unum-chain-micro-ChainPassFunction-x2KPIQMqdYFD"
NANO_TO_MILLI = 1000000
NUM_RUNS =20


def main():

    # delete the cloud watch log group before start
    ret = subprocess.run(["aws", "logs", "delete-log-group",
                          "--log-group-name", f'/aws/lambda/{CHAIN_PASS_FUNCTION_ARN}'],
                          capture_output=True)

    if ret.returncode != 0:
        print(f'Failed to get log streams for {CHAIN_PASS_FUNCTION_ARN}')
        print(f'{ret.stderr.decode("utf-8")}')
    else:
        print(f'log group /aws/lambda/{CHAIN_PASS_FUNCTION_ARN} deleted')


    # Lambda's input payload size limit: 256 KB for async invocations
    sizes = [1,5,50]

    final_result = {
        "chain2":{},
        "chain3":{},
        "chain4":{},
        "chain5":{},
        "chain6":{},
        "chain7":{},
        "chain8":{},
        "chain9":{},
        "chain10":{},
    }

    for d in range(2,11):

        print(f'\n**********Chain Depth: {d}**********\n')

        for i in sizes:

            # create payload
            input_payload = {
                        "Data": {
                            "Source": "http",
                            "Value": "b"*i*1024
                        },
                        "Fan-out": {
                            "Type":"Map",
                            "Index":0,
                            "Size": d
                        }
                    }
                

            # invoke the entry function 10 times
            print(f'\n**********Invoking with payload size {i}KB**********\n')

            for t in range(NUM_RUNS):
                time.sleep(1)

                with open('input-tmp.json', 'w') as f:
                    f.write(json.dumps(input_payload))

                ret = subprocess.run(["aws", "lambda", "invoke",
                                      "--function-name", CHAIN_PASS_FUNCTION_ARN,
                                      "--cli-binary-format", "raw-in-base64-out",
                                      "--payload", 'file://input-tmp.json', 'tmp'
                                      ],
                                      capture_output=True)

                if ret.returncode != 0:
                    print(f'Invocation failed: {ret.stderr.decode("utf-8")}')
                else:
                    # invocation succeeds
                    # record the executionArn
                    lambda_ret = json.loads(ret.stdout.decode("utf-8"))
                    print(f'Iteration {t}: \n\t{lambda_ret}')



            # get the cloud watch logs
            # download all streams of Cloudwatch logs for First. 

            time.sleep(10)

            ret = subprocess.run(["aws", "logs", "describe-log-streams",
                                  "--log-group-name", f'/aws/lambda/{CHAIN_PASS_FUNCTION_ARN}'],
                                  capture_output=True)

            if ret.returncode != 0:
                print(f'Failed to get log streams for {CHAIN_PASS_FUNCTION_ARN}')
                print(f'{ret.stderr.decode("utf-8")}')
                return None

            streams = json.loads(ret.stdout.decode("utf-8"))
            streams = streams["logStreams"]
            print(f'Found {len(streams)} log streams for {CHAIN_PASS_FUNCTION_ARN}')

            log_group_events = []

            for s in streams:
                ret = subprocess.run(["aws", "logs", "get-log-events",
                                      "--log-group-name", f'/aws/lambda/{CHAIN_PASS_FUNCTION_ARN}',
                                      "--log-stream-name", s["logStreamName"]],
                                      capture_output=True)
                
                if ret.returncode != 0:
                    print(f'Failed to get events from log stream {s["logStreamName"]} for {CHAIN_PASS_FUNCTION_ARN}')
                    log_group_events.append({"error": ret.stderr.decode("utf-8")})
                else:
                    events = json.loads(ret.stdout.decode("utf-8"))
                    events = events["events"] # a list of dict
                    log_group_events = log_group_events + events
        
            # get the latencies

            payload_size_start_tsp=[]
            payload_size_end_tsp=[]
            payload_size_result = []

            for idx, e in enumerate(log_group_events):
                if e['message'].startswith("[TEST]Start"):
                    payload_size_start_tsp.append(log_group_events[idx-1]['timestamp'])
                    print(log_group_events[idx-1]['message'])
                if e['message'].startswith("[TEST]End"):
                    payload_size_end_tsp.append(log_group_events[idx+1]['timestamp'])
                    print(log_group_events[idx+1]['message'])

            payload_size_start_tsp = np.array(sorted(payload_size_start_tsp))
            payload_size_end_tsp = np.array(sorted(payload_size_end_tsp))

            payload_size_result = [int(payload_size_end_tsp[idx] - payload_size_start_tsp[idx]) for idx in range(len(payload_size_start_tsp))]
            # print(payload_size_start_tsp)
            # print(payload_size_end_tsp)
            # print(payload_size_result)

            final_result[f"chain{d}"][i]=payload_size_result
       
            print(final_result)
            with open('final_result.json', 'w') as f:
                f.write(json.dumps(final_result))

            # delete the cloud watch log group before start
            ret = subprocess.run(["aws", "logs", "delete-log-group",
                                  "--log-group-name", f'/aws/lambda/{CHAIN_PASS_FUNCTION_ARN}'],
                                  capture_output=True)

            if ret.returncode != 0:
                print(f'Failed to get log streams for {CHAIN_PASS_FUNCTION_ARN}')
                print(f'{ret.stderr.decode("utf-8")}')
            else:
                print(f'log group /aws/lambda/{CHAIN_PASS_FUNCTION_ARN} deleted')




if __name__ == '__main__':
    main()