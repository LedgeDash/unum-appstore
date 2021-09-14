#!/usr/bin/env python
import subprocess, os
from cfn_tools import load_yaml, dump_yaml

# Test for AWS

# clean up
ret = subprocess.run(["unum-cli", "build", "-c"], capture_output=True)
ret = subprocess.run(["rm", "-f", "function-arn.yaml", "template.yaml"], capture_output=True)
ret = subprocess.run(["ls", "-alt"], capture_output=True)


# check if the stack is deployed
with open('unum-template.yaml') as f:
    unum_template = load_yaml(f.read())
    stack_name = unum_template['Globals']['ApplicationName']

ret = subprocess.run(["aws", "cloudformation", "describe-stacks",
                  "--stack-name", stack_name],
                  capture_output=True)
if ret.returncode == 0:
    # stack exists
    ret = subprocess.run(["aws", "cloudformation", "delete-stack",
                          "--stack-name", stack_name],
                          capture_output=True)
    if ret.returncode != 0:
        print(f'\033[31mFailed to delete AWS stack {stack_name}\033[0m')
    else:
        print(f'AWS stack {stack_name} deleted')

# create template.yaml and build
# ret = subprocess.run(["unum-cli", "build", "-g"], capture_output=True)
os.system("unum-cli build -g")
# ret = subprocess.run(["unum-cli", "deploy"], capture_output=True)
os.system("unum-cli deploy")
