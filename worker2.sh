#!/bin/bash   
source /var/beacon/clr/bin/activate
cd /var/beacon/clr/scripts
celery -A ctasks  worker --loglevel=DEBUG -n shoulder.%h 

#--concurrency=5
