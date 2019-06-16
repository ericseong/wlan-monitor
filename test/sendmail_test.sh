#!/bin/bash
(
 echo "From: Where you are  <localhost@localdomain>"
 echo "To: Your Name <your_email_address>"
 echo "Cc: His Name <your_email_address>"
 echo "Subject: Wlan report"
 echo "MIME-Version: 1.0"
 echo "Content-Type: text/html"
 echo "Content-Disposition: inline"
 echo
 echo "<pre>$(date +"%A %_d %b %Y %H:%M:%S") - status is TBD</pre>"
 echo
# cat $HOME/log.html
 echo
) | /usr/sbin/sendmail -v "account@myemail.com"
