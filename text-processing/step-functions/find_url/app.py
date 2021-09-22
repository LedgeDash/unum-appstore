import json
import re

url_pattern=re.compile(r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+")

def lambda_handler(event, context):
    urls = url_pattern.findall(event)
    return urls