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

import unittest

import _useDvbCssUninstalled

import dvbcss.monotonic_time as monotonic_time
import threading


class MockTime(object):
    """\
    Object that provides mocks for :func:`monotonic_time.time` and
    :func:`dvbcss.monotonic_time.sleep`
    
    Use :func:`install` and :func:`uninstall` to plug the mock in.
    
    It works by replacing the time() and sleep() function in the
    :mod:`dvbcss.monotonic_time` module (or alternative module that you specify
    when calling :func:`install`).
    It therefore will mock the monotonic_time module in any module that has
    already imported it, or that imports it in the future, with only one
    call to :func:`install`.
    """

    def __init__(self):
        super(MockTime,self).__init__()
        self._timeNow = 0
        self.doctoredTimeModule=None
        self.oldTimeFunc = None
        self.oldSleepFunc = None
        self.sleepEvents = []
        self._incrStep = 0
        
    @property
    def timeNow(self):
        """\
        Get/set this property to set the value that the mock time() function will return.
        
        If setting this property mean that the time has passed the point at which
        a call to the mocked :func:`sleep` function is due to wake (unblock)
        and return then this will take place.
        """
        # process any pending wakeups for this time
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
        
        t = self._timeNow
        
        # do auto increment (if enabled)
        if self._incrStep != 0:
            self._incrCountdown -= 1
            if self._incrCountdown == 0:
                self._incrCountdown = self._incrInterval
                self._timeNow += self._incrStep
                
        return t
        
    @timeNow.setter
    def timeNow(self, newValue):
        self._timeNow = newValue
        # trigger reading the time to cause any sleeps that need to be woken 
        # to be processed
        _ = self.timeNow
        
    def enableAutoIncrementBy(self, step, numReadsBetweenIncrements=1):
        self._incrStep = step
        self._incrInterval = numReadsBetweenIncrements
        self._incrCountdown = self._incrInterval
        
    def disableAutoIncrement(self):
        self._incrStep = 0
    
    def flush(self):
        """\
        Flushes any calls blocked on the mock :func:`sleep` function by causing
        them to all wake (unblock) and return.
        """
        while len(self.sleepEvents):
            wakeUpTime, event = self.sleepEvents[0]
            event.set()
            del self.sleepEvents[0]
    
    def install(self, module=monotonic_time):
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
        
        Also causes a :func:`flush` to happen.
        """
        if self.doctoredTimeModule is not None:
        
            self.flush()
        
            setattr(self.doctoredTimeModule,"time", self.oldTimeFunc)
            self.oldTimeFunc=None
            
            setattr(self.doctoredTimeModule,"sleep", self.oldSleepFunc)
            self.oldSleepFunc=None
            
            self.doctoredTimeModule = None
        else:
            raise Exception("MockTime is not already plugged in. Cannot be unplugged.")
            


class SleepThread(threading.Thread):
    def __init__(self, sleepArg):
        super(SleepThread,self).__init__()
        self.sleepArg = sleepArg
        self.daemon = True
    def run(self):
        monotonic_time.sleep(self.sleepArg)


class Test_mock_time(unittest.TestCase):
    """\
    Tests for the MockTime class.
    
    Turtles all the way down.
    """

    
    def testInstallUninstall(self):
        """\
        Check if the mock appears to replace (when installing) and
        restore (when uninstalling) the monotonic_module time() and sleep() functions.
        """
        import dvbcss.monotonic_time as monotonic_time
        
        oldTime = monotonic_time.time
        oldSleep = monotonic_time.sleep
        
        mockUnderTest = MockTime()

        self.assertEquals(oldTime, monotonic_time.time)
        self.assertEquals(oldSleep, monotonic_time.sleep)

        mockUnderTest.install(monotonic_time)
        try:
            self.assertNotEquals(oldTime, monotonic_time.time)
            self.assertNotEquals(oldSleep, monotonic_time.sleep)
        finally:
            mockUnderTest.uninstall()
        
        self.assertEquals(oldTime, monotonic_time.time)
        self.assertEquals(oldSleep, monotonic_time.sleep)
        
        
    def testTime(self):
        import dvbcss.monotonic_time as monotonic_time
    
        mockUnderTest = MockTime()
        mockUnderTest.install(monotonic_time)
        try:
            mockUnderTest.timeNow = 1234
            self.assertEquals(monotonic_time.time(), 1234)
            
            mockUnderTest.timeNow = -485.2701
            self.assertEquals(monotonic_time.time(), -485.2701)
        finally:
            mockUnderTest.uninstall()


    def testSleep(self):
        import dvbcss.monotonic_time as monotonic_time
    
        mockUnderTest = MockTime()
        mockUnderTest.install(monotonic_time)
        
        try:
            a = SleepThread(5.0)
            b = SleepThread(2.0)
            c = SleepThread(7.0)
            
            mockUnderTest.timeNow = 1000.0
            a.start()  # will happen at t > 1005
            
            self.assertTrue(a.isAlive())
            
            mockUnderTest.timeNow = 1001.0
            b.start()   # will happen at t >= 1003
            c.start()   # will happen at t >= 1008
            
            self.assertTrue(a.isAlive())
            self.assertTrue(b.isAlive())
            self.assertTrue(c.isAlive())

            mockUnderTest.timeNow = 1002.99
            self.assertTrue(a.isAlive())
            self.assertTrue(b.isAlive())
            self.assertTrue(c.isAlive())
             
            mockUnderTest.timeNow = 1003.1
            b.join(1.0)
            self.assertTrue(a.isAlive())
            self.assertFalse(b.isAlive())
            self.assertTrue(c.isAlive())
             
            mockUnderTest.timeNow = 1004.99
            self.assertTrue(a.isAlive())
            self.assertTrue(c.isAlive())

            mockUnderTest.timeNow = 1005.7
            a.join(1.0)
            self.assertFalse(a.isAlive())
            self.assertTrue(c.isAlive())
            
            mockUnderTest.timeNow = 1007.8
            self.assertTrue(c.isAlive())

            mockUnderTest.timeNow = 1008.0
            c.join(1.0)
            self.assertFalse(c.isAlive())

        finally:
            mockUnderTest.uninstall()


    def testSleepFlush(self):
        """\
        Check that sleeps that have not triggered are unblocked and return when
        the flush method is called.
        """
        import dvbcss.monotonic_time as monotonic_time
    
        mockUnderTest = MockTime()
        mockUnderTest.install(monotonic_time)
        
        try:
            a = SleepThread(5.0)
            b = SleepThread(2.0)
            c = SleepThread(7.0)
            
            mockUnderTest.timeNow = 1000.0
            a.start()  # will happen at t > 1005
            
            self.assertTrue(a.isAlive())
            
            mockUnderTest.timeNow = 1001.0
            b.start()   # will happen at t >= 1003
            c.start()   # will happen at t >= 1008
         
            self.assertTrue(a.isAlive())
            self.assertTrue(b.isAlive())
            self.assertTrue(c.isAlive())
            
            mockUnderTest.flush()
            a.join(1.0)         
            b.join(1.0)         
            c.join(1.0)     
            
            self.assertFalse(a.isAlive())    
            self.assertFalse(b.isAlive())    
            self.assertFalse(c.isAlive())
        finally:
            mockUnderTest.uninstall()

    def testSleepUninstallFlush(self):
        """\
        Check that sleeps that have not triggered are unblocked and return when
        the flush method is called.
        """
        import dvbcss.monotonic_time as monotonic_time
    
        mockUnderTest = MockTime()
        mockUnderTest.install(monotonic_time)
        
        try:
            a = SleepThread(5.0)
            b = SleepThread(2.0)
            c = SleepThread(7.0)
            
            mockUnderTest.timeNow = 1000.0
            a.start()  # will happen at t > 1005
            
            self.assertTrue(a.isAlive())
            
            mockUnderTest.timeNow = 1001.0
            b.start()   # will happen at t >= 1003
            c.start()   # will happen at t >= 1008
         
            self.assertTrue(a.isAlive())
            self.assertTrue(b.isAlive())
            self.assertTrue(c.isAlive())
            
        finally:
            mockUnderTest.uninstall()

        a.join(1.0)         
        b.join(1.0)         
        c.join(1.0)     
        
        self.assertFalse(a.isAlive())    
        self.assertFalse(b.isAlive())    
        self.assertFalse(c.isAlive())
        
    def testIncrInterval(self):
        """\
        Mock time can be auto incremented
        """
        import dvbcss.monotonic_time as monotonic_time
    
        mockUnderTest = MockTime()
        mockUnderTest.install(monotonic_time)
        
        try:
            mockUnderTest.timeNow = 5
            
            # no auto increment by Default
            for i in range(0,10000):
                self.assertEquals(5, monotonic_time.time())
                
            mockUnderTest.enableAutoIncrementBy(0.1, numReadsBetweenIncrements=5)
            for i in range(0,100):
                for j in range(0,5):
                    self.assertAlmostEquals(5 + i*0.1, monotonic_time.time(), delta=0.0001)
            
        finally:
            mockUnderTest.uninstall()

            
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
