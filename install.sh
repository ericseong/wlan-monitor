#!/bin/bash

sudo apt update
sudo apt install python-pip
sudo pip install RPi.GPIO
sudo pip install spidev
sudo apt install ttf-wqy-zenhei ttf-wqy-microhei
sudo apt install libjpeg-dev
sudo apt install libpng-dev
sudo apt install libfreetype6-dev
sudo pip install image
sudo apt install sendmail mailutils sendmail-bin

cp -f wlanmonitor_startup2.sh /usr/local/bin
cp -f wifiap_evaluate2.sh /usr/local/bin
cp -f wlanmonitor_controller2.sh /usr/local/bin

cp -f systemd-service/wlanmonitor.service /etc/systemd/system/ 
cp -f systemd-service/wlanmonitor_controller.service /etc/systemd/system/ 

# eof

