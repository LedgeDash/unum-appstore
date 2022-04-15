gcloud functions deploy excamera-vpxenc \
--runtime python38 \
--trigger-topic excamera-vpxenc \
--entry-point lambda_handler \
--memory 4096 \
--env-vars-file env.yaml 