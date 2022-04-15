gcloud functions deploy text-processing-create-post \
--runtime python38 \
--trigger-topic text-processing-create-post \
--entry-point lambda_handler \
--env-vars-file env.yaml 