#!/bin/bash
# This script has some wlan utility functions using iw and etc, basically to evaluate wireless lan AP in the radio range.
# Tested on Rasbian stretch lite running on Raspberry Pi 3B+

# Usage: 
# wifiap_evaluate2.sh scan interface ssid
# wifiap_evaluate2.sh deassociate interface
# wifiap_evaluate2.sh associate interface ssid passwd
# wifiap_evaluate2.sh connect interface ip_address
# wifiap_evaluate2.sh connect_internet interface
# wifiap_evaluate2.sh regulatory_domain interface country_code
# wifiap_evaluate2.sh refresh_netif interface

# brcmfmac unload
function mac_unload()
{
  while :
  do
    modprobe -r brcmfmac 
    modprobe -r cfg80211
    if [ $? -eq 0 ]; then
      echo "brcmfmac/cfg80211 is unloaded."
      break
    fi
    sleep 1
  done

  sleep 1
}

function mac_load()
{
  while :
  do
    modprobe brcmfmac 
    if [ $? -eq 0 ]; then
      echo "brcmfmac is loaded."
      break
    fi
    sleep 1
  done

  sleep 1
}

function mac_refresh()
{
  mac_unload
  mac_load
}

# netif down
function netif_down()
{
  systemctl stop dhcpcd
  systemctl stop wpa_supplicant
  sleep 1
  ip link set $1 down 
  echo "$1 is down with wpa_supplicant and dhcpcd."
  sleep 1
  
  return 0
}

# netif up
function netif_up()
{
  while :
  do
    ip link set $1 up 
    if [ $? -eq 0 ]; then
      systemctl start wpa_supplicant
      sleep 1
      systemctl start dhcpcd
      sleep 1
      echo "$1 is up with wpa_supplicant and dhcpcd."
      break
    fi
    sleep 1
  done

  return 0
}

# netif refresh
function refresh_netif()
{
  netif_down $1
  mac_unload
  mac_load
  netif_up $1

  sleep 2
  return 0
}

# reg set - deprecated. rather use refresh_netif to set to default reg. domain
function reg_set()
{
  while :
  do
    iw reg set $1
    if [ $? -eq 0 ]; then
      echo "Reg domain sets to $1."
      break
    fi
    sleep 1
  done

  sleep 3
  return 0
}

# wpa reconfigure
function wpa_reconfig()
{
  while :
  do
    wpa_cli -i $1 reconfigure
    res=$?
    if [ $res -eq 0 ]; then
      echo "wpa is now reconfigured for $1."
      break
    fi
    sleep 1
    refresh_netif $1
  done

  sleep 1
  return 0
}

# Scan ap and check if $2 is there
# Before executing scan, we need to make sure that wlan is not associated. Once associated, it's not allowed to scan other channels
function try_scan()
{
  while :
  do
    res="$(iw $1 scan | grep SSID)" 
    if [ -z "$res" ]; then
      sleep 1
    else
      if echo "$res" | grep -q "$2"; then
        return 0
      else
        return 1
      fi
    fi
    sleep 1
  done

  return 1 
}

# Deassociate netif 
function deassociate()
{
  iw dev $1 link | grep "Not connected."
  if [ $? -eq 0 ]; then
    echo 'Currently not connected. No need to issue deassociate here.'
    return 1
  fi

  if [ $? -eq 0 ]; then
    text=$'ctrl_interface=DIR=/var/run/wpa_supplicant\n'
    text+=$'update_config=1\n'
    text+=$'country=UK\n'
    text+=$'network={\n'
    text+=$'\tscan_ssid=1\n'
    text+=$'\tssid='
    text+=$'\"This ssid is a non-existing.\"'
    text+=$'\n'
    text+=$'\tpsk='
    text+=$'\"FAKEPASSWD\"'
    text+=$'\n'
    text+=$'}'

    echo "${text[*]}" > /etc/wpa_supplicant/wpa_supplicant.conf
    echo "wpa_reconfig 1"
    wpa_reconfig $1
    echo "wpa_reconfig 2"
  fi

  return $?
}

