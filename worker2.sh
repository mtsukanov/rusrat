#!/bin/bash   
source /var/beacon/clr/bin/activate
cd /var/beacon/clr/scripts
celery -A transgen worker --loglevel=DEBUG --concurrency=5 -n worker2.%h 




