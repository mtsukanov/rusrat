cd /var/beacon/clr
timestamp = $(date +%s)
git add . 
git commit -m timestamp 
git push https://github.com/mtsukanov/rusrat.git master

