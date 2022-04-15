To deploy the application on gcloud and run the experiment, first run the `deploy.sh` script which will use the `gcloud` cli to create 

1. `iot-pipeline-aggregator` gcloud function
2. `iot-pipeline-hvac-controller` gcloud function
3. `iot-pipeline-aggregator` gcloud pubsub topic
4. `iot-pipeline-hvac-controller` gcloud pubsub topic

Then run the experiment by running `python run_experiment.py`. It will invoke the `iot-pipeline-aggregator` gcloud function with `event.json` as its input payload, and collect the gcloud function log for both `iot-pipeline-aggregator` and `iot-pipeline-hvac-controller` and write the raw logs into `iot-pipeline-aggregator.log` and `iot-pipeline-hvac-controller.log`.

Note that `run_experiment.py` will only collect the logs related to the experiment. Any older logs are filtered out.