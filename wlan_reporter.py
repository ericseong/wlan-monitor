#!/usr/bin/python2
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, unicode_literals, print_function

import wlan_logger
log = wlan_logger.logger.get()

import os
import sys
import time
import string
import subprocess
import traceback
import json
import socket
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from PIL import Image,ImageDraw,ImageFont
from epaper import epd2in7

class Reporter(object):

  def __init__( self, timeout ):
    self._timeout = timeout 
    self._status = None 

  def isUpdated( self, status ):
    '''
    Check if any of the network status has been changed
    '''

    if self._status == None: # initial report
      self._status = status
      return True
 
    for ec in status:
      for ep in self._status: 
        if ec['ssid'] == ep['ssid']:
          if ec['scan'] != ep['scan'] or \
          ec['associate'] != ep['associate'] or \
          ec['gateway'] != ep['gateway'] or \
          ec['internet'] != ep['internet']:
            self._status = status
            return True
       
    return False 

  def send( self ):
    pass 

class EmailReporter( Reporter ):

  def __init__( self, to, timeout ):
    super( EmailReporter,self ).__init__( timeout )
    _recipients = ""
    for r in to:
      #log.debug( r )
      if "" != _recipients:
        _recipients += ','
      _recipients += r
    self._to = _recipients 
    log.debug( self._to )
    self._timeout = timeout
    self._subject = "1st floor Wi-Fi monitor"
    self._send_count = 1
    self._email_freq = 1800 # will send email in every 30 minutes 
    #self._email_freq = 60 # will send email in every minute 

    return

  def _getToAddrs( self ):
    return self._to

  def _getTimeout( self ):
    return self._timeout

  def _getSubject( self ):
    return self._subject

  def _getSendCount( self ):
    return self._send_count

  def _setSendCount( self, count ):
    self._send_count = count 

  def getEmailFreq( self ):
    return self._email_freq

  def _formatMessage( self, statuses ):
    _html = """\
      <html>
      <header>
      <style>
        p.note {
          font-style: italic;
          font-size: small;
          padding: 12px;
        }
        table, th, td {
          border-collapse: collapse;
        }
        th, td {
          padding: 10px;
          text-align: left;
        }
        th {
          border-bottom: 1px solid #ff8c00
        }
        tr {
          border-bottom: 1px solid #ddd;
        }
      </style>
      </header>

      <body>
      <br>
      <p class='intro'>
        This report has been sent from wlan monitor installed in CoffeeBreak Season 2.
      </p>
      <br>
        <table style="width:100%">
          <tr>
            <th>Time</th>
            <th>SSID</th>
            <th>Found by scan</th>
            <th>Associated to AP</th>
            <th>Connected to Gateway</th>
            <th>Connected to Internet</th>
            <th>Signal strength</th>
          </tr>\n
    """

    _key = ['time', 'ssid', 'scan', 'associate', 'gateway', 'internet', 'signal']
    for _el in statuses:
      log.debug( "_el is {}".format( _el ) )
      _html += "<tr>"
      for _k in _key:
        if _k != 'ssid' and _k != 'signal' and _k != 'time':
          _str = 'yes' if _el[_k] == 1 or _el[_k] == '1' else 'no'
        else:
          _str = str( _el[_k] )
        _html += "<td>{}</td>".format( _str )
      _html += "</tr>\n"

    _html += """\
        </table>
        <br>
      <p class='note'>
    """

    _now = datetime.now(); _dt = _now.strftime("%B %d. %Y, %H:%M:%S")
    _html += 'Last update: {}'.format( _dt )

    _html += """\
      </p>
      </body>
      </html>
    """

    return _html 
      
  def send( self, statuses, attachment ):
    '''
    Send email with accumulated stats
    arg - a list of status
    arg - files to attached
    '''

    _statuses = sorted( statuses, key = lambda i: i['time'], reverse=True )  
    _statuses = sorted( _statuses, key = lambda i: i['ssid'] )  
    _message = self._formatMessage( _statuses )
    log.debug( _message )

    '''
    Note that mail subject is with send_count considering mail cannot guarantee ordered delivery.
    '''
    _cmd = 'echo \"{}\" | \
      mail -a "Content-type: text/html;" -s \"[{:5d}] {}\" {}'.format( \
      _message, self._getSendCount(), self._getSubject(), self._getToAddrs() \
      )

    if attachment:
      for a in attachment:
        if os.path.isfile( a ):
          _cmd += '-A {} '.format( a )

    # FIXME! workaround to avoid the complaint from mail utility when hostname is unknown
    _hostname = socket.gethostname()
    with open( '/etc/hosts', 'r' ) as _hosts:
      _lines = _hosts.readlines()

    _line_index = 0; _found = False; _valid = False; 
    for _line in _lines:
      _stripped_line = _line.split()
      if len( _stripped_line ) != 0 and _stripped_line[0] == '127.0.0.1':
        _valid = True
        if _hostname in _stripped_line[1:]:
          _found = True
        break
      _line_index += 1

    if _valid == True and _found == False:
      _lines[_line_index] = _lines[_line_index].rstrip() + ' {}\n'.format( _hostname ) 
      log.info( "A new hostname - {} is added to /etc/hosts".format( _hostname ) )

    with open( '/etc/hosts', 'w' ) as _hosts:
      _hosts.writelines( _lines )
    # end of FIXME!

    _ret = subprocess.call( _cmd, shell=True )
    if _ret == 0:
      log.info( "Email has successfully been sent with count {}.".format( self._getSendCount() ) )
      self._setSendCount( self._getSendCount() + 1 )
    else:
      log.warning( "Can't send email" )

    return

