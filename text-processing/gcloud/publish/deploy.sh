gcloud functions deploy text-processing-publish \
--runtime python38 \
--trigger-topic text-processing-publish \
--entry-point lambda_handler \
--env-vars-file env.yaml 