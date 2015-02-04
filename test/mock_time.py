#!/usr/bin/env python
#
# Copyright 2015 British Broadcasting Corporation
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import dvbcss.monotonic_time as time

import threading

class MockTime(object):
    """\
    Object that provides mocks for time.time() and time.sleep()
    
    Use :func:`install` and :func:`uninstall` to plug the mock in.
    """

    def __init__(self):
        super(MockTime,self).__init__()
        self._timeNow = 0
        self.doctoredTimeModule=None
        self.oldTimeFunc = None
        self.oldSleepFunc = None
        self.sleepEvents = []
        
    @property
    def timeNow(self):
        return self._timeNow
        
    @timeNow.setter
    def timeNow(self, newValue):
        self._timeNow = newValue
        
        # go through list of pending sleeps and wake any up that need to be,
        # deleting them on the way.
        i=0
        while i<len(self.sleepEvents):
            wakeUpTime, event = self.sleepEvents[i]
            if self._timeNow >= wakeUpTime:
                event.set()
                del self.sleepEvents[i]
            else:
                i=i+1
    
    def install(self, module=time):
        """\
        Plugs the mock in (or does nothing if already plugged into something.
        
        :param module: The "time" module to have its `time()` and `sleep()` functions replaced. Defaults to the dvbcss.monotonic_time module.
        """
        if self.doctoredTimeModule is None:
        
            self.doctoredTimeModule = module
            self.oldTimeFunc = getattr(module,"time")
            
            setattr(module,"time", self.mockTimeFunc)
            self.oldSleepFunc = getattr(module,"sleep")
            
            setattr(module,"sleep", self.mockSleepFunc)
        else:
            raise Exception("MockTime is already plugged in. Cannot be plugged in in two places.")


    def mockTimeFunc(self):
        return self.timeNow
        
    def mockSleepFunc(self, durationSecs):
        wakeUpTime = self.timeNow + durationSecs
        event = threading.Event()
        event.clear()
        self.sleepEvents.append((wakeUpTime, event))
        event.wait()
        

    def uninstall(self):
        """\
        Unplugs the mock (or does nothing if already unplugged.
        """
        if self.doctoredTimeModule is not None:
        
            setattr(self.doctoredTimeModule,"time", self.oldTimeFunc)
            self.oldTimeFunc=None
            
            setattr(self.doctoredTimeModule,"sleep", self.oldSleepFunc)
            self.oldSleepFunc=None
            
            self.doctoredTimeModule = None
        else:
            raise Exception("MockTime is not already plugged in. Cannot be unplugged.")
            
