#!/bin/bash   
source /var/beacon/clr/bin/activate
cd /var/beacon/clr/scripts
celery -A ctasks  worker --loglevel=INFO --concurrency=1 -n shoulder.%h 

#--concurrency=5
