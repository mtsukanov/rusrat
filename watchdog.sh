#!/bin/bash   
source /var/beacon/clr/bin/activate
cd /var/beacon/clr/scripts/
./run_clr.py > /home/mtsukanov/run_clr_log/$(date +%Y%m%d)-$(date +%H%M%D).log
