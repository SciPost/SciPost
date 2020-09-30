#!/bin/bash
pkill -f bin/celery

cd /home/scipost/webapps/scipost_py38/SciPost && source ../venv3.8/bin/activate

mkdir -p ./local_files/logs
touch ./local_files/logs/celery_worker.log
touch ./local_files/logs/celery_beat.log
touch ./local_files/logs/rabbitmq.log

nohup rabbitmq-server > ./local_files/logs/rabbitmq.log 2>&1 &
nohup celery -A SciPost_v1 worker --loglevel=info -E > ./local_files/logs/celery_worker.log 2>&1 &
nohup celery -A SciPost_v1 beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler > ./local_files/logs/celery_beat.log 2>&1 &
