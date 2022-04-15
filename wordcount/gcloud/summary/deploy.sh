gcloud functions deploy wordcount-summary \
--runtime python38 \
--timeout 540s \
--trigger-topic wordcount-summary \
--entry-point lambda_handler \
--env-vars-file env.yaml 