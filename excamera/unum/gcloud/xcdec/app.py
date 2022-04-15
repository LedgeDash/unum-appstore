import subprocess
import json
import boto3
import os
import glob

s3_client = boto3.client('s3',
         aws_access_key_id='AKIA23OYRNXYQSI3DABG',
         aws_secret_access_key= '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')

def lambda_handler(event, context):
    bucket = event['bucket']
    fn = event['file']
    key = fn.split('.')[0]
    key = key.split('-')[0]
    output_fn=f'{key}-0.state'

     # download file to local storage
    s3_client.download_file(bucket, fn, f"/tmp/{fn}")

    # xc-dump
    ret = subprocess.run(["./xc-dump",
        f'/tmp/{fn}',
        f'/tmp/{output_fn}'],
        capture_output=True)

    # upload decoder state file back to S3
    s3_client.upload_file(f'/tmp/{output_fn}', bucket, output_fn)

    ivf_files = glob.glob('/tmp/*.ivf')
    state_files = glob.glob('/tmp/*.state')
    rm_cmd = ['rm'] + state_files + ivf_files
    subprocess.run(rm_cmd, capture_output=True)

    return {"bucket": bucket, "ivf file": fn, "state": output_fn}