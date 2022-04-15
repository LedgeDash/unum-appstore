gcloud functions deploy iot-pipeline-hvac-controller \
--runtime python38 \
--trigger-topic iot-pipeline-hvac-controller \
--entry-point lambda_handler \
--env-vars-file env.yaml 