#!/usr/bin/env python
from cfn_tools import load_yaml, dump_yaml
import json, os, sys, subprocess, time
import argparse
from datetime import datetime

import xlsxwriter
import pickle

''' Simple correctness test client

'''
def restore(args):
    ''' delete the following files and resources:
    1. .aws-sam/ (unum-cli build)
    2. unum runtime files (i.e., unum.py, ds.py) in each function directory (unum-cli build)
    3. unum_config.json in each function directory (frontend compiler)
    4. template.yaml (unum-cli build -g or unum-cli template)
    5. frontend compiler generated lambda functions (frontend compiler)
    6. restore to original unum-template.yaml (frontend compiler)
    7. the AWS Cloudformation stack (unum-cli deploy)
    8. remove the functin-arn.yaml file (unun-cli deploy)
    '''
    # item 1, 2
    ret = subprocess.run(["unum-cli", "build", "-c"], capture_output=True)

    # item 4, 8
    ret = subprocess.run(["rm", "-f", "function-arn.yaml", "template.yaml"], capture_output=True)
    print(f'\033[33m Remove unum build artifacts\033[0m')

    # item 3,5,6
    if args.skip_frontend == False:
        ret = subprocess.run(["sf", "-c"], capture_output=True)
        print(f'\033[33m Remove frontend compiler artifacts\033[0m')

    # item 7
    # check if the stack is deployed
    with open('unum-template.yaml') as f:
        unum_template = load_yaml(f.read())
        stack_name = unum_template['Globals']['ApplicationName']

    ret = subprocess.run(["aws", "cloudformation", "describe-stacks",
                      "--stack-name", stack_name],
                      capture_output=True)
    if ret.returncode == 0:
        # stack exists
        print(f'Stack exists on AWS. Deleting ......')
        ret = subprocess.run(["aws", "cloudformation", "delete-stack",
                              "--stack-name", stack_name],
                              capture_output=True)
        if ret.returncode != 0:
            print(f'\033[31mFailed to delete AWS stack {stack_name}\033[0m')
        else:
            print(f'AWS stack {stack_name} deletion initiated')
            while check_cloudformation_stack_exist(stack_name):
                time.sleep(5)
            print(f'\033[33m AWS stack {stack_name} deleted\033[0m\n')

    print(f'\033[32m unum Application Restored\033[0m\n')

def check_cloudformation_stack_exist(stack_name):
    ret = subprocess.run(["aws", "cloudformation", "describe-stacks",
                              "--stack-name", stack_name],
                              capture_output=True)

    if ret.returncode != 0:
        return False
    else:
        return True



def wait_workflow_log(timeout, function_arn_mapping):
    ''' Given a function to arn mapping, wait for all Lambdas in the workflow
    to populate Cloudwatch logs

    @param timeout int seconds
    '''
    elapsed_time = 0
    GAP = 10
    while check_workflow_log_exist(function_arn_mapping) == False:
        print(f'Waiting for logs to populate ......')
        time.sleep(GAP) # it takes time for cloudwatch logs to be populated
        elapsed_time = elapsed_time + GAP
        if elapsed_time >= timeout:
            return False
    return True


def check_workflow_execution_success(workflow_logs):
    ''' Given a workflow's Cloudwatch logs (returned by
    get_workflow_execution_log()), check if the execution was successful

    Requries the log group for each function to only have streams that are
    associated with this particular workflow invocation.

    See the check_lambda_log_success() for details on what checks are performs
    '''

    for f in workflow_logs:
        suc, diag = check_lambda_log_success(workflow_logs[f])
        if suc == False:

            print(f'\033[31m[*] Function {f} has errors in its logs:\033[0m')
            print(f'\033[31m{diag}')
            print(f'Raw Logs:')
            print(f'{workflow_logs[f]}\033[0m')

            return False
        else:
            print(f'\033[32m[*] Function {f} has no errors in its logs\033[0m')

    return True



