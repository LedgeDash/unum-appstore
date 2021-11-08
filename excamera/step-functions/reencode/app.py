import subprocess
import json
import boto3
import os
import glob

s3_client = boto3.client("s3")

def lambda_handler(event, context):
    bucket = event["bucket"]
    prev_state  = event["prev state"]
    my_ivf_file = event["ivf file"]
    key = my_ivf_file.split('.')[0]
    key = key.split('-')[0]
    my_interframe_ivf_fn = f'{key}-1.ivf'
    my_new_state = f'{key}-1.state'
    my_raw_video= f'{key}.y4m'

    # download file to local storage

    y4m_files = glob.glob('/tmp/*.y4m')
    ivf_files = glob.glob('/tmp/*.ivf')
    state_files = glob.glob('/tmp/*.state')

    if os.path.isfile(f'/tmp/{prev_state}') == False:
        rm_cmd = ['rm'] + state_files
        subprocess.run(rm_cmd, capture_output=True)

        s3_client.download_file(bucket, prev_state, f"/tmp/{prev_state}")

    s3_client.download_file(bucket, my_ivf_file, f"/tmp/{my_ivf_file}")

    if os.path.isfile(f'/tmp/{my_raw_video}') == False:
        rm_cmd = ['rm'] + y4m_files
        subprocess.run(rm_cmd, capture_output=True)
        
        s3_client.download_file(bucket, my_raw_video, f"/tmp/{my_raw_video}")

    # re-encode: replace the first keyframe with an interframe
    #./xc-enc -W -w 0.75 -i y4m -o 2-1.ivf -r -I 1-0.state -p 2-0.ivf -O 2-1.state 2.y4m
    ret = subprocess.run(["./xc-enc",
        "-W",
        "-w",
        "0.75",
        "-i",
        "y4m",
        "-o",
        f'/tmp/{my_interframe_ivf_fn}',
        "-r",
        "-I",
        f'/tmp/{prev_state}',
        "-p"
        f'/tmp/{my_ivf_file}',
        "-O",
        f'/tmp/{my_new_state}',
        f'/tmp/{my_raw_video}'
        ],
        capture_output=True)


    # upload recoded interframe-only ivf file and new decoder state file back to S3
    s3_client.upload_file(f'/tmp/{my_interframe_ivf_fn}', bucket, my_interframe_ivf_fn)
    s3_client.upload_file(f'/tmp/{my_new_state}', bucket, my_new_state)

    return {"bucket": bucket, "interframe-only ivf file": my_interframe_ivf_fn, "new decoder state": my_new_state}
