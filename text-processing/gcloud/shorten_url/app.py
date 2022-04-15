import random
import string

HOSTNAME="http://sh.ort"

def get_random_string(length):
    return ''.join(random.choice(string.ascii_lowercase) for i in range(length))

def lambda_handler(event, context):
    urls = event
    ret = []

    for u in urls:
        # nested arrays are not supported by firestore:
        # https://stackoverflow.com/questions/54785637/cloud-functions-error-cannot-convert-an-array-value-in-an-array-value
        ret.append({u: f'{HOSTNAME}/{get_random_string(5)}'})

    return ret
