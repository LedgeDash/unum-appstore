#!/usr/bin/env python
from cfn_tools import load_yaml, dump_yaml
import json, os, sys, subprocess, time
import argparse

''' Simple correctness test client

'''
def restore():
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
    ret = subprocess.run(["ls", "-alt"], capture_output=True)

    # item 3,5,6
    ret = subprocess.run(["sf", "-c"], capture_output=True)

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
            print(f'AWS stack {stack_name} deleted')


def check_cloudformation_stack_exist(stack_name):
    ret = subprocess.run(["aws", "cloudformation", "describe-stacks",
                              "--stack-name", stack_name],
                              capture_output=True)

    if ret.returncode != 0:
        return False
    else:
        return True

def aws_correctness_test():
    # Test for AWS
    # clean up
    restore()

    # compile from Step Functions
    print(f'Compiling Step Function into unum workflow\n')
    os.system("sf -pu -o trim")
    print(f'\nSuccess\n')

    # create template.yaml and build
    os.system("unum-cli build -g")

    # deploy
    os.system("unum-cli deploy")

    
    with open('unum-template.yaml') as f:
        unum_template = load_yaml(f.read())

    with open('function-arn.yaml') as f:
        function_arn_mapping = load_yaml(f.read())

    # invoke the workflow by invoking the start function
    for f in unum_template["Functions"]:
        if "Start" in unum_template["Functions"][f]["Properties"] and unum_template["Functions"][f]["Properties"]["Start"]:
            entry_function = f

    print(f'\nInvoking the entry function\n')
    print(f'Entry Function: {entry_function}, ARN: {function_arn_mapping[entry_function]}')

    if os.path.isfile('events/event.json'):
        ret = invoke_lambda(function_arn_mapping[entry_function], 'events/event.json')
        if ret != 0:
            print(f'Workflow Invocation Failed')
            return -1
    else:
        print(f'Cannot invoke lambda. Need events/event.json')
        return -2

    # Get the CloudWatch Logs for all functions in the workflow


def invoke_lambda(function_name, payload_file):
    ret = subprocess.run(["aws", "lambda", "invoke",
                              "--function-name", function_name,
                              "--invocation-type", "RequestResponse",
                              "--payload", f'fileb://{payload_file}',
                              "tmp"],
                              capture_output=True)
    if ret.returncode == 0:
        stdout_msg = json.loads(ret.stdout.decode("utf-8"))
        if stdout_msg["StatusCode"] == 200:
            print(f'Execution Succeeded\nMessage Returned:')
            os.system('cat tmp')
            return 0
        else:
            print(f'Execution Failed\nMessage Returned:')
            os.system('cat tmp')
            return -1
    else:
        print(f'Invocation Failed:')
        print(ret.stderr.decode("utf-8"))
        return -2


def main():
    parser = argparse.ArgumentParser(description='Simple correctness test client')
    parser.add_argument('-r', '--restore', required=False, action="store_true")
    parser.add_argument('-c', '--cleanup', required=False, action="store_true")
    args = parser.parse_args()

    if args.restore:
        restore()
        return

    aws_correctness_test()

    if args.cleanup:
        restore()

if __name__ == '__main__':
    main()