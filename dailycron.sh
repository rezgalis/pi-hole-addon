#!/bin/bash

# this script is called from crontab every midnight

cd /home/pi/pi-hole-addon
sudo python cron-run.py	
