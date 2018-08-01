#!/bin/bash

# this script is called from crontab every hour

cd /home/pi/pi-hole-addon
sudo python repo-refresh.py	