function try_associate()
{
  local res=1
  local count=0

  text=$'ctrl_interface=DIR=/var/run/wpa_supplicant\n'
  text+=$'update_config=1\n'
  text+=$'country=UK\n'
  text+=$'network={\n'
  text+=$'\tscan_ssid=1\n'
  text+=$'\tssid=\"'
  text+=$2
  text+=$'\"\n'
  text+=$'\tpsk=\"'
  text+=$3
  text+=$'\"\n'
  text+=$'}'

  echo "${text[*]}" > /etc/wpa_supplicant/wpa_supplicant.conf
  echo "wpa_reconfig 1"
  wpa_reconfig $1
  echo "wpa_reconfig 2"
  while :; do
    sleep 1
    ((count++))
    iw $1 link | grep $2
    res=$?
    if [ $res -eq 0 ]; then
      echo "$2 is associated at count $count."
      break
    fi
    if [ $count -ge 30 ]; then
      break
    fi
  done
  
  return $res 
}

function try_connect()
{
  ping -c 1 -W 10 $2 > /dev/null 2>&1
  return $?
}

# Check if we can connect to internet
function try_connect_internet()
{
  local r=0
  declare -a arr=("http://www.google.com" "http://www.facebook.com" "http://www.github.com")
  for i in "${arr[@]}"
  do
    wget --spider --timeout=10 --quiet "$i"
    r=$?
    if [ $r -eq 0 ]; then
      break;
    #else
    #  echo "Can't connect. $?"
    fi
  done

  return $r
}

# wifiap_evaluate2.sh scan interface ssid
if [ $1 == "scan" ]; then
  try_scan $2 $3
  if [ $? -eq 0 ]; then
    echo "Okay, $3 is in the radio range."
    exit 0
  else
    echo "$3 seems to be out of radio range."
    exit 1
  fi

# wifiap_evaluate2.sh dessociate interface
elif [ $1 == "deassociate" ]; then
  deassociate $2
  if [ $? -eq 0 ]; then
    echo "Now deassociated with $2."
    exit 0
  else
    echo "Can't deassociate $2."
    exit 1
  fi

# wifiap_evaluate2.sh associate interface ssid passwd
elif [ $1 == "associate" ]; then
  echo 'associate'
  try_associate $2 $3 $4
  if [ $? -eq 0 ]; then
    echo "Okay, now associated with $3."
    exit 0
  else
    echo "Can't associate $3."
    exit 1
  fi

# wifiap_evaluate2.sh connect interface ip_address # try connect to given ip
# if ip_address is not given, then we try connect to default gw of given interface
elif [ $1 == "connect" ]; then
  if [ "$#" -eq 2 ]; then
    # see if we can see the gateway for the associated AP 
    ok=0
    for run in {1..10}; do 
      sleep 1
      netstat -rn | grep UG
      if [ $? -eq 0 ]; then
        ok=1; break
      fi 
    done
    if [ $ok -eq 0 ]; then
      echo "Can't find gateway via $2."
      exit 1
    fi

    # try to connect to gateway 
    gateway=`netstat -rn | grep UG | grep $2 | awk '{print $2}'`
    try_connect $2 $gateway 
    if [ $? -eq 0 ]; then
      echo "Okay, now connected to $gateway via $2."
      exit 0
    else
      echo "Can't connect to $gateway via $2." 
      exit 1
    fi
  else
    try_connect $2 $3
    if [ $? -eq 0 ]; then
      echo "Okay, now connected to $3 via $2."
      exit 0
    else
      echo "Can't connect to $3 via $2."
      exit 1
    fi
  fi

# wifiap_evaluate2.sh connect_internet interface
elif [ $1 == "connect_internet" ]; then
  try_connect_internet $2
  if [ $? -eq 0 ]; then
    echo "Okay, now connected to internet via $2."
    exit 0
  else
    echo "Can't connect to internet via $2."
    exit 1
  fi

# regulatory domain set
# some workaround is included due to the issue registered at https://github.com/raspberrypi/linux/issues/2997  
elif [ $1 == "regulatory_domain" ]; then
  reg_set $3
  if [ $? -eq 0 ]; then
    echo "Okay, regulatory domain is set to $3"
    exit 0
  else
    echo "Can't set regulatory domain."
    exit 1
  fi

# refresh netif
elif [ $1 == "refresh_netif" ]; then
  refresh_netif $2
  if [ $? -eq 0 ]; then
    echo "Okay, netif $2 is refreshed."
    exit 0
  else
    echo "Can't refresh netif."
    exit 1
  fi

fi

# exception
exit 1

# eof

