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

import _useDvbCssUninstalled  # Enable to run when dvbcss not yet installed ... @UnusedImport

import dvbcss.monotonic_time as time

from dvbcss.clock import ClockBase, SysClock, CorrelatedClock, TunableClock, NoCommonClock, RangeCorrelatedClock

from mock_time import MockTime
from mock_dependent import MockDependent



class Test_SysClock(unittest.TestCase):

    def setUp(self):
        self.mockTime = MockTime()
        self.mockTime.install()

    def tearDown(self):
        self.mockTime.uninstall()

    def test_ticks(self):
        mockTime = self.mockTime

        sysClock = SysClock()
        
        mockTime.timeNow = 1234.5678
        self.assertAlmostEqual(sysClock.ticks, 1234.5678*1000000, places=5)

        mockTime.timeNow = 19445.325
        self.assertAlmostEqual(sysClock.ticks, 19445.325*1000000, places=5)

    def test_tickRate(self):
        sysClock = SysClock()
        self.assertEqual(sysClock.tickRate, 1000000)
        
    def test_calcWhen(self):
        sysClock = SysClock()
        self.assertAlmostEqual(sysClock.calcWhen(91248752), 91248752/1000000.0, places=5)

    def test_toParentTicks(self):
        sysClock = SysClock()
        self.assertRaises(StopIteration, lambda : sysClock.toParentTicks(10))

    def test_fromParentTicks(self):
        sysClock = SysClock()
        self.assertRaises(StopIteration, lambda : sysClock.fromParentTicks(10))

    def test_getParent(self):
        sysClock = SysClock()
        self.assertEqual(sysClock.getParent(), None)

class Test_ClockBase(unittest.TestCase):
    
    def test_dependents(self):
        b = ClockBase()
        d1 = MockDependent()
        d2 = MockDependent()
        b.bind(d1)
        b.bind(d2)
        b.notify(None)
        d1.assertNotificationsEqual([b])
        d2.assertNotificationsEqual([b])
        
        b.unbind(d1)
        b.notify(None)
        d2.assertNotificationsEqual([b])
        d1.assertNotificationsEqual([])
        
        b.unbind(d2)
        b.notify(None)
        d1.assertNotificationsEqual([])
        d2.assertNotificationsEqual([])
        
    def test_readSpeed(self):
        b = ClockBase()
        self.assertEquals(b.speed, 1.0, "Speed is 1.0")
        
        
