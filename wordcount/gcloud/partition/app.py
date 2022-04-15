import boto3


s3_client = boto3.client('s3',
         aws_access_key_id='AKIA23OYRNXYQSI3DABG',
         aws_secret_access_key= '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')


def lambda_handler(event, context):
    bucket = event[0]['bucket']
    numReducer = event[0]['numReducer']

    # # get all directories in the bucket that are "reducer" and return them in
    # # a sorted list

    response = s3_client.list_objects(
        Bucket=bucket,
        Prefix='',
        Delimiter='/'
    )

    partitions = [{'bucket': bucket, 'partition': e['Prefix']} for e in response['CommonPrefixes']]

    return partitions