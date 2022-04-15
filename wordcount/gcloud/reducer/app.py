import boto3

s3_client = boto3.client('s3',
         aws_access_key_id='AKIA23OYRNXYQSI3DABG',
         aws_secret_access_key= 'NbzlExvM+f4Fep22M0AENu116s+vU49+sc7hBGO7')

def readPerReducerSingle(bucket, partition):
    # Given a bucket and partition (e.g., reducer0/), return a map whose keys
    # are words in the partition and values are list of 1's, one for each
    # occurrence of the word. This function assumes that the files creates by
    # emitPerReducerSingle. In other words, the s3 directory should have a
    # list of subdirectories, one for each word. And under each word's
    # directory, there should be a list of uuid-named files, one for each
    # occurrence. These files do not have any contents.
    
    response = s3_client.list_objects(
        Bucket=bucket,
        Prefix=partition # e.g., reducer0/
    )

    data = [e['Key'] for e in response['Contents']]

    data = [e.split('/')[1:] for e in data]

    ret = {}
    for e in data:
        if e[0] in ret:
            ret[e[0]].append(1)
        else:
            ret[e[0]] = [1]
    return ret


def user_reduce(key, l):

    result = 0
    for e in l:
        result = result+e

    return result


def lambda_handler(event, context):
    bucket = event['bucket']
    partition = event['partition']

    data = readPerReducerSingle(bucket, partition)

    ret = {}
    for k in data:
        ret[k] = user_reduce(k, data[k])

    return ret