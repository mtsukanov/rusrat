#!/bin/bash   
source /var/beacon/clr/bin/activate
cd /var/beacon/clr/scripts
celery -A ctasks worker --loglevel=INFO --concurrency=5 -n worker1.%h 




