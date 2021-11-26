'''
Run the map workflow at different fan-out size: 2,4,8,16,32, 64, 128,256, 512

Each fan-out function (F1) only gets a single byte of input and F1 simply
return event.

Measure the end-to-end latency from UnumMap0's START to summary's END
'''

import time
import subprocess
import json

UNUM_MAP_0_NAME = "unum-map-micro-UnumMap0Function-oRZeO1vxZPeY"
SUMMARY_NAME = "unum-map-micro-SummaryFunction-vCRcPkfK6qZw"
NANO_TO_MILLI = 1000000
NUM_RUNS =20


def main():

    # delete the cloud watch log group before start
    ret = subprocess.run(["aws", "logs", "delete-log-group",
                          "--log-group-name", f'/aws/lambda/{UNUM_MAP_0_NAME}'],
                          capture_output=True)

    if ret.returncode != 0:
        print(f'Failed to get log streams for {UNUM_MAP_0_NAME}')
        print(f'{ret.stderr.decode("utf-8")}')

    ret = subprocess.run(["aws", "logs", "delete-log-group",
                          "--log-group-name", f'/aws/lambda/{SUMMARY_NAME}'],
                          capture_output=True)

    if ret.returncode != 0:
        print(f'Failed to get log streams for {SUMMARY_NAME}')
        print(f'{ret.stderr.decode("utf-8")}')


    fan_out_sizes = [2**i for i in range(1, 10)]
    # fan_out_sizes = [2**i for i in range(1, 3)]
    final_result = {}

    for sz in fan_out_sizes:
        print(f'\n*************Fan-out Size: {sz}*************\n')

        # create payload
        input_payload = {
            "Data": {
                "Source": "http",
                "Value": ["b" for _ in range(sz)]
                }
        }

        with open('input-tmp.json', 'w') as f:
                f.write(json.dumps(input_payload))

        # invoke the entry function NUM_RUNS times
        for t in range(NUM_RUNS):
            time.sleep(1)

            ret = subprocess.run(["aws", "lambda", "invoke",
                                  "--function-name", UNUM_MAP_0_NAME,
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

        # wait for all cloudwatch logs to populate
        time.sleep(10)

        # get the cloud watch logs
        # download all streams of Cloudwatch logs for UNUM_MAP_0_NAME and SUMMARY_NAME

        # UNUM_MAP_0_NAME 
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

        # SUMMARY_NAME
        ret = subprocess.run(["aws", "logs", "describe-log-streams",
                              "--log-group-name", f'/aws/lambda/{SUMMARY_NAME}'],
                              capture_output=True)

        if ret.returncode != 0:
            print(f'Failed to get log streams for {SUMMARY_NAME}')
            print(f'{ret.stderr.decode("utf-8")}')
            return None

        streams = json.loads(ret.stdout.decode("utf-8"))
        streams = streams["logStreams"]
        print(f'Found {len(streams)} log streams for {SUMMARY_NAME}')

        summary_log_group_events = []

        for s in streams:
            ret = subprocess.run(["aws", "logs", "get-log-events",
                                  "--log-group-name", f'/aws/lambda/{SUMMARY_NAME}',
                                  "--log-stream-name", s["logStreamName"]],
                                  capture_output=True)
            
            if ret.returncode != 0:
                print(f'Failed to get events from log stream {s["logStreamName"]} for {SUMMARY_NAME}')
                summary_log_group_events.append({"error": ret.stderr.decode("utf-8")})
            else:
                events = json.loads(ret.stdout.decode("utf-8"))
                events = events["events"] # a list of dict
                summary_log_group_events = summary_log_group_events + events

        # extract useful data from raw logs
        #
        # We're only interested in the START timestamp of UnumMap0 and END
        # timestamp of Summary. Extract both and order them in ascending order
        # to match.
        # print(unum_map_log_group_events)
        # print(summary_log_group_events)
        result = {
            "UnumMap0 START tsp": [],
            "Summary END tsp":[],
            "e2e latency":[]
        }

        for e in unum_map_log_group_events:
            if e['message'].startswith("START"):
                result['UnumMap0 START tsp'].append(e['timestamp'])

        for e in summary_log_group_events:
            if e['message'].startswith("END"):
                result['Summary END tsp'].append(e['timestamp'])

        result['UnumMap0 START tsp'].sort()
        result['Summary END tsp'].sort()

        result['e2e latency'] = [result['Summary END tsp'][i] - result['UnumMap0 START tsp'][i] for i in range(len(result['Summary END tsp']))]

        final_result[sz] = result
        print(result)

        # delete the cloud watch log group before starting the next experiment
        ret = subprocess.run(["aws", "logs", "delete-log-group",
                              "--log-group-name", f'/aws/lambda/{UNUM_MAP_0_NAME}'],
                              capture_output=True)

        if ret.returncode != 0:
            print(f'Failed to get log streams for {UNUM_MAP_0_NAME}')
            print(f'{ret.stderr.decode("utf-8")}')

        ret = subprocess.run(["aws", "logs", "delete-log-group",
                              "--log-group-name", f'/aws/lambda/{SUMMARY_NAME}'],
                              capture_output=True)

        if ret.returncode != 0:
            print(f'Failed to get log streams for {SUMMARY_NAME}')
            print(f'{ret.stderr.decode("utf-8")}')

        time.sleep(5)

    print(final_result)
    with open('final_result.json', 'w') as f:
        f.write(json.dumps(final_result))

    


if __name__ == '__main__':
    main()