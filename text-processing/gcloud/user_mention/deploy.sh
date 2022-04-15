gcloud functions deploy text-processing-user-mention \
--runtime python38 \
--trigger-topic text-processing-user-mention \
--entry-point lambda_handler \
--env-vars-file env.yaml 