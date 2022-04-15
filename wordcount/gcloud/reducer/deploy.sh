gcloud functions deploy wordcount-reducer \
--runtime python38 \
--timeout 540s \
--trigger-topic wordcount-reducer \
--entry-point lambda_handler \
--env-vars-file env.yaml 