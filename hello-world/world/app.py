import boto3

client = boto3.client("sqs")


def lambda_handler(event, context):
    if "sqs" in event:
        data = event["data"]
        ret = f'{data} world!'
        # write to sqs
        client.send_message(QueueUrl=event["sqs"], MessageBody=ret)
    else:
        data = event

    return f'{data} world!'
