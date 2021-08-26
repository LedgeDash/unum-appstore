import json

def lambda_handler(event, context):
    user_names = event[0]
    urls = event[1]
    return {
        "user_names": user_names,
        "urls": urls
    }
