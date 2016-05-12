#!/bin/bash   
source /var/beacon/clr/bin/activate
cd /var/beacon/clr/scripts
celery -A ctasks  worker --loglevel=DEBUG --concurrency=5 --pool=solo -n worker2.%h 


