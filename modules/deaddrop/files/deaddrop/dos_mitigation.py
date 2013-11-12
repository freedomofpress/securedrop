"""
Class that detects dos attacks and performs mitigation procedure such as captchas
"""


# external imports
import argparse
import datetime
import math
import scipy.stats
import os
import sys
import string, sys, os, syslog, time



class DOS_Mitigation(object):

    def __init__(self, inputLog, outputLog):
        self.underAttack    = False
        self.time           = datetime.datetime.utcnow()
        self.event_counts   = dict()
        self.deviant_events = dict()

        self.input          = inputLog
        self.output         = outputLog

    def addEvent(self, eventName, eventTime):
        if self.event_counts.__contains__(eventName):
            minute = self.event_counts[eventName]
            if minute.__contains__(eventTime):
                minute[eventTime] += 1
            else:
                minute[eventTime] = 1
        else:
            minute[eventTime] = 1
            self.event_counts[eventName] = minute
            
    def detect(self):
        for event, minute_dict in self.event_counts.iteritems():
            minute_list = list()
            
            for minute, count in minute_dict.iteritems():
                temp = [minute, count]
                minute_list.append(temp)
            
            # sorts by minute
            minute_list = sorted(filter(self.excludeDeviantTimes(minute[0]), minute_list), key=lambda pair: pair[0])
            
            now = minute_list.pop()
            n = minute_list.__len__()
            past = reduce(lambda x, y: x+y, minute_list)
            mean = past / n
            stdDev = math.sqrt(reduce(lambda x, y: x+y, map(lambda x: x*x, minute_list)) / n)
            today_prob = scipy.stats.norm(mean, stdDev).cdf(now[0])
            
            if today_prob > 0.99:
                self.underAttack = True
                self.deviant_events[event] = now[0]
                self.alert(event, now[0], now[1])
        
        # add sleep t = 10 or whatever
                    
        self.time = datetime.datetime.utcnow()

        if not self.underAttack:
            self.dumpOldValues()
            
    def dumpOldValues(self):        
        # removes old minutes from event_counts
        for event in self.event_counts.itervalues():
            for minute_string in event.iterkeys():
                arr = minute_string.split(':')
                minute = datetime.datetime(arr[0], arr[1], arr[2], arr[3], arr[4])
                if int((self.time - minute).total_seconds) > 30*60:
                    self.event_counts[event].remove(minute_string)
        
        # removes empty events from event_counts
        for event, map in self.event_counts.iteritems():
            if len(map) == 0:
                self.event_counts.remove(event)
                
        # removes old minutes from deviant_events
        for event, minute in self.deviant_events.iteritems():
            arr = minute_string.split(':')
            minute = datetime.datetime(arr[0], arr[1], arr[2], arr[3], arr[4])
            if int((self.time - minute).total_seconds) > 30*60:
                self.deviant_events[event].remove(minute_string)
        
        # removes empty events from deviant_events
        for event in self.deviant_events.iterkeys():
            if len(self.deviant_events[event]) == 0:
                self.deviant_events.remove(event)
                    
    def alert(self, eventName, deviantValue, deviantTime):
        # TODO write to log
        break
        
    def excludeDeviantTimes(self, minute):
        if self.deviant_events.has_key(minute):
            return False
        else:
            return True


# here we use Moxie's LogFile class
#
# Copyright (c) 2009 Moxie Marlinspike
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307
# USA

class LogFile:

    def __init__(self, file):
        self.file = file        

    def checkForFileRotate(self, fd):
        freshFile = open(self.file)
            
        if (os.path.sameopenfile(freshFile.fileno(), fd.fileno())):
            freshFile.close()
            return fd
        else:
            fd.close()
            return freshFile

    def tail(self):
        fd = open(self.file)
        fd.seek(0, os.SEEK_END)
        
        while True:
            fd    = self.checkForFileRotate(fd)
            where = fd.tell()
            line  = fd.readline()

            if not line:
                time.sleep(.25)
                fd.seek(where)
            else:
                yield line


"""Disk And Execution MONitor (Daemon)

Configurable daemon behaviors:

   1.) The current working directory set to the "/" directory.
   2.) The current file creation mode mask set to 0.
   3.) Close all open files (1024). 
   4.) Redirect standard I/O streams to "/dev/null".

A failed call to fork() now raises an exception.

References:
   1) Advanced Programming in the Unix Environment: W. Richard Stevens
   2) Unix Programming Frequently Asked Questions:
         http://www.erlenstar.demon.co.uk/unix/faq_toc.html
"""

def createDaemon():
   """This here is a modified version of Chad J. Schroeder's createDaemon()...
   Sampled from Moxie! https://github.com/moxie0/knockknock/blob/master/knockknock/daemonize.py
   Detach a process from the controlling terminal and run it in the
   background as a daemon.
   """

   UMASK   = 0
   WORKDIR = "/"
   MAXFD   = 1024

   # The standard I/O file descriptors are redirected to /dev/null by default.
   if (hasattr(os, "devnull")):
       REDIRECT_TO = os.devnull
   else:
       REDIRECT_TO = "/dev/null"

   try:
      pid = os.fork()
   except OSError, e:
      raise Exception, "%s [%d]" % (e.strerror, e.errno)

   if (pid == 0):        # The first child.
      os.setsid()

      try:
         pid = os.fork()        # Fork a second child.
      except OSError, e:
         raise Exception, "%s [%d]" % (e.strerror, e.errno)

      if (pid == 0):        # The second child.
         os.chdir(WORKDIR)
         os.umask(UMASK)
      else:
         os._exit(0)        # Exit parent (the first child) of the second child.
   else:
      os._exit(0)        # Exit parent of the first child.

   os.open(REDIRECT_TO, os.O_RDWR)        # standard input (0)
   os.dup2(0, 1)                        # standard output (1)
   os.dup2(0, 2)                        # standard error (2)

   return(0)


def getEventIdAndTime(line):
    # TODO: catch and throw exceptions?
    time, id = line.split()
    return (time, id)


def main():

    parser     = argparse.ArgumentParser()
    parser.add_argument("--event-log", dest='eventlog', help="SecureDrop DOS mitigation event log")
    args       = parser.parse_args()

    if args.eventlog is None:
        parser.print_help()
        return

    createDaemon()
    mitigation = DOS_Mitigation()

    log = LogFile(args.eventlog)

    for line in log.tail():
        try:
            event_time, event_id = getEventIdAndTime(line)
            event = (event_time, event_id)
            mitigation.addEvent(event)


if __name__ == '__main__':
    main()
        
