def lambda_handler(event, context):
    if "sqs" in event:
        return {
            "sqs": event["sqs"],
            "data": "Hello"
        }
    return "Hello"
