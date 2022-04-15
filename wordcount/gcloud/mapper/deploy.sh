gcloud functions deploy wordcount-mapper \
--runtime python38 \
--timeout 540s \
--trigger-topic wordcount-mapper \
--entry-point lambda_handler \
--env-vars-file env.yaml 