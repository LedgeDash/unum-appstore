gcloud functions deploy text-processing-unum-parallel-0 \
--runtime python38 \
--trigger-topic text-processing-unum-parallel-0 \
--entry-point lambda_handler \
--env-vars-file env.yaml 