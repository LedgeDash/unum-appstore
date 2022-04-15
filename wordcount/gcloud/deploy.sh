cd UnumMap0

bash deploy.sh &

cd ../mapper

bash deploy.sh &

cd ../partition

bash deploy.sh &

cd ../reducer

bash deploy.sh &

cd ../summary

bash deploy.sh &