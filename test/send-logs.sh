#!/bin/bash

function send_logs()
{
  # get kernel log
  now=$(date +'%Y%m%d-%H%M')
  dmesg > "${now}-dmesg.txt"

  # get wlanmonitor service log
  systemctl -n 100 status wlanmonitor > "${now}-systemctl_status.txt"

  # get syslog
  tail -n 500 /var/log/syslog > "${now}-syslog.txt"

  # get mail log
  tail -n 100 /var/log/mail.log > "${now}-mail-log.txt"
  tail -n 100 /var/log/mail.err > "${now}-mail-err.txt"

  # now, send those files to mail
  # It seems that there's no way we can send body + attachment with mail utility \
  # and thus only attachments are sent without message body.
echo '' |  mail -s "Message from wlanmonitor_controller. This message has been sent because wlanmonitor_controller can't recover wlanmonitor to normal state and thus decide to reboot. Before issuing reboot, this message has been sent." \
  -A "${now}-dmesg.txt" \
  -A "${now}-systemctl_status.txt" \
  -A "${now}-syslog.txt" \
  -A "${now}-mail-log.txt" \
  -A "${now}-mail-err.txt" \
  coffeebreak2.2019@gmail.com 
}

send_logs

# eof