def check_lambda_log_success(log_events):
    ''' For a particular Lambda, given the streams of log events returned by
    get_lambda_log (which in turn is using aws logs get-log-events on all
    streams in the log group for a Lambda), return whether there are errors.

    @param log_events list of dict, each dict is a JSON object of an event
    Lambda events typically have the following structure:
        "timestamp": int
        "message": str
        "ingestionTime": int

    "message" usually starts with one of the following:
        "START"
        "END"
        "REPORT"
        "[ERROR]"
    '''
    for stream in log_events:
        if isinstance(stream, dict):
            # failed to get the stream's event
            return False, stream
        elif isinstance(stream, list):
            for e in stream:
                if e["message"].startswith('[ERROR]') or e["message"].startswith('[Error]'):
                    return False, e["message"]
        else:
            print(f'Unknown stream result: {stream}')

    return True, None



def get_workflow_execution_log(function_arn_mapping):
    ''' Given a workflows function to arn mapping, get the logs for all of the
    functions in the workflow
    '''
    ret = {}
    for f in function_arn_mapping:
        function_arn = function_arn_mapping[f]
        function_name = function_arn.split(':')[-1]
        log_events = get_lambda_log(function_name) # a list of lists of dicts. each element list corresponds to a stream

        if log_events == None:
            print(f'function {f} ({function_name}) failed to get Cloudwatch logs')
            ret[f] = {"error": "no logs"}
            continue

        if isinstance(log_events, list):
            # succeeded getting log streams
            ret[f] = log_events
        else:
            print(f'get_lambda_log() returned non-list results')
            raise

    return ret



def get_lambda_log(function_name):
    ''' Given a Lambda arn, get its logs.

    This functions returns each stream of log events in its own list.

    @return

        If the Lambda doesn't have a Cloudwatch log group, return None

        If aws logs fails to get the list of log streams for the Lambda's
        Cloudwatch log group, return None

        For each stream, if aws logs fails to get the events, append a dict
        with the key "error" to the final output; if aws logs succeeds, return
        a list of dicts.

        Once all streams are done, return a list of dict and lists, with each
        element corresponds to a stream.
    '''

    log_group_name = f'/aws/lambda/{function_name}'

    if check_lambda_log_exist(function_name) == False:
        print(f'Log group {log_group_name} does NOT exist')
        return None

    ret = subprocess.run(["aws", "logs", "describe-log-streams",
                              "--log-group-name", log_group_name],
                              capture_output=True)

    if ret.returncode != 0:
        print(f'Failed to get log streams for {function_name}')
        print(f'{ret.stderr.decode("utf-8")}')
        return None

    streams = json.loads(ret.stdout.decode("utf-8"))
    streams = streams["logStreams"]
    print(f'Found {len(streams)} log streams for {function_name}')

    log_group_events = []

    for s in streams:
        ret = subprocess.run(["aws", "logs", "get-log-events",
                              "--log-group-name", log_group_name,
                              "--log-stream-name", s["logStreamName"]],
                              capture_output=True)
        
        if ret.returncode != 0:
            print(f'Failed to get events from log stream {s["logStreamName"]} for {function_name}')
            log_group_events.append({"error": ret.stderr.decode("utf-8")})
        else:
            events = json.loads(ret.stdout.decode("utf-8"))
            events = events["events"] # a list of dict
            log_group_events.append(events) # a list of list of dict.

    return log_group_events



def delete_lambda_log(function_name):
    ''' Delete the LOG GROUP of a Lambda function
    '''
    if check_lambda_log_exist(function_name):

        log_group_name = f'/aws/lambda/{function_name}'

        ret = subprocess.run(["aws", "logs", "delete-log-group",
                              "--log-group-name", log_group_name],
                              capture_output=True)

        if ret.returncode !=0:
            print(f'Failed to delete log group{log_group_name}:\n {ret.stderr.decode("utf-8")}')

def delete_workflow_log_streams(function_arn_mapping):
    ''' Delete the log streams for all functions in a workflow, keeping the
    log groups
    '''
    for f in function_arn_mapping:
        function_arn = function_arn_mapping[f]
        function_name = function_arn.split(':')[-1]

        if delete_lambda_log_streams(function_name) == False:
            print(f'Failed to delete log streams for function {function_name}')

    return



