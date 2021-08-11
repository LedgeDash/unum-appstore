import json
import boto3
import uuid
import yaml
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

with open("dbconfig.yaml") as f:
    config = yaml.load(f.read(), Loader=Loader)
    db_name = config["PostDatabase"]

post_db = boto3.client("dynamodb")

def lambda_handler(event, context):

    user_names=[{"S": n} for n in event['user_names']]
    urls = [{"L": [{"S": e[0]}, {"S": e[1]}]} for e in event['urls']]

    dynamodb_client.put_item(TableName=db_name,
            Item={
                'postid': {'S': f'{uuid.uuid4()}'},
                'user_names': {"L": user_names},
                'urls': {"L": urls}
            }
        )

    return event
