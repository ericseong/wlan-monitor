#!/usr/bin/python2
# -*- coding: utf-8 -*-

# We're not logging for this module itself!

from __future__ import absolute_import, division, unicode_literals, print_function

import logging, logging.handlers

from datetime import datetime
import os
import sys
import time
from os.path import expanduser

HOME_DIR = "/home/pi" 

class Logger(object):

  def __init__( self, app_name, log_level, enable_console, enable_syslog, enable_file ):
    self._app_name = app_name
    self._logger = logging.getLogger( app_name )
    self._logger.setLevel( log_level ) 
    self._formatter = logging.Formatter( '%(name)s - %(asctime)s - %(levelname)s - %(message)s' )

    if self._app_name != "":

      if enable_console:
        print( 'enable_console' )
        _ch = logging.StreamHandler()
        _ch.setLevel( log_level ) 
        _ch.setFormatter( self._formatter )
        self._logger.addHandler( _ch )
      
      if enable_syslog:
        print( 'enable_syslog' )
        _sh = logging.handlers.SysLogHandler( address='/dev/log' )
        _sh.setLevel( log_level )
        _sh.setFormatter( logging.Formatter( '%(name)s: %(message)s' ) )
        self._logger.addHandler( _sh )
      
      if enable_file:
        print( 'enable_file' )
        _fh = logging.FileHandler( HOME_DIR + '/work/wlan-monitor/log/wlan_monitor.log' ) 
        _fh.setLevel( log_level )
        _fh.setFormatter( self._formatter ) 
        self._logger.addHandler( _fh )

    else:
      print( "Logger() is not initialized." )

    return

  def get( self ):
    return self._logger

# release mode - only with logging to syslog
logger = Logger( "wlanmonitor", logging.INFO, False, True, False )

# debug mode - with logging to console, syslog, file 
#logger = Logger( "wlanmonitor", logging.DEBUG, True, True, True )

''' for test
log = logger.get()

def main( argv ):

  #logger = Logger( "wlanmonitor", logging.INFO, False, True, True )
  log = Logger( "wlanmonitor", logging.DEBUG, True, True, True ).get()
  if( log == None ):
    print( "Logger failed in initialization" )

  log.debug( 'Hi, this is debug message.' )
  log.info( 'Hi, this is info message.' )
  log.warning( 'Hi, this is warning message.' )
  log.critical( 'Hi, this is critical message.' )
  log.error( 'Hi, this is error message.' )

  return

if __name__ == "__main__":
  main( sys.argv )

'''

# eof

