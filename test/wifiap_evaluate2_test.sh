#!/bin/bash
# wifiap_evaluate2.sh force_scan interface
# wifiap_evaluate2.sh scan interface ssid
# wifiap_evaluate2.sh deassociate interface
# wifiap_evaluate2.sh associate interface ssid passwd
# wifiap_evaluate2.sh connect interface ip_address
# wifiap_evaluate2.sh connect_internet interface
# wifiap_evaluate2.sh regulatory_domain country_code
# wifiap_evaluate2.sh refresh_netif interface

while :
do
  wifiap_evaluate2.sh refresh_netif wlan0
  ip link set wlan0 down
  sleep 1
  wifiap_evaluate2.sh regulatory_domain wlan0 KR
  sleep 1
  modprobe -r brcmfmac
  sleep 1
  modprobe brcmfmac
  sleep 1
  ip link set wlan0 up 
  sleep 1
  wifiap_evaluate2.sh deassociate wlan0
  wifiap_evaluate2.sh associate wlan0 coffeebreak_5g coffeebreak1** 
  wifiap_evaluate2.sh connect wlan0 192.168.35.1
  wifiap_evaluate2.sh connect_internet wlan0
done

# eof

