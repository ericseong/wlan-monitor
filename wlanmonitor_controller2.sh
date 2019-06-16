#!/bin/bash
# This script is written to make sure wlanmonitor.service runs all the time. If wlanmonitor seems not to be looping then it dumps some logs, restarts RPi and sends the logs at the next boot.

NO_LOOPING_ELAPSE=600
EXEC_DIR=/home/pi/work/wlan-monitor
LOG_DIR=$EXEC_DIR/log

echo "wlanmonitor_controller starts."

function dump_logs()
{
  echo "In dump_logs()"

  # get kernel log 
  dmesg > "$LOG_DIR/dmesg.txt"

  # get wlanmonitor service log
  systemctl -n 500 status wlanmonitor > "$LOG_DIR/systemctl_status.txt"

  # get syslog
  tail -n 2000 /var/log/syslog > "$LOG_DIR/syslog.txt"

  # get mail log
  tail -n 500 /var/log/mail.log > "$LOG_DIR/mail-log.txt"
  tail -n 500 /var/log/mail.err > "$LOG_DIR/mail-err.txt"
}

function send_logs()
{
  echo "In send_logs()"

  mail_cmd_line="echo '' | "
  mail_cmd_line+="mail -s \"Message from wlanmonitor_controller. This message has been sent because wlanmonitor_controller can't recover wlanmonitor from error and thus decide to reboot.\" "
  if [ -s "$LOG_DIR/dmesg.txt" ]; then
    mail_cmd_line+="-A \"$LOG_DIR/dmesg.txt\" "
  fi
  if [ -s "$LOG_DIR/systemctl_status.txt" ]; then
    mail_cmd_line+="-A \"$LOG_DIR/systemctl_status.txt\" "
  fi
  if [ -s "$LOG_DIR/syslog.txt" ]; then
    mail_cmd_line+="-A \"$LOG_DIR/syslog.txt\" "
  fi
  if [ -s "$LOG_DIR/mail-log.txt" ]; then
    mail_cmd_line+="-A \"$LOG_DIR/mail-log.txt\" "
  fi
  if [ -s "$LOG_DIR/mail-err.txt" ]; then
    mail_cmd_line+="-A \"$LOG_DIR/mail-err.txt\" "
  fi

  mail_cmd_line+="sunghd@yahoo.com,shdong@hotmail.com"
  eval $mail_cmd_line
  echo "mail has been sent with logs."
}

function connect_to_internet()
{
  wlanmonitor_startup2.sh

  ${EXEC_DIR}/wifiap_evaluate2.sh associate wlan0 coffeebreak_5g coffeebreak1**
  sleep 10 
  ${EXEC_DIR}/wifiap_evaluate2.sh connect_internet wlan0
  sleep 10 
  if [ $? -eq 0 ]; then
    return 0
  fi
  return 1
}

sleep 20

# send logs via email if there's some to send 
if find /home/pi/work/wlan-monitor/log -type f -name "*.txt" -mindepth 1 -print -quit 2>/dev/null | grep -q .; then
  echo "Trying to stop wlanmonitor.."
  systemctl stop wlanmonitor
  sleep 1

  connect_to_internet     
  if [ $? -eq 0 ]; then
    send_logs
    sleep 30
  else
    echo "Cannot connect to internet."
  fi

  find /home/pi/work/wlan-monitor/log -type f -name "*.txt" -exec rm -rv {} \;

  echo "Restaring wlanmonitor.."
  systemctl start wlanmonitor
  echo "Restarted wlanmonitor.."
  sleep 1

fi

sleep 600

# controller main loop 
while :
do
  # Check if the process continues looping
  stamp=$(</var/opt/wlanmonitor_tick)
  if [ -z "$stamp" ]; then
    stamp=0
  fi
  echo "$stamp"
  now=$(date +%s 2>&1)
  elapse="$(($now-$stamp))"
  echo "$elapse"

  if (( $elapse > $NO_LOOPING_ELAPSE )); then
    echo "wlanmonitor seems to be not looping.. Logs are dumped."
    dump_logs
    sleep 5
    echo "Forcing to reboot.."
    systemctl --force reboot
  else
    echo "wlanmonitor loops okay."
  fi

  sleep 600 

done

exit 1

# eof

