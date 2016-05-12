#!/bin/bash   
source /var/beacon/clr/bin/activate
cd /var/beacon/clr/scripts
celery -A transgen  worker --loglevel=DEBUG --concurrency=5 -n worker_trans.%h 
celery -A ctasks worker --loglevel=DEBUG --concurrency=5 -n worker_ctask.%h 

