#!/bin/bash   
source /var/beacon/clr/bin/activate
cd /var/beacon/clr/scripts/
./run_clr.py
curl -v http://10.20.1.21:5000/checkpar/
#./run_clr.py | tee -a /home/mtsukanov/run_clr_log/$(date +%Y%m%d-%H%M%S).log
