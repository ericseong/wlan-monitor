#!/usr/bin/python2
# -*- coding:utf-8 -*-

# Usage: wlan_monitor.py --configfile config_file.json --toaddrs email_addrs.json --interval interval
# config_file.json - json format file with netif and arrays of SSID and password
# email_addrs.json - json format file with email addresses. The report will be sent to these email addresses
# interval - monitoring interval in seconds

import wlan_logger
log = wlan_logger.logger.get()

import os
import sys
import time
import argparse
import subprocess
import json
import socket
from datetime import datetime
import traceback
import wlan_reporter

class WlanMonitor(object):

  def __init__( self, args ):
    self._netif = ""
    self._aps = []
    self._toaddrs = []
    self._timeout = 30
    self._interval = 1
    self._epd_reporter = None
    self._email_reporter = None

    if True == self._setupEnv( args.configfile, args.toaddrs, args.interval ):
      return True 

    self._epd_reporter = \
      wlan_reporter.EpdReporter( self._getTimeout() )
    self._email_reporter = \
      wlan_reporter.EmailReporter( self._getToAddrs(), self._getTimeout() ) 
    
    return
  
  def _getNetIf( self ):
    return self._netif

  def _getAPs( self ):
    return self._aps

  def _getToAddrs( self ):
    return self._toaddrs

  def _getTimeout( self ):
    return self._timeout

  def _getInterval( self ):
    return self._interval

  def _getEpdReporter( self ):
    return self._epd_reporter

  def _getEmailReporter( self ):
    return self._email_reporter

  def _setupEnv( self, config, toaddrs, interval ):
    '''
    reads file and set up environment - netif and list of aps
    arg - config - config file 
    toaddrs - email recipients
    return - False if success, True otherwise 
    '''

    self._interval = interval

    try:
      with open( config ) as infile1:
        _dict = json.load( infile1 )
      self._netif = _dict['netif']
      self._aps = _dict['aps']
      log.debug( json.dumps(_dict) )

      with open( toaddrs ) as infile2: 
        _arr = json.load( infile2 )
      self._toaddrs = _arr 
      log.debug( json.dumps(_arr) )

    except:
      log.error( 'traceback.format_exc():\n%s' % traceback.format_exc() )

    return False

  def _forceScan( self ):
    '''
    force wifi to rescan
    '''
    os.system( 'wifiap_evaluate2.sh force_scan' + ' ' + self._getNetIf() )
    return

  def _evaluateOne( self, ap ):
    '''
    evaluate a single AP
    arg - list of ap
    return - evaluated status 
    '''
    try:
      _res={}
      _ssid = ap['ssid']; _passwd = ap['passwd']
      _res['ssid'] = _ssid
      _res['passwd'] = _passwd
      _res['scan'] = _res['associate'] = _res['gateway'] = _res['internet'] = _res['signal'] = 0

      # refresh netif - workaround to avoid reg domain related bug in brcmfmac
      os.system( 'wifiap_evaluate2.sh refresh_netif' + ' ' + self._getNetIf() )
      time.sleep(1)
        
      # try scan
      if 0 == os.system( 'wifiap_evaluate2.sh scan' + ' ' + self._getNetIf() + ' ' + _ssid ):
        _res['scan'] = 1
      else:
        return _res

      # try associate
      if 0 == os.system( 'wifiap_evaluate2.sh associate' + ' ' + self._getNetIf() + ' ' + _ssid + ' ' + _passwd ):
        _res['associate'] = 1
      else:
        return _res

      # try connect to gateway
      if 0 == os.system( 'wifiap_evaluate2.sh connect' + ' ' + self._getNetIf() ):
        _res['gateway'] = 1
      else:
        return _res

      # try connect to internet
      if 0 == os.system( 'wifiap_evaluate2.sh connect_internet' + ' ' + self._getNetIf() ):
        _res['internet'] = 1
        _res['signal'] = subprocess.check_output( "iw dev wlan0 link | grep signal | awk  '{print $2 " " $3}'", shell = True )[:-1]
      else:
        return _res

    except:
      log.error( 'traceback.format_exc():\n%s' % traceback.format_exc() )

    return _res

  def _evaluateAll( self, aps ):
    _res = []

    for el in aps:
      _res.append( self._evaluateOne( el ) )
    
    return _res

  def _connectInternetWithStatus( self, status ):
    _ap = {};
    try:
      _status = sorted( status, key = lambda i: i['signal'], reverse=False )
      for el in _status:
        if el['internet'] == 1:
          _ap['ssid'] = el['ssid']; _ap['passwd'] = el['passwd']
          if 1 == self._evaluateOne(_ap)['internet']:
            log.debug( " {}: connected AP: {} ".format( sys._getframe().f_code.co_name, _ap['ssid'] ) )
            return True 

    except:
      log.error( 'traceback.format_exc():\n%s' % traceback.format_exc() )

    return False 

  def run( self ):

    _loop_count = 0
    _start = time.time()
    _statuses = []
    while True:
      _status = []

      log.info( 'loop_count= {}'.format( _loop_count ) )
      _loop_count += 1
      with open( '/var/opt/wlanmonitor_tick', 'w' ) as _f:
        _f.write( "{}".format( int( time.time() ) ) )

      '''
      Evaluate all APs 
      '''
      _status = self._evaluateAll( self._getAPs() )
      log.info( "status is {}".format( _status ) )

      '''
      Update display
      '''
      if self._getEpdReporter().isUpdated( _status ):
        self._getEpdReporter().send( _status )

      '''
      Send email 
      '''
      for _el in _status:
        _now = datetime.now().strftime("%H:%M:%S"); _el['time'] = _now;
        _statuses.insert( 0, _el )
      log.debug( "_statuses is {}".format( _statuses ) )

      _end = time.time(); _elapsed = _end - _start;
      _email_freq = self._getEmailReporter().getEmailFreq()
      if _elapsed > _email_freq:
        _start = time.time() 
        if self._connectInternetWithStatus( _status ): 
          log.debug( 'Now, connected to internet.' )
          
          self._getEmailReporter().send( _statuses, None )
          time.sleep( 30 )
        else:
          log.debug( "Can't connect to internet." )

        _statuses = []

      time.sleep( self._getInterval() )
      #os.system( 'free -h' )

    return

def main( argv ):
  '''
  arg1 - config file with netif and the list of ssid
  arg2 - interval in seconds 
  arg3 - toaddrs
  '''
  log.info( "{} starts..".format( argv[0] ) )
  _parser = argparse.ArgumentParser( description='wlan monitor' )
  _parser.add_argument( '-c', '--configfile', type=str, required=True, help='wlan config file' )
  _parser.add_argument( '-i', '--interval', type=int, default=60, help='interval in seconds' )
  _parser.add_argument( '-t', '--toaddrs', type=str, required=True, help='email recipients' )

  _args = _parser.parse_args()

  # give sometime before start.
  time.sleep( 30 )

  # When we start/stop the service, there could be a case when mac driver or netif or wpa_supplicant is not activated. 
  os.system( 'wlanmonitor_startup2.sh' )
  log.info( "wlanmonitor_startup2.sh" )

  # now, run
  _wlan_mon = WlanMonitor( _args )
  if True == _wlan_mon.run():
    return 1
    
  return 0 

if __name__ == "__main__":

  main( sys.argv )

# eof
 
