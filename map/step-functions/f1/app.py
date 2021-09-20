def lambda_handler(event, context):
    with open('f1.output') as f:
        ret = f.read()

    return {
        "index": event,
        "ret": ret
    }