# e-paper reporter - displays status to epd
class EpdReporter( Reporter ):

  def __init__( self, timeout ):
    super( EpdReporter, self ).__init__( timeout ) 

  def send( self, status ):

    try:
      log.info( 'Start drawing to epd' )
      log.debug( status )
      epd = epd2in7.EPD()
      epd.init()
      epd.Clear(0xff)

      WIDTH = epd2in7.EPD_WIDTH; HEIGHT = epd2in7.EPD_HEIGHT
      x = y = 0;
      marginXBorder = marginYBorder = marginFooter = 2; marginYText = 4; marginXText = marginXCircle = 2
      marginHeader = 8;

      font16 = ImageFont.truetype( '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc' , 16); heightHeader = widthHeader = 16
      font14 = ImageFont.truetype( '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc' , 14); heightText = widthText = 14; heightCircle = widthCircle = 12; cy = 4 # y-axis compensation for circle
      font12 = ImageFont.truetype( '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc' , 12); heightFooter = widthFooter = 12

      vImage = Image.new( '1', (WIDTH, HEIGHT), 255 )
      draw = ImageDraw.Draw( vImage )

      y = marginYBorder
      draw.text( ( marginXBorder, y ), "Wi-Fi status", font = font16, fill = 0 )
      y += heightHeader
      draw.line( ( marginXBorder, y, WIDTH-1, y ), fill = 0 )

      y += marginHeader;
      for el in status:
        draw.text( ( marginXBorder, y ), el['ssid'] + ' ', font = font14, fill = 0 )

        x = WIDTH - marginXBorder; x -= ( widthCircle*4 + marginXCircle*4 );
        draw.chord( ( x, y+cy, x+widthCircle, y+heightCircle+cy ), 0, 360, fill=0 ) if el['scan'] == 1 else draw.arc( ( x, y+cy, x+widthCircle, y+heightCircle+cy ), 0, 360, fill=0 )

        x += widthCircle + marginXCircle;
        draw.chord( ( x, y+cy, x+widthCircle, y+heightCircle+cy ), 0, 360, fill=0 ) if el['associate'] == 1 else  draw.arc( ( x, y+cy, x+widthCircle, y+heightCircle+cy ), 0, 360, fill=0 )

        x += widthCircle + marginXCircle;
        draw.chord( ( x, y+cy, x+widthCircle, y+heightCircle+cy ), 0, 360, fill=0 ) if el['gateway'] == 1 else  draw.arc( ( x, y+cy, x+widthCircle, y+heightCircle+cy ), 0, 360, fill=0 )

        x += widthCircle + marginXCircle;
        draw.chord( ( x, y+cy, x+widthCircle, y+heightCircle+cy ), 0, 360, fill=0 ) if el['internet'] == 1 else  draw.arc( ( x, y+cy, x+widthCircle, y+heightCircle+cy ), 0, 360, fill=0 )

        y += heightText + marginYText

      _now = datetime.now()
      draw.text( ( marginXBorder, HEIGHT-marginFooter-heightFooter ), "Last update: " + _now.strftime("%m/%d/%y, %H:%M:%S") + " ", font = font12, fill = 0 )

      epd.display( epd.getbuffer( vImage ) )
      log.info( 'End drawing' )
      epd.sleep()

    except:
      log.error( 'traceback.format_exc():\n%s'.format( traceback.format_exc() ) )

    return

# eof

