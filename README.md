# Overview
This program is to monitor Wi-Fi connection status to the target access points in the radio range. For each access point, it tries to check the followings and stores the results per the AP.  
1. Whether the AP is in the radio range or not   
2. Whether the AP can be associated or not with given credentials  
3. Whether it can connect to the gateway or not via the associated AP   
4. Whether it can connect to the internet or not via the associated AP   

The gathered status info. is presented onto the e-paper display and is also sent to the given email addresses periodically. This program has been tested on RPi3 b+ running Rasbian stretch lite.  

# Usage
wlan_monitor.py --configfile wifi.json --toaddrs recipients.json --interval interval_in_seconds  
or,  
systemctl start wlanmonitor wlanmonitor_controller

# Install and run 
* Install Rasbian stretch lite from https://www.raspberrypi.org/downloads/raspbian/
* Clone this repository at /home/pi/work and run _sudo ./install.sh_
* Make sure the following configuration files are correctly given
  * Refer to wifi.json for the list of APs and the credentials to connect to 
  * Refer to recipients.json for the email addresses to get the status report
* epaper dir. is with e-paper io modules. Find the details at https://github.com/waveshare/e-Paper
* Set up gmail relay. I followed the steps given at https://tecadmin.net/sendmail-to-relay-emails-through-gmail-stmp/ 
* Enable two services, by executing _systemctl enable wlanmonitor wlanmonitor_controller_

# Known issues
* It seems that bcmfmac does not correctly set some of the regulatory domains. 
  https://github.com/raspberrypi/linux/issues/2997 
* Sometimes wireless extension can't be recovered into normal state without refreshing brcmfmac. And thus some work-arounds are there

# TODO
* As of now, only WPA1/2 personal mode is supported. WPA enterprise and WEP mode are not supported.

