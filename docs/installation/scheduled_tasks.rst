***************
Scheduled tasks
***************

The tasks that involve large requests from CR are supposed to run in the background. For this to work, Celery is required. The following commands assume that you are in the `scipost_v1` main folder, inside the right virtual environment.

Celery depends on a broker, for which we use RabbitMQ. On MacOS one may simply install this by executing::

   brew update
   brew install rabbitmq


To start the RabbitMQ broker::

   nohup nice rabbitmq-server > ../logs/rabbitmq.log 2>&1 &


Then the Celery worker itself::

   nohup nice celery -A SciPost_v1 worker --loglevel=info -E > ../logs/celery_worker.log 2>&1 &


And finally `beat`, which enables setting up periodic tasks::

   nohup nice celery -A SciPost_v1 beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler > ../logs/celery_beat.log 2>&1 &


Note: on the staging server, these commands are contained in two shell scripts in the `scipoststg` home folder. Just run::

   ./start_celery.sh