def delete_lambda_log_streams(function_name):
    ''' Delete all LOG STREAMS of a Lambda's Cloudwatch log group without deleting
    the log group
    '''
    success = True
    if check_lambda_log_exist(function_name):
        log_group_name = f'/aws/lambda/{function_name}'
        ret = subprocess.run(["aws", "logs", "describe-log-streams",
                              "--log-group-name", log_group_name],
                              capture_output=True)
        if ret.returncode != 0:
            print(f'Failed to get log streams for {function_name}')
            print(ret.stderr.decode("utf-8"))
            return False

        streams = json.loads(ret.stdout.decode("utf-8"))
        streams = streams["logStreams"]

        stream_names = [s["logStreamName"] for s in streams]

        for sn in stream_names:
            ret = subprocess.run(["aws", "logs", "delete-log-stream",
                              "--log-group-name", log_group_name,
                              "--log-stream-name", sn],
                              capture_output=True)

            if ret.returncode != 0:
                print(f'Failed to delete log stream {sn} for log group {log_group_name}')
                print(ret.stderr.decode("utf-8"))
                success = False

        return success

    else:
        return True


def check_workflow_log_exist(function_arn_mapping):
    ''' Given the function to arn mapping for a workflow, check if all
    functions have their Cloudwatch logs populated.
    '''
    for f in function_arn_mapping:

        function_arn = function_arn_mapping[f]
        function_name = function_arn.split(':')[-1]

        # print(f'Checking function {f} ({function_name})')

        if check_lambda_log_exist(function_name) == False:
            return False
    return True



def check_lambda_log_exist(function_name):
    ''' Given a Lambda's ARN, check if it has a Cloudwatch log group
    populated.
    '''
    log_group_name = f'/aws/lambda/{function_name}'

    # aws logs describe-log-streams return a JSON object with log streams when
    # the log group exists. Otherwise, it writes to stderr and returns a
    # non-zero exit code

    ret = subprocess.run(["aws", "logs", "describe-log-streams",
                              "--log-group-name", log_group_name],
                              capture_output=True)

    if ret.returncode == 0:
        return True
    else:
        # print(ret.stderr.decode("utf-8"))
        return False


def invoke_lambda(function_arn, payload_file):
    '''

    @return
    if execution succeeded, return True, "<ret>"
    if execution failed, return False, "<error>"
    '''
    ret = subprocess.run(["aws", "lambda", "invoke",
                              "--function-name", function_arn,
                              "--invocation-type", "RequestResponse",
                              "--payload", f'fileb://{payload_file}',
                              "tmp"],
                              capture_output=True)
    if ret.returncode == 0:
        stdout_msg = json.loads(ret.stdout.decode("utf-8"))
        if stdout_msg["StatusCode"] == 200:
            try:
                with open('tmp') as f:
                    return True, f.read()
            except Exception as e:
                return True, "No output"
        else:
            try:
                with open('tmp') as f:
                    return False, f.read()
            except Exception as e:
                return False, "No output"
    else:
        return False, ret.stderr.decode("utf-8")



