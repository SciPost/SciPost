#!/bin/bash
pkill -f bin/celery

cd /home/scipost/SciPost/scipost_django && source ../venv-3.8.5/bin/activate

mkdir -p /home/scipost/SciPost_logs
touch /home/scipost/SciPost_logs/celery_worker.log
touch /home/scipost/SciPost_logs/celery_beat.log
touch /home/scipost/SciPost_logs/rabbitmq.log

#nohup rabbitmq-server > /home/scipost/SciPost_logs/rabbitmq.log 2>&1 &
nohup celery -A SciPost_v1 worker --loglevel=info -E > /home/scipost/SciPost_logs/celery_worker.log 2>&1 &
nohup celery -A SciPost_v1 beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler > /home/scipost/SciPost_logs/celery_beat.log 2>&1 &