class Test_CorrelatedClock(unittest.TestCase):
    
    def setUp(self):
        self.mockTime = MockTime()
        self.mockTime.install()

    def tearDown(self):
        self.mockTime.uninstall()

    def test_correlationAndFreqPropertiesInitialised(self):
        b = SysClock()
        c = CorrelatedClock(b, 1000, correlation=(0,300))
        self.assertEqual(c.correlation, (0,300))
        self.assertEqual(c.tickRate, 1000)
        
    
    def test_ticking(self):
        mockTime = self.mockTime

        mockTime.timeNow = 5020.8
        
        b = SysClock()
        c = CorrelatedClock(b, 1000, correlation=(0,300))
        self.assertAlmostEqual(c.ticks, 5020.8*1000 + 300, places=5)
        
        mockTime.timeNow += 22.7
        self.assertAlmostEqual(c.ticks, (5020.8+22.7)*1000 + 300, places=5)
        
    def test_changeCorrelation(self):
        mockTime = self.mockTime

        mockTime.timeNow = 5020.8
        
        b = SysClock()
        c = CorrelatedClock(b, 1000, correlation=(0,300))
        self.assertAlmostEqual(c.ticks, 5020.8*1000 + 300, places=5)
        
        c.correlation = (50000,320)
        self.assertEqual(c.correlation, (50000,320))
        self.assertAlmostEqual(c.ticks, (int(5020.8*1000000) - 50000) / 1000 + 320, places=5)
        
    def test_changeCorrelationNotifies(self):
        """Check a change to the correlation propagates notifications to dependents of this clock"""
        b = SysClock()
        c = CorrelatedClock(b, 1000, correlation=(0,300))
        cc = CorrelatedClock(c, 50)
        
        d1 = MockDependent()
        d2 = MockDependent()
        d3 = MockDependent()
        
        b.bind(d1)
        c.bind(d2)
        cc.bind(d3)
        
        c.correlation = (50,20)
        
        d1.assertNotNotified()
        d2.assertNotificationsEqual([c])
        d3.assertNotificationsEqual([cc])
        
    def test_changeSpeedeNotifies(self):
        """Check a change to the correlation propagates notifications to dependents of this clock"""
        b = SysClock()
        c = CorrelatedClock(b, 1000, correlation=(0,300))
        cc = CorrelatedClock(c, 50)
        
        d1 = MockDependent()
        d2 = MockDependent()
        d3 = MockDependent()
        
        b.bind(d1)
        c.bind(d2)
        cc.bind(d3)
        
        c.speed = 0.5
        
        d1.assertNotNotified()
        d2.assertNotificationsEqual([c])
        d3.assertNotificationsEqual([cc])
        
    def test_changeFreq(self):
        mockTime = self.mockTime

        mockTime.timeNow = 5020.8
        
        b = SysClock()
        c = CorrelatedClock(b, 1000, correlation=(50,300))
        self.assertAlmostEqual(c.ticks, (5020.8*1000000 - 50)/(1000000/1000) + 300, places=5)
        
        self.assertEqual(c.tickRate, 1000)
        c.tickRate = 500
        self.assertEqual(c.tickRate, 500)
        self.assertAlmostEqual(c.ticks, (5020.8*1000000 - 50)/(1000000/500) + 300, places=5)
        
    def test_changeFreqNotifies(self):
        mockTime = self.mockTime

        mockTime.timeNow = 5020.8
        
        b = SysClock()
        c = CorrelatedClock(b, 1000, correlation=(50,300))
        cc = CorrelatedClock(c, 50)
        
        d1 = MockDependent()
        d2 = MockDependent()
        d3 = MockDependent()
        
        b.bind(d1)
        c.bind(d2)
        cc.bind(d3)
        
        c.tickRate = 500
        
        d1.assertNotNotified()
        d2.assertNotificationsEqual([c])
        d3.assertNotificationsEqual([cc])
      
    def test_rebase(self):
        b = SysClock(tickRate=1000)
        c = CorrelatedClock(b, 1000, correlation=(50,300))
        c.rebaseCorrelationAtTicks(400)
        self.assertEquals(c.correlation, (150,400))
      
    def test_toParentTicks(self):
        mockTime = self.mockTime

        mockTime.timeNow = 1000.0
        
        b = SysClock(tickRate=2000000)
        c = CorrelatedClock(b, 1000, correlation=(50,300))
        self.assertAlmostEqual(c.toParentTicks(400), 50 + (400-300)*2000, places=5 )
        
    def test_fromParentTicks(self):
        mockTime = self.mockTime

        mockTime.timeNow = 1000.0
        
        b = SysClock(tickRate=2000000)
        c = CorrelatedClock(b, 1000, correlation=(50,300))
        self.assertAlmostEqual(c.fromParentTicks(50 + (400-300)*2000), 400, places=5 )
      
    def test_getParent(self):
        b = SysClock()
        c = CorrelatedClock(b, 1000, correlation=(50,300))
        self.assertEqual(c.getParent(), b)


class Test_RangeCorrelatedClock(unittest.TestCase):
    
    def setUp(self):
        self.mockTime = MockTime()
        self.mockTime.install()

    def tearDown(self):
        self.mockTime.uninstall()

    def test_rangeConversion(self):
        mockTime=MockTime()
        mockTime.install()
        
        mockTime.timeNow = 0.0
        b = SysClock(tickRate=1000)
        c = RangeCorrelatedClock(b, 1000, correlation1=(100,1000), correlation2=(200,1110))
        
        mockTime.timeNow = b.calcWhen(100)
        self.assertEqual(c.ticks, 1000)
       
        mockTime.timeNow = b.calcWhen(200)
        self.assertEqual(c.ticks, 1110)

        mockTime.timeNow = b.calcWhen(150)
        self.assertEqual(c.ticks, 1055)
        
      
