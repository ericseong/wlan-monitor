#!/bin/bash

function send_logs()
{
  # get kernel log
  now=$(date +'%Y%m%d-%H%M')
  dmesg > "${now}-dmesg.txt"

  systemctl -n 100 status wlanmonitor > "${now}-systemctl_status.txt"
  tail -n 500 /var/log/syslog > "${now}-syslog.txt"
  tail -n 100 /var/log/mail.log > "${now}-mail-log.txt"
  tail -n 100 /var/log/mail.err > "${now}-mail-err.txt"

  # Now, let's send those files to mail. It seems that there's no way we can send body + attachment with mail utility and thus only attachments are sent without message body.
  echo '' |  mail -s "Sent from send_logs()" \
  -A "${now}-dmesg.txt" \
  -A "${now}-systemctl_status.txt" \
  -A "${now}-syslog.txt" \
  -A "${now}-mail-log.txt" \
  -A "${now}-mail-err.txt" \
  account@myemail.com 
}

send_logs

# eof