def aws_correctness_test(args):
    # clean up
    restore(args)

    # compile from Step Functions
    if args.skip_frontend == False:
        print(f'\033[33mCompiling Step Function into unum workflow\033[0m\n')
        os.system("sf -pu -o trim")
        print(f'\n\033[32mCompiling Step Function into unum workflow Succeeded\033[0m\n')

    # create template.yaml and build
    os.system("unum-cli build -g")

    # deploy
    os.system("unum-cli deploy")

    
    with open('unum-template.yaml') as f:
        unum_template = load_yaml(f.read())

    with open('function-arn.yaml') as f:
        function_arn_mapping = load_yaml(f.read())

    print(f'Functions in this workflow:')
    print(f'{function_arn_mapping}')

    # Find the entry functions
    for f in unum_template["Functions"]:
        if "Start" in unum_template["Functions"][f]["Properties"] and unum_template["Functions"][f]["Properties"]["Start"]:
            entry_function = f

    # invoke the workflow by invoking the start function
    print(f'\n\033[33mInvoking the entry function\033[0m\n')
    print(f'Entry Function: {entry_function}, ARN: {function_arn_mapping[entry_function]}\n')

    if os.path.isfile(args.payload):
        suc, msg = invoke_lambda(function_arn_mapping[entry_function], args.payload)
        if suc == False:
            print(f'Workflow Invocation Failed: {msg}')
            return -1
    else:
        print(f'Cannot invoke lambda. Need events/event.json')
        return -2

    # Get the CloudWatch Logs for all functions in the workflow.

    # First make sure all Lambda's have their CloudWatch logs populated. This
    # could take a while, depending on how long the workflow is. Moreover, the
    # logs might not include all the events for a complete execution. There
    # could be a big time gap between the START event and the END event.
    # Therefore, we first wait for a period (the initial waiting period)
    # before checking the logs. Then we periodically check until all logs are
    # populated or a timeout happens which indicates that the workflow likely
    # broke somewhere.
    #
    # The initial waiting period is a cmdline option and allows the user to
    # customize based on their experienced guess on the workflow duration.

    # first wait for a period of time.
    print(f'\033[33m\nWaiting for workflow to complete before checking logs for execution correctness\033[0m\n')
    time.sleep(int(args.wait_limit))

    LOGCHECK_TIMEOUT = 20 #sec
    if wait_workflow_log(LOGCHECK_TIMEOUT, function_arn_mapping) == False:
        print(f'Not all Lambda log are present')
    
    print(f'\033[33m\nChecking Cloudwatch logs for all functions in the workflow\033[0m\n')

    logs = get_workflow_execution_log(function_arn_mapping)

    if check_workflow_execution_success(logs):
        print(f'\033[32m\nAll functions in the workflow succeeded\033[0m')
    else:
        print(f'\033[31m\nSome functions in the workflow failed. See trace for more details\033[0m')




def performance_test(args):
    # clean up
    restore(args)

    # compile from Step Functions
    if args.skip_frontend == False:
        print(f'\033[33mCompiling Step Function into unum workflow\033[0m\n')
        os.system("sf -pu -o trim")
        print(f'\n\033[32mCompiling Step Function into unum workflow Succeeded\033[0m\n')

    # create template.yaml and build
    os.system("unum-cli build -g")

    # deploy
    os.system("unum-cli deploy")

    with open('unum-template.yaml') as f:
        unum_template = load_yaml(f.read())

    with open('function-arn.yaml') as f:
        function_arn_mapping = load_yaml(f.read())

    print(f'Functions in this workflow:')
    print(f'{function_arn_mapping}')

    # Find the entry function
    for f in unum_template["Functions"]:
        if "Start" in unum_template["Functions"][f]["Properties"] and unum_template["Functions"][f]["Properties"]["Start"]:
            entry_function = f

    # invoke the workflow by invoking the start function
    print(f'\n\033[33mInvoking the entry function\033[0m\n')
    print(f'Entry Function: {entry_function}, ARN: {function_arn_mapping[entry_function]}\n')

    if os.path.isfile(args.payload) == False:
        print(f'\033[31m\nFailed: Cannot invoke workflow')
        print(f'Make sure input payload file exists. Specified payload: {args.payload}\033[0m')
        exit(1)

    # warm up rounds to 1. avoid Lambda cold starts 2. populate Cloudwatch logs
    # Warm up by invoking the workflow for a few times quickly
    print(f'Warm-up rounds ......')
    NUM_WARM_UP = 5
    for i in range(NUM_WARM_UP):
        suc, msg = invoke_lambda(function_arn_mapping[entry_function], args.payload)
        if suc == False:
            print(f'\033[31m\nWorkflow Invocation Failed during Warm-up: {msg}\033[0m\n')

    # wait for the log groups to populate

    # first wait for a period of time.
    print(f'\033[33m\nWaiting for warm-up rounds to complete and Cloudwatch logs to populate ...... \033[0m\n')
    time.sleep(int(args.wait_limit)*NUM_WARM_UP)

    LOGCHECK_TIMEOUT = 20 #sec
    if wait_workflow_log(LOGCHECK_TIMEOUT, function_arn_mapping) == False:
        print(f'Not all Lambda log are present')

    # delete existing Cloudwatch log streams without deleting the log groups
    print(f'Clearing all Cloudwatch log streams ......')
    if delete_workflow_log_streams(function_arn_mapping) == False:
        print(f'Failed to delete all existing log streams for all Lambda')
        exit(1)

    time.sleep(5) # Cloudwatch sometimes will partially delete a stream if a write happens quickly after delete initiates...

    # Run the actual experiments
    # Invoke workflow at a low rate for NUM_RUNS runs
    NUM_RUNS = 50
    print(f'\033[33mStart Experiment with {NUM_RUNS} runs\033[0m')

    for i in range(NUM_RUNS):
        print(f'{i+1}',end=' ')
        suc, msg = invoke_lambda(function_arn_mapping[entry_function], args.payload)
        if suc == False:
            print(f'\033[31mIteration {i} failed to invoke the entry function:{msg}\033[0m\n')
        time.sleep(args.interval)
    print('\n')

    time.sleep(int(args.wait_limit)*NUM_RUNS)

    # Collect the Cloudwatch logs and write to local files
    logs = get_workflow_execution_log(function_arn_mapping)

    if check_workflow_execution_success(logs):
        print(f'\033[32m\nAll functions in the workflow succeeded\033[0m')

    # write to a local directory "logs"
    try:
        os.mkdir('logs')
    except FileExistsError as e:
        pass

    local_timestamp = datetime.now()

    # pickle the logs
    # with open(f'logs-{local_timestamp}.pickle', 'wb') as p:
    #     pickle.dump(logs, p)

    for f in logs:
        fn = f'{f}-{local_timestamp}'
        print(f'\033[32m[*] Outputing logs for function {f}: logs/{fn}.xlsx\033[0m')

        write_streams_to_excel(logs[f], f'logs/{fn}.xlsx')




