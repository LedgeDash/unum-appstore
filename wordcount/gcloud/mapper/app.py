import boto3
import os
import uuid
import hashlib

NUM_REDUCERS = int(os.environ['NUM_REDUCERS'])
# https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html
s3_client = boto3.client('s3',
         aws_access_key_id='AKIA23OYRNXYQSI3DABG',
         aws_secret_access_key= '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')



def emitPerReducerSingle(word, bucket):

    # create a file in S3 with name reducer{reducerId}/{word}/{uuid}
    reducerId = int(hashlib.sha256(word.encode('utf-8')).hexdigest(), 16) % NUM_REDUCERS
    fileUuid = uuid.uuid4()
    objKey = f'reducer{reducerId}/{word}/{fileUuid}'

    try:
        s3_client.put_object(Bucket=bucket,
            Key=objKey)
    except ClientError as e:
        if e.response['Error']['Code'] == 'SlowDown':
            try:
                random.seed()
                wait_millisec = random.randint(0,2000)
                time.sleep(wait_millisec/1000)

                s3_client.put_object(Bucket=bucket,
                    Key=objKey)

            except ClientError as e:
                if e.response['Error']['Code'] == 'SlowDown':
                    try:
                        random.seed()
                        wait_millisec = random.randint(1000,4000)
                        time.sleep(wait_millisec/1000)
                        s3_client.put_object(Bucket=bucket,
                            Key=objKey)
                    except ClientError as e:
                        if e.response['Error']['Code'] == 'SlowDown':
                            print(f'[WARN] Skipping due to S3 SlowDown')
                            return



def user_map(text, bucket):

    words = text.split()

    for word in words:
        emitPerReducerSingle(word, bucket)

    return



def lambda_handler(event, context):
    if 'text' in event:
        text = event['text']
    elif 'pointer' in event:
        if 'bucket' in event['pointer']:
            # read from s3
            s3_client.download_file(event['pointer']['bucket'], event['pointer']['key'], f'/tmp/input.txt')
            with open(f'/tmp/input.txt') as f:
                text = f.read()
        else:
            print(f'[Mapper] Wrong input pointer')
            return
    else:
        print(f'[Mapper] No input data')
        return


    bucket = event['destination']

    user_map(text, bucket)

    return {
        "bucket": bucket,
        "numReducer": NUM_REDUCERS
    }