class Test_TunableClock(unittest.TestCase):
    
    def setUp(self):
        self.mockTime = MockTime()
        self.mockTime.install()

    def tearDown(self):
        self.mockTime.uninstall()

    def test_tickRateAndTicksInitialised(self):
        mockTime = self.mockTime
        
        mockTime.timeNow = 5020.8
        
        b = SysClock()
        c = TunableClock(b, tickRate=1000, ticks=5)
        self.assertEqual(c.ticks, 5)
        self.assertEqual(c.tickRate, 1000)
        self.assertEqual(c.speed, 1.0)
        
    def test_ticking(self):
        mockTime = self.mockTime
        
        mockTime.timeNow = 5020.8
        
        b = SysClock()
        c = TunableClock(b, tickRate=1000, ticks=5)

        mockTime.timeNow += 100.2
        self.assertEqual(c.ticks, 100.2*1000 + 5)
        
    def test_slewFromMomentApplied(self):
        mockTime = self.mockTime
        
        mockTime.timeNow = 5020.8
        
        b = SysClock()
        c = TunableClock(b, tickRate=1000, ticks=5)

        mockTime.timeNow += 100.2
        self.assertEqual(c.ticks, 100.2*1000 + 5)
        
        c.slew = 100
        self.assertEqual(c.ticks, 100.2*1000 + 5)
        self.assertAlmostEqual(c.slew, 100, places=8)
        
        mockTime.timeNow += 10
        self.assertEqual(c.ticks, 100.2*1000 + 5 + 10*1100)

    def test_adjustTicks(self):
        mockTime = self.mockTime
        
        mockTime.timeNow = 5020.8
        
        b = SysClock()
        c = TunableClock(b, tickRate=1000, ticks=5)

        mockTime.timeNow += 100.2
        self.assertEqual(c.ticks, 100.2*1000 + 5)
        
        c.adjustTicks(28)
        self.assertEqual(c.ticks, 100.2*1000 + 5 + 28)
        
    def test_slewNotifiesDependents(self):
        mockTime = self.mockTime
        
        mockTime.timeNow = 5020.8
        
        b = SysClock()
        c = TunableClock(b, tickRate=1000, ticks=5)
        cc = TunableClock(c, tickRate=100)
        
        d1 = MockDependent()
        d2 = MockDependent()
        d3 = MockDependent()
        
        b.bind(d1)
        c.bind(d2)
        cc.bind(d3)

        d1.assertNotNotified()            
        d2.assertNotNotified()            
        d3.assertNotNotified()            
        
        c.slew = 100
        
        d1.assertNotNotified()            
        d2.assertNotificationsEqual([c])            
        d3.assertNotificationsEqual([cc])            

    def test_toParentTicks(self):
        mockTime = self.mockTime
        
        mockTime.timeNow = 5020.8
        
        b = SysClock(tickRate=1000000)
        c = TunableClock(b, tickRate=1000, ticks=5)
        c.slew=50
        
        self.assertAlmostEqual(c.toParentTicks(5+1000*50), b.ticks + 1000000*50.0/1.050, delta=1)

    def test_fromParentTicks(self):
        mockTime = self.mockTime
        
        mockTime.timeNow = 5020.8
        
        b = SysClock(tickRate=1000000)
        c = TunableClock(b, tickRate=1000, ticks=5)
        c.slew=50
        
        self.assertAlmostEqual(c.fromParentTicks(b.ticks + 1000000*50.0/1.050), 5+1000*50, places=5)

    def test_getParent(self):
        b = SysClock()
        c = TunableClock(b, tickRate=1000, ticks=5)
        self.assertEqual(c.getParent(), b)