def write_streams_to_excel(streams, fn):
    workbook = xlsxwriter.Workbook(f'{fn}')

    # Add a bold format to use to highlight cells.
    bold = workbook.add_format({'bold': 1})

    for stream in streams:

        worksheet = workbook.add_worksheet()
        worksheet.write('A1', 'Timestamp', bold)
        worksheet.write('B1', 'Event Type', bold)
        worksheet.write('C1', 'Request ID', bold)
        worksheet.write('D1', 'Message', bold)

        # Start from the first cell below the headers.
        row = 1
        col = 0

        for e in stream:
            timestamp = e['timestamp']
            if e['message'].startswith('START'):
                event_type = 'START'
                request_id = e['message'].split(' ')[2].rstrip('\n')
            elif e['message'].startswith('END'):
                event_type = 'END'
                request_id = e['message'].split(' ')[2].rstrip('\n')
            elif e['message'].startswith('REPORT'):
                event_type = 'REPORT'
                request_id = e['message'].split(' ')[2]
                request_id = request_id.split('\t')[0]

                metrics = e['message'].split('\t')[1:]
                worksheet.write_string(row, col+3, str(metrics))

            else:
                raise ValueError(f'Unknown event type: {e["message"]}')

            worksheet.write_number(row, col, timestamp)
            worksheet.write_string(row, col+1, event_type)
            worksheet.write_string(row, col+2, request_id)

            row = row+1

    workbook.close()




def main():
    parser = argparse.ArgumentParser(description='Simple correctness test client')
    parser.add_argument('-r', '--restore', required=False, action="store_true", help='restore the unum application without running tests')
    parser.add_argument('-c', '--cleanup', required=False, action="store_true", help='restore the unum application after running tests')
    parser.add_argument('-l', '--wait_limit', required=False, default = 10, help="Wait time for Cloudwatch logs to populate")
    parser.add_argument('-i', '--interval', required=False, default = 5, help="Interval between invocations for performance test (in seconds)")
    parser.add_argument('--clear_cloudwatch_logs', required=False, action="store_true")
    parser.add_argument('-p', '--performance', required=False, action="store_true", help='run performance tests instead of correctness tests')
    parser.add_argument('--payload', required=False, default = 'events/event.json', help="Input payload file for workflow [default: events/event.json]")
    parser.add_argument('--skip_frontend', required=False, action="store_true", help='Skip frontend compilation')

    args = parser.parse_args()

    if args.restore:
        restore(args)
        return

    if args.performance:
        performance_test(args)
    else:
        aws_correctness_test(args)

    if args.cleanup:
        restore(args)

if __name__ == '__main__':
    main()