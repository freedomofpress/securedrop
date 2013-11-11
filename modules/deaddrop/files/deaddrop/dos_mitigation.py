"""
Class that detects dos attacks and turns on captchas
"""

import datetime
import math
import scipy.stats

class dos_mitigation(object):
    underAttack = False
    time = datetime.datetime.utcnow()
    event_counts = dict()
    deviant_events = dict()

    #time.sleep(30*60)    
    #while True:
    #    detect()
    #    time.sleep(10)
    
    def __init__(self, inputLog, outputLog):
        self.input = inputLog
        self.output = outputLog
    
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
        
        
        
        
        