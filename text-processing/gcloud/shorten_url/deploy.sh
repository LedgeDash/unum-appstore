gcloud functions deploy text-processing-shorten-url \
--runtime python38 \
--trigger-topic text-processing-shorten-url \
--entry-point lambda_handler \
--env-vars-file env.yaml 