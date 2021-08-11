import json
import random
import string

HOSTNAME="http://sh.ort"

def get_random_string(length):
    return ''.join(random.choice(string.ascii_lowercase) for i in range(length))

def lambda_handler(event, context):
    urls = event
    ret = []

    for u in urls:
        ret.append((u, f'{HOSTNAME}/{get_random_string(5)}'))

    return ret