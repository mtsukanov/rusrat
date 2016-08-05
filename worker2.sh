#!/bin/bash   
source /var/beacon/clr/bin/activate
cd /var/beacon/clr/scripts
celery -A ctasks  worker --loglevel=DEBUG --concurrency=15 -n shoulder.%h 

#--concurrency=5
