import subprocess
import json
import boto3
import os
import glob

s3_client = boto3.client("s3")

def lambda_handler(event, context):

    bucket = event[1]["bucket"]

    y4m_files = glob.glob('/tmp/*.y4m')
    ivf_files = glob.glob('/tmp/*.ivf')
    state_files = glob.glob('/tmp/*.state')

    if "new decoder state" in event[1]:
        # 3rd and later chunk (e.g., 00000002+)
        my_key = event[1]["interframe-only ivf file"].split('.')[0]
        my_key = my_key.split('-')[0]
        prev_key = event[0]["new decoder state"].split('.')[0]
        prev_key = prev_key.split('-')[0]

        # download input files to local storage
        

        if os.path.isfile(f'/tmp/{prev_key}-0.state') == False or os.path.isfile(f'/tmp/{prev_key}-1.state') == False:
            rm_cmd = ['rm'] + state_files
            subprocess.run(rm_cmd, capture_output=True)
            s3_client.download_file(bucket, f'{prev_key}-0.state', f'/tmp/{prev_key}-0.state')
            s3_client.download_file(bucket, f'{prev_key}-1.state', f'/tmp/{prev_key}-1.state')

        if os.path.isfile(f'/tmp/{my_key}-1.ivf') == False:
            rm_cmd = ['rm'] + ivf_files
            subprocess.run(rm_cmd, capture_output=True)
            s3_client.download_file(bucket, f'{my_key}-1.ivf', f'/tmp/{my_key}-1.ivf')

        if os.path.isfile(f'/tmp/{my_key}.y4m'):
            # file already exists, skip downloading
            pass
        else:
            # file doesn't exist
            # delete other y4m files and then download the target y4m file
            rm_cmd = ['rm']+ y4m_files
            subprocess.run(rm_cmd, capture_output=True)
            s3_client.download_file(bucket, f'{my_key}.y4m', f'/tmp/{my_key}.y4m')

        # xc-enc -W -w 0.75 -i y4m -o 00000002.ivf -r -I 00000001-1.state -p 00000002-1.ivf -S 00000001-0.state -O 00000002-1.state 00000002.y4m
        ret = subprocess.run(["./xc-enc",
            "-W",
            "-w",
            "0.75",
            "-i",
            "y4m",
            "-o",
            f'/tmp/{my_key}.ivf',
            "-r",
            "-I",
            f'/tmp/{prev_key}-1.state',
            "-p"
            f'/tmp/{my_key}-1.ivf',
            "-S",
            f"/tmp/{prev_key}-0.state",
            "-O",
            f'/tmp/{my_key}-1.state',
            f'/tmp/{my_key}.y4m'
            ],
            capture_output=True)

        # upload my final interframe-only ivf file and my final decoder state to S3
        s3_client.upload_file(f'/tmp/{my_key}.ivf', bucket, f'{my_key}.ivf')
        s3_client.upload_file(f'/tmp/{my_key}-1.state', bucket, f'{my_key}-1.state')

        if (int(my_key)+1) % 16 == 0:
            print(f'[Unum] Rebase of chunk {my_key} completed')

        return {"bucket": bucket, "interframe-only ivf file": f'{my_key}.ivf', "new decoder state": f'{my_key}-1.state'}

    elif "ivf file" in event[1]:
        # 2nd chunk (e.g., 00000001)
        my_key = event[0]["file"].split('.')[0]
        my_key = my_key.split('-')[0]
        prev_key = event[1]["state"].split('.')[0]
        prev_key = prev_key.split('-')[0]

        # download input files to local storage
        if os.path.isfile(f'/tmp/{prev_key}-0.state') == False:
            rm_cmd = ['rm'] + state_files
            subprocess.run(rm_cmd, capture_output=True)
            s3_client.download_file(bucket, f'{prev_key}-0.state', f'/tmp/{prev_key}-0.state')

        if os.path.isfile(f'/tmp/{my_key}-0.ivf') == False:
            rm_cmd = ['rm'] + ivf_files
            subprocess.run(rm_cmd, capture_output=True)
            s3_client.download_file(bucket, f'{my_key}-0.ivf', f'/tmp/{my_key}-0.ivf')

        if os.path.isfile(f'/tmp/{my_key}.y4m') == False:
            rm_cmd = ['rm']+ y4m_files
            subprocess.run(rm_cmd, capture_output=True)
            s3_client.download_file(bucket, f'{my_key}.y4m', f'/tmp/{my_key}.y4m')

        # xc-enc -W -w 0.75 -i y4m -o 00000001.ivf -r -I 00000000-0.state -p 00000001-0.ivf -O 00000001-1.state 00000001.y4m
        ret = subprocess.run(["./xc-enc",
            "-W",
            "-w",
            "0.75",
            "-i",
            "y4m",
            "-o",
            f'/tmp/{my_key}.ivf',
            "-r",
            "-I",
            f'/tmp/{prev_key}-0.state',
            "-p"
            f'/tmp/{my_key}-0.ivf',
            "-O",
            f'/tmp/{my_key}-1.state',
            f'/tmp/{my_key}.y4m'
            ],
            capture_output=True)

        # upload my final interframe-only ivf file and my final decoder state to S3
        s3_client.upload_file(f'/tmp/{my_key}.ivf', bucket, f'{my_key}.ivf')
        s3_client.upload_file(f'/tmp/{my_key}-1.state', bucket, f'{my_key}-1.state')

        return {"bucket": bucket, "interframe-only ivf file": f'{my_key}.ivf', "new decoder state": f'{my_key}-1.state'}

    else:
        raise IOError(f'Unknown rebase input: {event}')