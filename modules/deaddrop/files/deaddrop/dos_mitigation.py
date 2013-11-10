"""
Class that detects dos attacks and turns on captchas
"""

import datetime
import math
import scipy.stats

class dos_mitigation(object):
    time = datetime.datetime.utcnow()
    map = {}
    
    def addEvent(self, eventName):
        if map.__contains__(eventName):
            minute = map[eventName]
            if minute.__contains__(self.time.strftime("%Y:%m:%d:%H:%M")):
                minute[self.time.strftime("%Y:%m:%d:%H:%M")] += 1
            else:
                minute[self.time.strftime("%Y:%m:%d:%H:%M")] = 1
        else:
            minute[self.time.strftime("%Y:%m:%d:%H:%M")] = 1
            map[eventName] = minute
            
            
    def doYourShit(self):
        for event, minute_dict in event.iteritems():
            minute_list = list()
            
            for minute, count in minute_dict.iteritems():
                temp = [minute, count]
                minute_list.append(temp)
            
            # sorts by minute
            minute_list = sorted(minute_list, key=lambda pair: pair[0])
            
            now = minute_list.pop()
            n = minute_list.__len__()
            past = reduce(lambda x, y: x+y, minute_list)
            mean = past / n
            stdDev = math.sqrt(reduce(lambda x, y: x+y, map(lambda x: x*x, minute_list)) / n)
            today_prob = scipy.stats.norm(mean, stdDev).cdf(now)
            
            if today_prob > 0.99:
                self.alert()
        
        # add sleep t = 10 or whatever
                    
        self.time = datetime.datetime.utcnow()
        self.dumpOldValues()
            
    def dumpOldValues(self):
        for event in map.itervalues():
            for minute_string in event.iterkeys():
                arr = minute_string.split(':')
                minute = datetime.datetime(arr[0], arr[1], arr[2], arr[3], arr[4])
                if int((self.time - minute).total_seconds) > 30*60:
                    map[event].remove(minute_string)
                    
    def alert(self):
        
                
                