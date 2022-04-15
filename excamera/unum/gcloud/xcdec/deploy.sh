gcloud functions deploy excamera-xcdec \
--runtime python38 \
--trigger-topic excamera-xcdec \
--entry-point lambda_handler \
--memory 4096 \
--env-vars-file env.yaml 