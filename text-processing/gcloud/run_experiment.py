import json
import subprocess
import os
import time
from datetime import datetime, timezone


APP_NAME='Text Processing'
ENTRY_FUNCTION_TOPIC = 'text-processing-unum-parallel-0'
FUNCTION_NAMES = ['text-processing-unum-parallel-0', 'text-processing-user-mention', 'text-processing-shorten-url', 'text-processing-create-post', 'text-processing-publish', 'text-processing-find-url' ]
NUM_ITERATIONS = 20
WAIT_FOR_LOG = 60 # seconds



def invoke(topic, data):

    ret = subprocess.run(['gcloud', 'pubsub', 'topics', 'publish', topic, f'--message={json.dumps(data)}'], capture_output=True)

    if ret.returncode != 0:
        print(f'{ret.stderr.decode("utf-8")}')
    else:
        # print(f'{ret.stdout.decode("utf-8")}')
        return



def get_gcloud_function_log(function_name, start_time):

    ret = subprocess.run(['gcloud', 'functions', 'logs', 'read', function_name, f'--start-time={start_time.isoformat()}', f'--limit=1000'], capture_output=True)
    # ret = subprocess.run(['gcloud', 'functions', 'logs', 'read', function_name])

    print

    if ret.returncode != 0:
        print(f'{ret.stderr.decode("utf-8")}')
    else:
        return ret.stdout.decode("utf-8")



def main():

    with open('event.json') as f:
        input_data = json.loads(f.read())

    experiment_start_datetime = datetime.now(timezone.utc)

    print(f'Starting experiment with {APP_NAME} at {experiment_start_datetime.isoformat()}')

    for i in range(NUM_ITERATIONS):
        print(f'iteration #{i+1}', end='\r')
        invoke(ENTRY_FUNCTION_TOPIC, input_data)
        time.sleep(2)

    print(f'Waiting {WAIT_FOR_LOG} seconds for logs to populate')
    time.sleep(WAIT_FOR_LOG)

    for f in FUNCTION_NAMES:

        print(f'Saving logs for {f} into {f}.log')
        log_raw = get_gcloud_function_log(f, experiment_start_datetime)
        with open(f'{f}.log', 'w') as f:
            f.write(log_raw)




if __name__ == '__main__':
    main()