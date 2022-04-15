gcloud functions deploy excamera-rebase \
--runtime python38 \
--trigger-topic excamera-rebase \
--entry-point lambda_handler \
--memory 4096 \
--env-vars-file env.yaml 