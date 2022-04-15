gcloud functions deploy excamera-unum-map-0 \
--runtime python38 \
--trigger-topic excamera-unum-map-0 \
--entry-point lambda_handler \
--memory 4096 \
--env-vars-file env.yaml 