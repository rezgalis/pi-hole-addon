#!/bin/bash

#this script is called from command-line to trigger installation of https://github.com/rezgalis/pi-hole-addon repo

#install pre-requisites
apt-get install git python-pip -y
pip install gitpython

#clone git repository and remove unnecessary files
cd /home/pi
rm pi-hole-addon/ -R
git clone https://github.com/rezgalis/pi-hole-addon.git
cd pi-hole-addon/
mkdir repo
rm .git/ -R
rm blacklists/*
rm daily-job.py
cp blacklists/95-restrict.conf /etc/dnsmasq.d/95-restrict.conf

#TO-DO:
#need to update (!) /etc/hosts in similar manner as crontab with extra details

#chmod cron scripts
chmod +x dailycron.sh
chmod +x hourlycron.sh

#install crontab
(crontab -l ; echo "@hourly sudo /home/pi/pi-hole-addon/hourlycron.sh >> /home/pi/pi-hole-addon/logs/hourlycron.log 2>&1") | sort - | uniq - | crontab -
(crontab -l ; echo "@midnight sudo /home/pi/pi-hole-addon/dailycron.sh >> /home/pi/pi-hole-addon/logs/dailycron.log 2>&1") | sort - | uniq - | crontab -

#trigger python job this time
./hourlycron.sh
