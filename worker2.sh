#!/bin/bash   
source /var/beacon/clr/bin/activate
cd /var/beacon/clr/scripts
celery -A proj  worker --loglevel=DEBUG --concurrency=1 -n shoulder.%h 

#--concurrency=5
