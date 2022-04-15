gcloud functions deploy excamera-reencode \
--runtime python38 \
--trigger-topic excamera-reencode \
--entry-point lambda_handler \
--memory 4096 \
--env-vars-file env.yaml 