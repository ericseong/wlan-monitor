#!/bin/bash

# wifiap_evaluate2.sh scan interface ssid
# wifiap_evaluate2.sh deassociate interface
# wifiap_evaluate2.sh associate interface ssid passwd
# wifiap_evaluate2.sh connect interface ip_address
# wifiap_evaluate2.sh connect_internet interface
# wifiap_evaluate2.sh regulatory_domain interface country_code
# wifiap_evaluate2.sh refresh_netif interface

while :; do

  wifiap_evaluate2.sh refresh_netif wlan0
  sleep 1
  if [ $? -ne 0 ]; then
    continue
  fi

  wifiap_evaluate2.sh scan wlan0 coffeebreak_5g
  sleep 1
  if [ $? -ne 0 ]; then
    continue
  fi

  wifiap_evaluate2.sh associate wlan0 coffeebreak_5g coffeebreak1** 
  sleep 10 
  if [ $? -ne 0 ]; then
    continue
  fi

  gateway=`netstat -rn | grep UG | grep $2 | awk '{print $2}'`
  wifiap_evaluate2.sh connect wlan0 $gateway 
  if [ $? -ne 0 ]; then
    continue
  fi

  wifiap_evaluate2.sh connect_internet wlan0
  if [ $? -ne 0 ]; then
    continue
  fi

done

# eof

