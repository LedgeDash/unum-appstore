gcloud functions deploy iot-pipeline-aggregator \
--runtime python38 \
--trigger-topic iot-pipeline-aggregator \
--entry-point lambda_handler \
--env-vars-file env.yaml 