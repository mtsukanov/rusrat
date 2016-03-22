#!/bin/bash   
source /var/beacon/clr/bin/activate
cd /var/beacon/clr/scripts
celery -A transgen worker --loglevel=INFO --pool=solo --concurrency=5 -n worker2.%h 




