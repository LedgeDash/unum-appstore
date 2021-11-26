import time
import subprocess
import json

FRIST_FUNCTION_ARN = "unum-pass-micro-FirstFunction-LtxIB55cUMXx"
NANO_TO_MILLI = 1000000
NUM_RUNS =20


def main():

    # delete the cloud watch log group before start
    ret = subprocess.run(["aws", "logs", "delete-log-group",
                          "--log-group-name", f'/aws/lambda/{FRIST_FUNCTION_ARN}'],
                          capture_output=True)

    if ret.returncode != 0:
        print(f'Failed to get log streams for {FRIST_FUNCTION_ARN}')
        print(f'{ret.stderr.decode("utf-8")}')


    # Lambda's input payload size limit: 256 KB for async invocations
    sizes = [5*i for i in range(0,52)]
    # sizes = [5*i for i in range(0,2)]

    final_result = {}

    for i in sizes:

        # create payload
        input_payload = {
                    "Data": {
                        "Source": "http",
                        "Value": "b"*i*1024
                        }
                    }
            

        # invoke the entry function 10 times
        # print(f'aws lambda invoke --function-name {FRIST_FUNCTION_ARN} --cli-binary-format raw-in-base64-out --payload {json.dumps(input_payload)} tmp')

        print(f'\n**********Invoking with payload size {i}KB**********\n')

        for t in range(NUM_RUNS):
            time.sleep(1)

            with open('input-tmp.json', 'w') as f:
                f.write(json.dumps(input_payload))

            ret = subprocess.run(["aws", "lambda", "invoke",
                                  "--function-name", FRIST_FUNCTION_ARN,
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
                              "--log-group-name", f'/aws/lambda/{FRIST_FUNCTION_ARN}'],
                              capture_output=True)

        if ret.returncode != 0:
            print(f'Failed to get log streams for {FRIST_FUNCTION_ARN}')
            print(f'{ret.stderr.decode("utf-8")}')
            return None

        streams = json.loads(ret.stdout.decode("utf-8"))
        streams = streams["logStreams"]
        print(f'Found {len(streams)} log streams for {FRIST_FUNCTION_ARN}')

        log_group_events = []

        for s in streams:
            ret = subprocess.run(["aws", "logs", "get-log-events",
                                  "--log-group-name", f'/aws/lambda/{FRIST_FUNCTION_ARN}',
                                  "--log-stream-name", s["logStreamName"]],
                                  capture_output=True)
            
            if ret.returncode != 0:
                print(f'Failed to get events from log stream {s["logStreamName"]} for {FRIST_FUNCTION_ARN}')
                log_group_events.append({"error": ret.stderr.decode("utf-8")})
            else:
                events = json.loads(ret.stdout.decode("utf-8"))
                events = events["events"] # a list of dict
                log_group_events = log_group_events + events
        
        # get the latencies

        '''
        the unum runtime is dotted with tracing that measures the latency for
        individual component operations:

        Latency:

            [Unum Wrapper] get_checkpoint:137293187; user_lambda: 1262; egress: 57767316

                get_checkpoint(), run all the time, before the user function.

                user_lambda, run only when get_checkpoint() return None

                egress(), the entire egress() function in the wrapper, run all the time

            [Unum Wrapper.egress]run_checkpoint: 22795350; run_continuation: 34930183

                run_checkpoint(), inside egress(). do an actual checkpoint (i.e.,
                PUTITEM) when get_checkpoint() returns None; otherwise just return

                run_continuation(), inside egress(). 



        DynamoDB consumed capacity:

            checkpoint() in the ds.py for put_item

                [ds.dynamodb.checkpoint] put_item consumed capacity: 1.0


        Note:

            1. total additional latency is get_checkpoint() + egress total

            2. total checkpoint related latency: get_checkpoint() + run_checkpoint()

            3. total continuation latency: run_continuation()

        '''
        result = {
            "get_checkpoint": [],
            "egress total": [],
            "run_checkpoint": [],
            "run_continuation":[],
            "user function":[],
            'invoke':[],
            'checkpoint read':[],
            'checkpoint write':[]
        }

        for e in log_group_events:
            if e['message'].startswith("[Unum Wrapper.egress]"):
                egress_parts = e['message'].split(';')

                #run_checkpoint

                result['run_checkpoint'].append(int(egress_parts[0].split(':')[1])/NANO_TO_MILLI)
                result['run_continuation'].append(int(egress_parts[1].split(':')[1])/NANO_TO_MILLI)

            if e['message'].startswith("[Unum Wrapper]"):
                wrapper_parts = e['message'].split(';')
                # [Unum Wrapper] get_checkpoint:137293187; user_lambda: 1262; egress: 57767316

                result['get_checkpoint'].append(int(wrapper_parts[0].split(':')[1])/NANO_TO_MILLI)
                result['user function'].append(int(wrapper_parts[1].split(':')[1])/NANO_TO_MILLI)
                result['egress total'].append(int(wrapper_parts[2].split(':')[1])/NANO_TO_MILLI)
            if e['message'].startswith('[INVOKER invoke()]'):
                result['invoke'].append(int(e['message'].split(']')[1])/NANO_TO_MILLI)
            if e['message'].startswith('[DS checkpoint()]'):
                result['checkpoint write'].append(int(e['message'].split(']')[1])/NANO_TO_MILLI)
            if e['message'].startswith('[DS get_checkpoint]'):
                result['checkpoint read'].append(int(e['message'].split(']')[1])/NANO_TO_MILLI)



        # Clean data:
        # remove the top 2 and bottom 2 of each

        def remove_top_bottom_two(l):
            l.remove(max(l))
            l.remove(max(l))
            l.remove(min(l))
            l.remove(min(l))

            return l

        result['get_checkpoint'] = remove_top_bottom_two(result['get_checkpoint'])
        result['egress total'] = remove_top_bottom_two(result['egress total'])
        result['run_checkpoint'] = remove_top_bottom_two(result['run_checkpoint'])
        result['run_continuation'] = remove_top_bottom_two(result['run_continuation'])
        result['invoke'] = remove_top_bottom_two(result['invoke'])
        result['checkpoint read'] = remove_top_bottom_two(result['checkpoint read'])
        result['checkpoint write'] = remove_top_bottom_two(result['checkpoint write'])


        # save results

        final_result[i] = result


        # delete the cloud watch log group
        ret = subprocess.run(["aws", "logs", "delete-log-group",
                              "--log-group-name", f'/aws/lambda/{FRIST_FUNCTION_ARN}'],
                              capture_output=True)

        if ret.returncode != 0:
            print(f'Failed to get log streams for {FRIST_FUNCTION_ARN}')
            print(f'{ret.stderr.decode("utf-8")}')
            return None

        time.sleep(5)

        print(final_result)

        with open('final_result.json', 'w') as f:
            f.write(json.dumps(final_result))

    print(final_result)

    with open('final_result.json', 'w') as f:
        f.write(json.dumps(final_result))




if __name__ == '__main__':
    main()