class Test_HierarchyTickConversions(unittest.TestCase):
    """\
    Tests for the toOtherClockTicks function
    """
    
    def setUp(self):
        self.mockTime = MockTime()
        self.mockTime.install()

    def tearDown(self):
        self.mockTime.uninstall()

    def test_noCommonAncestor(self):
        a = SysClock()
        b = SysClock()
        a1 = CorrelatedClock(a, tickRate=1000, correlation=(0,0))
        b1 = CorrelatedClock(b, tickRate=1000, correlation=(0,0))
        a2 = CorrelatedClock(a1, tickRate=1000, correlation=(0,0))
        b2 = CorrelatedClock(b1, tickRate=1000, correlation=(0,0))
        
        self.assertRaises(NoCommonClock, lambda:a.toOtherClockTicks(b, 5))
        self.assertRaises(NoCommonClock, lambda:a.toOtherClockTicks(b1, 5))
        self.assertRaises(NoCommonClock, lambda:a.toOtherClockTicks(b2, 5))

        self.assertRaises(NoCommonClock, lambda:a1.toOtherClockTicks(b, 5))
        self.assertRaises(NoCommonClock, lambda:a1.toOtherClockTicks(b1, 5))
        self.assertRaises(NoCommonClock, lambda:a1.toOtherClockTicks(b2, 5))
        
        self.assertRaises(NoCommonClock, lambda:a2.toOtherClockTicks(b, 5))
        self.assertRaises(NoCommonClock, lambda:a2.toOtherClockTicks(b1, 5))
        self.assertRaises(NoCommonClock, lambda:a2.toOtherClockTicks(b2, 5))
        
        self.assertRaises(NoCommonClock, lambda:b.toOtherClockTicks(a, 5))
        self.assertRaises(NoCommonClock, lambda:b.toOtherClockTicks(a1, 5))
        self.assertRaises(NoCommonClock, lambda:b.toOtherClockTicks(a2, 5))

        self.assertRaises(NoCommonClock, lambda:b1.toOtherClockTicks(a, 5))
        self.assertRaises(NoCommonClock, lambda:b1.toOtherClockTicks(a1, 5))
        self.assertRaises(NoCommonClock, lambda:b1.toOtherClockTicks(a2, 5))
        
        self.assertRaises(NoCommonClock, lambda:b2.toOtherClockTicks(a, 5))
        self.assertRaises(NoCommonClock, lambda:b2.toOtherClockTicks(a1, 5))
        self.assertRaises(NoCommonClock, lambda:b2.toOtherClockTicks(a2, 5))
        
    def test_immediateParent(self):
        a = SysClock(tickRate=1000000)
        a1 = CorrelatedClock(a, tickRate=100, correlation=(50,0))
        a2 = CorrelatedClock(a1, tickRate=78, correlation=(28,999))
        self.assertEquals(a1.toOtherClockTicks(a, 500), a1.toParentTicks(500)) 
        self.assertEquals(a2.toOtherClockTicks(a1, 500), a2.toParentTicks(500)) 
        
    def test_distantParent(self):
        a = SysClock(tickRate=1000000)
        a1 = CorrelatedClock(a, tickRate=100, correlation=(50,0))
        a2 = CorrelatedClock(a1, tickRate=78, correlation=(28,999))
        self.assertEquals(a2.toOtherClockTicks(a, 500), a1.toParentTicks(a2.toParentTicks(500))) 

    def test_distantParentMidHierarchy(self):
        a = SysClock(tickRate=1000000)
        a1 = CorrelatedClock(a, tickRate=100, correlation=(50,0))
        a2 = CorrelatedClock(a1, tickRate=78, correlation=(28,999))
        a3 = CorrelatedClock(a2, tickRate=178, correlation=(5,1003))
        a4 = CorrelatedClock(a3, tickRate=28, correlation=(17,9))
        self.assertEquals(a3.toOtherClockTicks(a1, 500), a2.toParentTicks(a3.toParentTicks(500)))

    def test_differentBranches(self):
        a = SysClock(tickRate=1000000)
        a1 = CorrelatedClock(a, tickRate=100, correlation=(50,0))
        a2 = CorrelatedClock(a1, tickRate=78, correlation=(28,999))
        a3 = CorrelatedClock(a2, tickRate=178, correlation=(5,1003))
        a4 = CorrelatedClock(a3, tickRate=28, correlation=(17,9))
        b3 = CorrelatedClock(a2, tickRate=1000, correlation=(10,20))
        b4 = CorrelatedClock(b3, tickRate=2000, correlation=(15,90))
        
        v = a4.toParentTicks(500)
        v = a3.toParentTicks(v)
        v = b3.fromParentTicks(v)
        v = b4.fromParentTicks(v)
        
        self.assertEquals(a4.toOtherClockTicks(b4, 500), v)

    def test_speedChangePropagates(self):
        mockTime = self.mockTime
        
        mockTime.timeNow = 5
        
        a = SysClock(tickRate=1000)
        a1 = CorrelatedClock(a, tickRate=1000, correlation=(50,0))
        a2 = CorrelatedClock(a1, tickRate=100, correlation=(28,999))
        a3 = CorrelatedClock(a2, tickRate=50, correlation=(5,1003))
        a4 = CorrelatedClock(a3, tickRate=25, correlation=(1000,9))
        b3 = CorrelatedClock(a2, tickRate=1000, correlation=(500,20))
        b4 = CorrelatedClock(b3, tickRate=2000, correlation=(15,90))
        
        at1, a1t1, a2t1, a3t1, a4t1, b3t1, b4t1 = [x.ticks for x in [a,a1,a2,a3,a4,b3,b4]]
        a3.speed = 0
        mockTime.timeNow = 6 # advance time 1 second
        
        at2, a1t2, a2t2, a3t2, a4t2, b3t2, b4t2 = [x.ticks for x in [a,a1,a2,a3,a4,b3,b4]]
        
        self.assertEquals(at2,  at1 + 1000)  # a  still advances
        self.assertEquals(a1t2, a1t1 + 1000) # a1 still advances
        self.assertEquals(a2t2, a2t1 + 100)  # a2 still advances
        self.assertEquals(a3t2, 1003)        # a3 is speed zero, is now at the correlation point
        self.assertEquals(a4t2, 10.5)        # a4 is speed zero, a3.ticks is 3 ticks from correlation point for a4, translating to 1.5 ticks from a4 correlation point at its tickRate
        self.assertEquals(b3t2, b3t1 + 1000) # b3 still advances
        self.assertEquals(b4t2, b4t1 + 2000) # b4 is paused
        
if __name__ == "__main__":
    unittest.main()
