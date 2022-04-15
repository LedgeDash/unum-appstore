gcloud functions deploy text-processing-find-url \
--runtime python38 \
--trigger-topic text-processing-find-url \
--entry-point lambda_handler \
--env-vars-file env.yaml 