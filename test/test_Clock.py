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
import math

import _useDvbCssUninstalled  # Enable to run when dvbcss not yet installed ... @UnusedImport

import dvbcss.monotonic_time as time

from dvbcss.clock import ClockBase, SysClock, CorrelatedClock, OffsetClock, TunableClock, NoCommonClock, RangeCorrelatedClock, Correlation

from mock_time import MockTime
from mock_dependent import MockDependent

class Test_SysClock(unittest.TestCase):

    def setUp(self):
        self.mockTime = MockTime()
        self.mockTime.install()

    def tearDown(self):
        self.mockTime.uninstall()

    def newSysClock(self, *args, **kwargs):
        self.mockTime.enableAutoIncrementBy(0.000001, numReadsBetweenIncrements=1)
        sysClock = SysClock(*args, **kwargs)
        self.mockTime.disableAutoIncrement()
        return sysClock

    def test_ticks(self):
        mockTime = self.mockTime

        sysClock = self.newSysClock()
        
        mockTime.timeNow = 1234.5678
        self.assertAlmostEqual(sysClock.ticks, 1234.5678*1000000, places=5)

        mockTime.timeNow = 19445.325
        self.assertAlmostEqual(sysClock.ticks, 19445.325*1000000, places=5)

    def test_tickRate(self):
        sysClock = self.newSysClock()
        self.assertEqual(sysClock.tickRate, 1000000)
        
    def test_calcWhen(self):
        sysClock = self.newSysClock()
        self.assertAlmostEqual(sysClock.calcWhen(91248752), 91248752/1000000.0, places=5)

    def test_toParentTicks(self):
        sysClock = self.newSysClock()
        self.assertRaises(StopIteration, lambda : sysClock.toParentTicks(10))

    def test_fromParentTicks(self):
        sysClock = self.newSysClock()
        self.assertRaises(StopIteration, lambda : sysClock.fromParentTicks(10))

    def test_getParent(self):
        sysClock = self.newSysClock()
        self.assertEqual(sysClock.getParent(), None)
        
    def test_available(self):
        sysClock = self.newSysClock()
        self.assertTrue(sysClock.isAvailable())
        
    def test_cannotChangeAvailability(self):
        sysClock = self.newSysClock()
        self.assertRaises(NotImplementedError, sysClock.setAvailability, True)
        self.assertRaises(NotImplementedError, sysClock.setAvailability, False)

    def test_getRootReturnsSelf(self):
        sysClock = self.newSysClock()
        self.assertEquals(sysClock, sysClock.getRoot())

    def test_ancestry(self):
        sysClock = self.newSysClock()
        self.assertEquals([sysClock], sysClock.getAncestry())

    def test_toFromRootTicks(self):
        sysClock = self.newSysClock()
        self.assertEquals(12345, sysClock.toRootTicks(12345))
        self.assertEquals(12345, sysClock.fromRootTicks(12345))
        
    def test_dispersion(self):
        """Dispersion should equal precision irrespective of time value"""
        sysClock = self.newSysClock(tickRate=1000000000)
        
        now = sysClock.ticks
        self.assertAlmostEquals(0.000001, sysClock.dispersionAtTime(now), delta=0.0000001)

        newNow = now + sysClock.tickRate * 1000
        self.assertAlmostEquals(0.000001, sysClock.dispersionAtTime(newNow), delta=0.0000001)

    def test_cannotSetParent(self):
        sysClock = self.newSysClock(tickRate=1000000000)
        sysClock2 = self.newSysClock(tickRate=1000000000)
        self.assertRaises(NotImplementedError, lambda : sysClock.setParent(sysClock2))

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
        

class Test_Correlation(unittest.TestCase):
    def test_createNeedsTwoArguments(self):
        self.assertRaises(TypeError, Correlation)
        self.assertRaises(TypeError, Correlation, 1)
        Correlation(1,2)
        
    def test_createTwoArgsZeroError(self):
        c = Correlation(1,2)
        self.assertEquals(1, c.parentTicks)
        self.assertEquals(2, c.childTicks)
        self.assertEquals(0, c.initialError)
        self.assertEquals(0, c.errorGrowthRate)
        
    def test_createWithErr(self):
        c = Correlation(1,2,3,4)
        self.assertEquals(1, c.parentTicks)
        self.assertEquals(2, c.childTicks)
        self.assertEquals(3, c.initialError)
        self.assertEquals(4, c.errorGrowthRate)
        
    def test_immutable(self):
        c = Correlation(1,2,3,4)
        try:
            c.parentTicks = 5
            self.fail(msg="Assignment of parentTicks property")
        except:
            pass
        try:
            c.childTicks = 5
            self.fail(msg="Assignment of childTicks property")
        except:
            pass
        try:
            c.initialError = 5
            self.fail(msg="Assignment of initialError property")
        except:
            pass
        try:
            c.errorGrowthRate = 5
            self.fail(msg="Assignment of errorGrowthRate property")
        except:
            pass
        
    def test_equality(self):
        """Correlations can be compared for equivalence using the equality operator"""
        self.assertEqual(Correlation(1,2,3,4), Correlation(1,2,3,4))
        self.assertEqual(Correlation(1,2,0,0), Correlation(1,2))
        self.assertNotEqual(Correlation(1,2), Correlation(1,2,3,4))
        self.assertNotEqual(Correlation(9,2,3,4), Correlation(1,2,3,4))
        self.assertNotEqual(Correlation(1,9,3,4), Correlation(1,2,3,4))
        self.assertNotEqual(Correlation(1,2,9,4), Correlation(1,2,3,4))
        self.assertNotEqual(Correlation(1,2,3,9), Correlation(1,2,3,4))

        self.assertFalse(Correlation(1,2,3,4) == Correlation(1,9,3,4))
        self.assertTrue(Correlation(1,2,3,4) != Correlation(1,9,3,4))
        
        self.assertFalse(Correlation(1,2,3,4) != Correlation(1,2,3,4))
        self.assertTrue(Correlation(1,2,3,4) == Correlation(1,2,3,4))
        
    def test_tupleEquivEquality(self):
        """Correlations can be compared with 2-tuples for equality of the parentTicks and childTicks"""
        self.assertEqual(Correlation(1,2,3,4), (1,2))
        self.assertEqual((1,2), Correlation(1,2,3,4))
        self.assertNotEqual(Correlation(9,2,3,4), (1,2))
        self.assertNotEqual(Correlation(1,9,3,4), (1,2))
        self.assertNotEqual((1,2), Correlation(9,2,3,4))
        self.assertNotEqual((1,2), Correlation(1,9,3,4))
        
    def test_mutate(self):
        c=Correlation(1,2,3,4)

        c2 = c.butWith()
        self.assertEquals(c2, Correlation(1,2,3,4))

        c3 = c.butWith(parentTicks=7)
        self.assertEquals(c3, Correlation(7,2,3,4))

        c4 = c.butWith(childTicks=99)
        self.assertEquals(c4, Correlation(1,99,3,4))

        c5 = c.butWith(initialError=888)
        self.assertEquals(c5, Correlation(1,2,888,4))

        c6 = c.butWith(errorGrowthRate=1000)
        self.assertEquals(c6, Correlation(1,2,3,1000))

    def test_tupleStyleUnpacking(self):
        """A correlation can be unpacked as if it is a 2-tuple by assignment-unpacking"""
        c = Correlation(1,2,3,4)
        x,y = c
        self.assertEquals(1,x)
        self.assertEquals(2,y)
        
    def test_tuppleStyleIndexing(self):
        """A correlation can be unpacked as if it is a 2-tuple by indexing"""
        c = Correlation(1,2,3,4)
        self.assertEquals(1,c[0])
        self.assertEquals(2,c[1])
        self.assertRaises(IndexError, lambda: c[2])

        
class Test_CorrelatedClock(unittest.TestCase):
    
    def setUp(self):
        self.mockTime = MockTime()
        self.mockTime.install()

    def tearDown(self):
        self.mockTime.uninstall()

    def newSysClock(self, *args, **kwargs):
        self.mockTime.enableAutoIncrementBy(0.000001, numReadsBetweenIncrements=1)
        sysClock = SysClock(*args, **kwargs)
        self.mockTime.disableAutoIncrement()
        return sysClock

    def test_correlationAndFreqPropertiesInitialised(self):
        b = self.newSysClock()
        c = CorrelatedClock(b, 1000, correlation=Correlation(0,300))
        self.assertEqual(c.correlation, Correlation(0,300))
        self.assertEqual(c.tickRate, 1000)
        
    
    def test_ticking(self):
        mockTime = self.mockTime

        b = self.newSysClock()

        mockTime.timeNow = 5020.8
        
        c = CorrelatedClock(b, 1000, correlation=Correlation(0,300))
        self.assertAlmostEqual(c.ticks, 5020.8*1000 + 300, places=5)
        
        mockTime.timeNow += 22.7
        self.assertAlmostEqual(c.ticks, (5020.8+22.7)*1000 + 300, places=5)
        
    def test_changeCorrelation(self):
        mockTime = self.mockTime

        b = self.newSysClock()
        mockTime.timeNow = 5020.8
        c = CorrelatedClock(b, 1000, correlation=Correlation(0,300))
        self.assertAlmostEqual(c.ticks, 5020.8*1000 + 300, places=5)
        
        c.correlation = Correlation(50000,320)
        self.assertEqual(c.correlation, Correlation(50000,320))
        self.assertAlmostEqual(c.ticks, (int(5020.8*1000000) - 50000) / 1000 + 320, places=5)
        
    def test_changeCorrelationToTuple(self):
        mockTime = self.mockTime

        b = self.newSysClock()
        mockTime.timeNow = 5020.8
        c = CorrelatedClock(b, 1000, correlation=(0,300))
        self.assertAlmostEqual(c.ticks, 5020.8*1000 + 300, places=5)
        
        c.correlation = (50000,320)
        self.assertEqual(c.correlation, Correlation(50000,320))
        self.assertAlmostEqual(c.ticks, (int(5020.8*1000000) - 50000) / 1000 + 320, places=5)
        
        c.setCorrelationAndSpeed((50000, 400), 1.0)
        self.assertEqual(c.correlation, Correlation(50000,400))
        self.assertAlmostEqual(c.ticks, (int(5020.8*1000000) - 50000) / 1000 + 400, places=5)
        
    def test_changeCorrelationNotifies(self):
        """Check a change to the correlation propagates notifications to dependents of this clock"""
        b = self.newSysClock()
        c = CorrelatedClock(b, 1000, correlation=Correlation(0,300))
        cc = CorrelatedClock(c, 50)
        
        d1 = MockDependent()
        d2 = MockDependent()
        d3 = MockDependent()
        
        b.bind(d1)
        c.bind(d2)
        cc.bind(d3)
        
        c.correlation = Correlation(50,20)
        
        d1.assertNotNotified()
        d2.assertNotificationsEqual([c])
        d3.assertNotificationsEqual([cc])
        
    def test_changeSpeedeNotifies(self):
        """Check a change to the correlation propagates notifications to dependents of this clock"""
        b = self.newSysClock()
        c = CorrelatedClock(b, 1000, correlation=Correlation(0,300))
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

        b = self.newSysClock()

        mockTime.timeNow = 5020.8
        
        c = CorrelatedClock(b, 1000, correlation=Correlation(50,300))
        self.assertAlmostEqual(c.ticks, (5020.8*1000000 - 50)/(1000000/1000) + 300, places=5)
        
        self.assertEqual(c.tickRate, 1000)
        c.tickRate = 500
        self.assertEqual(c.tickRate, 500)
        self.assertAlmostEqual(c.ticks, (5020.8*1000000 - 50)/(1000000/500) + 300, places=5)
        
    def test_changeFreqNotifies(self):
        mockTime = self.mockTime

        b = self.newSysClock()

        mockTime.timeNow = 5020.8
        
        c = CorrelatedClock(b, 1000, correlation=Correlation(50,300))
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
        b = self.newSysClock(tickRate = 1000)
        c = CorrelatedClock(b, 1000, correlation=Correlation(50,300))
        c.rebaseCorrelationAtTicks(400)
        self.assertEquals(c.correlation, Correlation(150,400))
      
    def test_toParentTicks(self):
        mockTime = self.mockTime

        b = self.newSysClock(tickRate=2000000)

        mockTime.timeNow = 1000.0
        
        c = CorrelatedClock(b, 1000, correlation=Correlation(50,300))
        self.assertAlmostEqual(c.toParentTicks(400), 50 + (400-300)*2000, places=5 )
        
        c = CorrelatedClock(b, 1000, correlation=Correlation(50,300), speed=0)
        self.assertEquals(c.toParentTicks(300), 50)
        self.assertTrue(math.isnan(c.toParentTicks(400)))
        
    def test_fromParentTicks(self):
        mockTime = self.mockTime

        b = self.newSysClock(tickRate=2000000)

        mockTime.timeNow = 1000.0
        
        c = CorrelatedClock(b, 1000, correlation=Correlation(50,300))
        self.assertAlmostEqual(c.fromParentTicks(50 + (400-300)*2000), 400, places=5 )
        
        c = CorrelatedClock(b, 1000, correlation=Correlation(50,300), speed=0)
        self.assertEquals(c.fromParentTicks(50), 300)
        self.assertEquals(c.fromParentTicks(100), 300)
      
    def test_getParent(self):
        b = self.newSysClock()
        c = CorrelatedClock(b, 1000, correlation=Correlation(50,300))
        self.assertEqual(c.getParent(), b)

    def test_getRoot(self):
        a = self.newSysClock()
        b = CorrelatedClock(a, 1000)
        c = CorrelatedClock(b, 2000)
        d = CorrelatedClock(c, 3000)
        
        self.assertEquals(a.getRoot(), a)
        self.assertEquals(b.getRoot(), a)
        self.assertEquals(c.getRoot(), a)
        self.assertEquals(d.getRoot(), a)

    def test_setCorrelationAndSpeed(self):
        a = self.newSysClock(tickRate=1000000)
        b = CorrelatedClock(a, 1000, correlation=Correlation(0,0))
        b.speed = 1.0
        
        db = MockDependent()
        b.bind(db)
        
        b.setCorrelationAndSpeed(Correlation(5,0),2)
        db.assertNotificationsEqual([b])
        self.assertEqual(b.toParentTicks(10), 5005)

    def test_quantifyChange(self):
        a = self.newSysClock()
        b = CorrelatedClock(a, 1000, correlation=Correlation(0,0))
        
        self.assertEquals(float('inf'), b.quantifyChange( Correlation(0,0), 1.01))        
        self.assertEquals(1.0, b.quantifyChange( Correlation(0, 1000), 1.0))
        
        b.speed = 0.0
        self.assertEquals(0.005, b.quantifyChange( Correlation(0, 5), 0.0))

    def test_setParent(self):
        a = self.newSysClock(tickRate=1000)
        b = CorrelatedClock(a, 1000, correlation=Correlation(0,0))
        c = CorrelatedClock(a, 1000, correlation=Correlation(10,0))
        d = MockDependent()
        b.bind(d)
        
        d.assertNotNotified()
        b.setParent(c)
        d.assertNotificationsEqual([b])
        self.assertEquals(b.getParent(), c)
        
    def test_setParentNoChangeNoNotify(self):
        a = self.newSysClock(tickRate=1000)
        b = CorrelatedClock(a, 1000, correlation=Correlation(0,0))
        c = CorrelatedClock(a, 1000, correlation=Correlation(10,0))
        d = MockDependent()
        b.bind(d)

        d.assertNotNotified()
        b.setParent(a)
        d.assertNotNotified()
        self.assertEquals(b.getParent(), a)
        
    def test_dispersionCalcForZeroError(self):
        """With zero error contribution, the dispersion at different times is the same as for the parent clock"""
        a = self.newSysClock(tickRate=1000)
        b = CorrelatedClock(a, 1000, correlation=Correlation(0,0))
        self.assertEquals(a.dispersionAtTime(10), b.dispersionAtTime(10))
        self.assertEquals(a.dispersionAtTime(20), b.dispersionAtTime(20))
        
    def test_dispersionCalcForError(self):
        """With non-zero error contribution, the dispersion at different times is additional to that of the parent clock, both before and after the correlation time"""
        a = self.newSysClock(tickRate=1000)
        b = CorrelatedClock(a, 1000, correlation=Correlation(0, 0, 0.5, 0.1))
        self.assertEquals(a.dispersionAtTime(10) + 0.5 + 0.1*10/1000, b.dispersionAtTime(10))
        self.assertEquals(a.dispersionAtTime(20) + 0.5 + 0.1*20/1000, b.dispersionAtTime(20))
        self.assertEquals(a.dispersionAtTime(-10) + 0.5 + 0.1*10/1000, b.dispersionAtTime(-10))
        

class Test_RangeCorrelatedClock(unittest.TestCase):
    
    def setUp(self):
        self.mockTime = MockTime()
        self.mockTime.install()

    def tearDown(self):
        self.mockTime.uninstall()

    def newSysClock(self, *args, **kwargs):
        self.mockTime.enableAutoIncrementBy(0.000001, numReadsBetweenIncrements=1)
        sysClock = SysClock(*args, **kwargs)
        self.mockTime.disableAutoIncrement()
        return sysClock

    def test_rangeConversion(self):
        mockTime = self.mockTime
        
        b = self.newSysClock(tickRate=1000)

        mockTime.timeNow = 0.0
        c = RangeCorrelatedClock(b, 1000, correlation1=Correlation(100,1000), correlation2=Correlation(200,1110))
        
        mockTime.timeNow = b.calcWhen(100)
        self.assertEqual(c.ticks, 1000)
       
        mockTime.timeNow = b.calcWhen(200)
        self.assertEqual(c.ticks, 1110)

        mockTime.timeNow = b.calcWhen(150)
        self.assertEqual(c.ticks, 1055)
        
    def test_withTuples(self):
        mockTime = self.mockTime
        
        b = self.newSysClock(tickRate=1000)

        mockTime.timeNow = 0.0
        c = RangeCorrelatedClock(b, 1000, correlation1=(100,1000), correlation2=(200,1110))
        self.assertEqual(Correlation(100,1000), c.correlation1)
        self.assertEqual(Correlation(200,1110), c.correlation2)
        
        mockTime.timeNow = b.calcWhen(100)
        self.assertEqual(c.ticks, 1000)
       
        mockTime.timeNow = b.calcWhen(200)
        self.assertEqual(c.ticks, 1110)

        c.correlation1 = (100, 2000)
        c.correlation2 = (200, 2110)
        self.assertEqual(Correlation(100,2000), c.correlation1)
        self.assertEqual(Correlation(200,2110), c.correlation2)
        self.assertEqual(c.ticks, 2110)

    def test_setParent(self):
        a = self.newSysClock(tickRate=1000)
        b = RangeCorrelatedClock(a, 1000, correlation1=(100,1000), correlation2=(200,1110))
        c = RangeCorrelatedClock(a, 1000, correlation1=(200,1000), correlation2=(300,1110))
        d = MockDependent()
        b.bind(d)
        
        d.assertNotNotified()
        b.setParent(c)
        d.assertNotificationsEqual([b])
        self.assertEquals(b.getParent(), c)
        
    def test_setParentNoChangeNoNotify(self):
        a = self.newSysClock(tickRate=1000)
        b = RangeCorrelatedClock(a, 1000, correlation1=(100,1000), correlation2=(200,1110))
        c = RangeCorrelatedClock(a, 1000, correlation1=(200,1000), correlation2=(300,1110))
        d = MockDependent()
        b.bind(d)

        d.assertNotNotified()
        b.setParent(a)
        d.assertNotNotified()
        self.assertEquals(b.getParent(), a)
        
      
class Test_TunableClock(unittest.TestCase):
    
    def setUp(self):
        self.mockTime = MockTime()
        self.mockTime.install()

    def tearDown(self):
        self.mockTime.uninstall()

    def newSysClock(self, *args, **kwargs):
        self.mockTime.enableAutoIncrementBy(0.000001, numReadsBetweenIncrements=1)
        sysClock = SysClock(*args, **kwargs)
        self.mockTime.disableAutoIncrement()
        return sysClock

    def test_tickRateAndTicksInitialised(self):
        mockTime = self.mockTime
        
        b = self.newSysClock()

        mockTime.timeNow = 5020.8
        
        c = TunableClock(b, tickRate=1000, ticks=5)
        self.assertEqual(c.ticks, 5)
        self.assertEqual(c.tickRate, 1000)
        self.assertEqual(c.speed, 1.0)
        
    def test_ticking(self):
        mockTime = self.mockTime
        
        b = self.newSysClock()

        mockTime.timeNow = 5020.8
        
        c = TunableClock(b, tickRate=1000, ticks=5)

        mockTime.timeNow += 100.2
        self.assertEqual(c.ticks, 100.2*1000 + 5)
        
    def test_slewFromMomentApplied(self):
        mockTime = self.mockTime
        
        b = self.newSysClock()

        mockTime.timeNow = 5020.8
        
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
        
        b = self.newSysClock()

        mockTime.timeNow = 5020.8
        
        c = TunableClock(b, tickRate=1000, ticks=5)

        mockTime.timeNow += 100.2
        self.assertEqual(c.ticks, 100.2*1000 + 5)
        
        c.adjustTicks(28)
        self.assertEqual(c.ticks, 100.2*1000 + 5 + 28)
        
    def test_slewNotifiesDependents(self):
        mockTime = self.mockTime
        
        b = self.newSysClock()

        mockTime.timeNow = 5020.8
        
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
        
        b = self.newSysClock(tickRate=1000000)

        mockTime.timeNow = 5020.8
        
        c = TunableClock(b, tickRate=1000, ticks=5)
        c.slew=50
        
        self.assertAlmostEqual(c.toParentTicks(5+1000*50), b.ticks + 1000000*50.0/1.050, delta=1)

    def test_fromParentTicks(self):
        mockTime = self.mockTime
        
        b = self.newSysClock(tickRate=1000000)

        mockTime.timeNow = 5020.8
        
        c = TunableClock(b, tickRate=1000, ticks=5)
        c.slew=50
        
        self.assertAlmostEqual(c.fromParentTicks(b.ticks + 1000000*50.0/1.050), 5+1000*50, places=5)

    def test_getParent(self):
        b = self.newSysClock()
        c = TunableClock(b, tickRate=1000, ticks=5)
        self.assertEqual(c.getParent(), b)

    def test_errorInitiallyZero(self):
        """Initially, the contribution to error/dispersion is zero and does not grow"""
        b = self.newSysClock()
        c = TunableClock(b, tickRate=1000, ticks=5)
        
        t = b.ticks
        parentDisp = b.dispersionAtTime(t)
        thisDisp = c.dispersionAtTime(c.fromParentTicks(t))
        self.assertEqual(0, parentDisp - thisDisp)
        
        thisDispLater = c.dispersionAtTime(c.fromParentTicks(t+1000000))
        self.assertEqual(thisDisp, thisDispLater)

    def test_errorSettable(self):
        mockTime = self.mockTime
        
        b = self.newSysClock(tickRate=1000)
        c = TunableClock(b, tickRate=1000, ticks=5)

        sysClockErr = b.dispersionAtTime(0) # will be constant

        mockTime.timeNow = 1000
        c.setError(0.1, growthRate = 0.01) # 0.1, increasing by 0.01 every second
        self.assertAlmostEquals(0.1 + sysClockErr, c.dispersionAtTime(c.ticks), delta=0.0000001)
        
        mockTime.timeNow += 5
        self.assertAlmostEquals(0.15 + sysClockErr, c.dispersionAtTime(c.ticks), delta=0.0000001)

        c.setError(0.2, growthRate = 0.001) # 0.2, increasing by 0.001 every second
        self.assertAlmostEquals(0.2 + sysClockErr, c.dispersionAtTime(c.ticks), delta=0.0000001)
        
        mockTime.timeNow += 5
        self.assertAlmostEquals(0.205 + sysClockErr, c.dispersionAtTime(c.ticks), delta=0.0000001)


class Test_OffsetClock(unittest.TestCase):
    """\
    Tests for OffsetClock
    """
    
    def setUp(self):
        self.root = SysClock() # init before installing mock, so it can do its precision measurement while time still flows
        self.mockTime = MockTime()
        self.mockTime.install()
        self.parent = CorrelatedClock(parentClock=self.root, tickRate=1000)
        self.altParent = CorrelatedClock(parentClock=self.root, tickRate=50)

    def tearDown(self):
        self.mockTime.uninstall()

    def test_speedAlways1(self):
        oc = OffsetClock(parentClock=self.parent)
        self.assertEquals(oc.speed, 1)
        self.parent.speed = 2.7
        self.assertEquals(oc.speed, 1)

    def test_effectiveSpeedSameAsParents(self):
        oc = OffsetClock(parentClock=self.parent)
        self.assertEquals(oc.getEffectiveSpeed(), self.parent.getEffectiveSpeed())
        self.parent.speed = 2.7
        self.assertEquals(oc.getEffectiveSpeed(), self.parent.getEffectiveSpeed())
        
    def test_inheritsTickRateFromParent(self):
        oc = OffsetClock(parentClock=self.parent)
        self.assertEquals(oc.tickRate, self.parent.tickRate)
        self.parent.tickRate = 25
        self.assertEquals(oc.tickRate, self.parent.tickRate)
        
    def test_offsetAppliedAtSpeed1(self):
        OC_AHEAD_BY=0.050
        oc = OffsetClock(parentClock=self.parent, offset=OC_AHEAD_BY)
        self.parent.speed = 1
        t = oc.ticks
        # advance time and see if OffsetClock was indeed ahead by OC_AHEAD_BY seconds
        self.mockTime.timeNow = self.mockTime.timeNow + OC_AHEAD_BY
        t2 = self.parent.ticks
        self.assertEquals(t,t2)
        
    def test_offsetAppliedAtSpeed0(self):
        OC_AHEAD_BY=0.098
        oc = OffsetClock(parentClock=self.parent, offset=OC_AHEAD_BY)
        self.parent.speed = 0
        t = oc.ticks
        # advance time and see if OffsetClock was indeed ahead by OC_AHEAD_BY seconds
        self.mockTime.timeNow = self.mockTime.timeNow + OC_AHEAD_BY
        t2 = self.parent.ticks
        self.assertEquals(t,t2)
        
    def test_offsetAppliedAtSpeedGreaterThan1(self):
        OC_AHEAD_BY=0.02
        oc = OffsetClock(parentClock=self.parent, offset=OC_AHEAD_BY)
        self.parent.speed = 2
        t = oc.ticks
        # advance time and see if OffsetClock was indeed ahead by OC_AHEAD_BY seconds
        self.mockTime.timeNow = self.mockTime.timeNow + OC_AHEAD_BY
        t2 = self.parent.ticks
        self.assertEquals(t,t2)
        
    def test_noOffsetWorks(self):
        oc = OffsetClock(parentClock=self.parent, offset=0)
        self.assertEquals(oc.ticks, self.parent.ticks)
        
    def test_offsetChangeNewOffsetUsed(self):
        oc = OffsetClock(parentClock=self.parent, offset=0.040)
        self.assertEquals(oc.ticks, self.parent.ticks + 40)
        oc.offset = 0.065
        self.assertEquals(oc.ticks, self.parent.ticks + 65)

    def test_parentChangedOffsetStillApplied(self):
        oc = OffsetClock(parentClock=self.parent, offset=0.040)
        self.assertEquals(oc.getParent(), self.parent) 
        self.assertEquals(oc.ticks, self.parent.ticks + 40)
        oc.setParent(self.altParent)
        self.assertEquals(oc.getParent(), self.altParent) 
        self.assertEquals(oc.ticks, self.altParent.ticks + 2)
        
    def test_parentChangeCausesNotification(self):
        oc = OffsetClock(parentClock=self.parent, offset=0.040)
        dep = MockDependent()
        oc.bind(dep)
        dep.assertNotNotified()
        oc.setParent(self.altParent)
        dep.assertNotificationsEqual([oc])
        
    def test_negativeOffsetWorks(self):
        OC_BEHIND_BY=0.050
        oc = OffsetClock(parentClock=self.parent, offset=-OC_BEHIND_BY)
        self.parent.speed = 1
        t = oc.ticks
        # regress time and see if OffsetClock was indeed behind by OC_BEHIND_BY seconds
        self.mockTime.timeNow = self.mockTime.timeNow - OC_BEHIND_BY
        t2 = self.parent.ticks
        self.assertEquals(t,t2)
        
    def test_toRootTicks(self):
        OC_AHEAD_BY=0.124
        oc = OffsetClock(parentClock=self.parent, offset=OC_AHEAD_BY)
        t = 1285.2
        rt = oc.toRootTicks(t)
        rt2 = self.parent.toRootTicks(t)
        self.assertEquals(rt + OC_AHEAD_BY*self.root.tickRate, rt2)
        
    def test_fromRootTicks(self):
        OC_AHEAD_BY=0.124
        oc = OffsetClock(parentClock=self.parent, offset=OC_AHEAD_BY)
        rt = 22849128
        t = oc.fromRootTicks(rt)
        t2 = self.parent.fromRootTicks(rt + OC_AHEAD_BY*self.root.tickRate)
        self.assertEquals(t, t2)


class Test_HierarchyTickConversions(unittest.TestCase):
    """\
    Tests for the toOtherClockTicks function
    """
    
    def setUp(self):
        self.mockTime = MockTime()
        self.mockTime.install()

    def tearDown(self):
        self.mockTime.uninstall()

    def newSysClock(self, *args, **kwargs):
        self.mockTime.enableAutoIncrementBy(0.000001, numReadsBetweenIncrements=1)
        sysClock = SysClock(*args, **kwargs)
        self.mockTime.disableAutoIncrement()
        return sysClock

    def test_noCommonAncestor(self):
        a = self.newSysClock()
        b = self.newSysClock()
        a1 = CorrelatedClock(a, tickRate=1000, correlation=Correlation(0,0))
        b1 = CorrelatedClock(b, tickRate=1000, correlation=Correlation(0,0))
        a2 = CorrelatedClock(a1, tickRate=1000, correlation=Correlation(0,0))
        b2 = CorrelatedClock(b1, tickRate=1000, correlation=Correlation(0,0))
        
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
        a = self.newSysClock(tickRate=1000000)
        a1 = CorrelatedClock(a, tickRate=100, correlation=Correlation(50,0))
        a2 = CorrelatedClock(a1, tickRate=78, correlation=Correlation(28,999))
        self.assertEquals(a1.toOtherClockTicks(a, 500), a1.toParentTicks(500)) 
        self.assertEquals(a2.toOtherClockTicks(a1, 500), a2.toParentTicks(500)) 
        
    def test_distantParent(self):
        a = self.newSysClock(tickRate=1000000)
        a1 = CorrelatedClock(a, tickRate=100, correlation=Correlation(50,0))
        a2 = CorrelatedClock(a1, tickRate=78, correlation=Correlation(28,999))
        self.assertEquals(a2.toOtherClockTicks(a, 500), a1.toParentTicks(a2.toParentTicks(500))) 

    def test_distantParentMidHierarchy(self):
        a = self.newSysClock(tickRate=1000000)
        a1 = CorrelatedClock(a, tickRate=100, correlation=Correlation(50,0))
        a2 = CorrelatedClock(a1, tickRate=78, correlation=Correlation(28,999))
        a3 = CorrelatedClock(a2, tickRate=178, correlation=Correlation(5,1003))
        a4 = CorrelatedClock(a3, tickRate=28, correlation=Correlation(17,9))
        self.assertEquals(a3.toOtherClockTicks(a1, 500), a2.toParentTicks(a3.toParentTicks(500)))

    def test_differentBranches(self):
        a = self.newSysClock(tickRate=1000000)
        a1 = CorrelatedClock(a, tickRate=100, correlation=Correlation(50,0))
        a2 = CorrelatedClock(a1, tickRate=78, correlation=Correlation(28,999))
        a3 = CorrelatedClock(a2, tickRate=178, correlation=Correlation(5,1003))
        a4 = CorrelatedClock(a3, tickRate=28, correlation=Correlation(17,9))
        b3 = CorrelatedClock(a2, tickRate=1000, correlation=Correlation(10,20))
        b4 = CorrelatedClock(b3, tickRate=2000, correlation=Correlation(15,90))
        
        v = a4.toParentTicks(500)
        v = a3.toParentTicks(v)
        v = b3.fromParentTicks(v)
        v = b4.fromParentTicks(v)
        
        self.assertEquals(a4.toOtherClockTicks(b4, 500), v)

    def test_speedChangePropagates(self):
        mockTime = self.mockTime
        
        a = self.newSysClock(tickRate=1000)

        mockTime.timeNow = 5
        
        a1 = CorrelatedClock(a, tickRate=1000, correlation=Correlation(50,0))
        a2 = CorrelatedClock(a1, tickRate=100, correlation=Correlation(28,999))
        a3 = CorrelatedClock(a2, tickRate=50, correlation=Correlation(5,1003))
        a4 = CorrelatedClock(a3, tickRate=25, correlation=Correlation(1000,9))
        b3 = CorrelatedClock(a2, tickRate=1000, correlation=Correlation(500,20))
        b4 = CorrelatedClock(b3, tickRate=2000, correlation=Correlation(15,90))
        
        at1, a1t1, a2t1, a3t1, a4t1, b3t1, b4t1 = [x.ticks for x in [a,a1,a2,a3,a4,b3,b4]]
        a3.speed = 0.5
        a4.speed = 0.2
        self.assertEquals(1.0, a.getEffectiveSpeed())
        self.assertEquals(1.0, a1.getEffectiveSpeed())
        self.assertEquals(1.0, a2.getEffectiveSpeed())
        self.assertEquals(0.5, a3.getEffectiveSpeed())
        self.assertEquals(0.1, a4.getEffectiveSpeed())


        a3.speed = 0
        a4.speed = 1.0
        self.assertEquals(1.0, a.getEffectiveSpeed())
        self.assertEquals(1.0, a1.getEffectiveSpeed())
        self.assertEquals(1.0, a2.getEffectiveSpeed())
        self.assertEquals(0.0, a3.getEffectiveSpeed())
        self.assertEquals(0.0, a4.getEffectiveSpeed())

        mockTime.timeNow = 6 # advance time 1 second
        
        at2, a1t2, a2t2, a3t2, a4t2, b3t2, b4t2 = [x.ticks for x in [a,a1,a2,a3,a4,b3,b4]]
        
        self.assertEquals(at2,  at1 + 1000)  # a  still advances
        self.assertEquals(a1t2, a1t1 + 1000) # a1 still advances
        self.assertEquals(a2t2, a2t1 + 100)  # a2 still advances
        self.assertEquals(a3t2, 1003)        # a3 is speed zero, is now at the correlation point
        self.assertEquals(a4t2, 10.5)        # a4 is speed zero, a3.ticks is 3 ticks from correlation point for a4, translating to 1.5 ticks from a4 correlation point at its tickRate
        self.assertEquals(b3t2, b3t1 + 1000) # b3 still advances
        self.assertEquals(b4t2, b4t1 + 2000) # b4 is paused
        
    def test_availabilityPropagation(self):
        a = self.newSysClock()
        b = CorrelatedClock(a, 1000)
        c = CorrelatedClock(b, 2000)
        d = CorrelatedClock(c, 3000)
        
        da = MockDependent()
        db = MockDependent()
        dc = MockDependent()
        dd = MockDependent()

        a.bind(da)
        b.bind(db)
        c.bind(dc)
        d.bind(dd)
        
        self.assertTrue(a.isAvailable())
        self.assertTrue(b.isAvailable())
        self.assertTrue(c.isAvailable())
        self.assertTrue(d.isAvailable())

        c.setAvailability(False)
        self.assertTrue(a.isAvailable())
        self.assertTrue(b.isAvailable())
        self.assertFalse(c.isAvailable())
        self.assertFalse(d.isAvailable())
        da.assertNotNotified()
        db.assertNotNotified()
        dc.assertNotificationsEqual([c])
        dd.assertNotificationsEqual([d])

        d.setAvailability(False)
        self.assertTrue(a.isAvailable())
        self.assertTrue(b.isAvailable())
        self.assertFalse(c.isAvailable())
        self.assertFalse(d.isAvailable())
        da.assertNotNotified()
        db.assertNotNotified()
        dc.assertNotNotified()
        dd.assertNotNotified()

        c.setAvailability(True)
        self.assertTrue(a.isAvailable())
        self.assertTrue(b.isAvailable())
        self.assertTrue(c.isAvailable())
        self.assertFalse(d.isAvailable())
        da.assertNotNotified()
        db.assertNotNotified()
        dc.assertNotificationsEqual([c])
        dd.assertNotificationsEqual([d])

    def test_clockDiff(self):
        a = self.newSysClock()
        self.mockTime.timeNow = 1
        b = CorrelatedClock(a, 1000, correlation=Correlation(0,0))
        c = CorrelatedClock(b, 2000, correlation=Correlation(0,0))
        d = CorrelatedClock(c, 3000, correlation=Correlation(0,0))
        e = RangeCorrelatedClock(d, 1000, Correlation(5,0), Correlation(15005,5000))
    
        self.assertEquals(float('inf'), b.clockDiff(c))
        self.assertEquals(float('inf'), b.clockDiff(d))
        self.assertAlmostEquals(0.001666667, b.clockDiff(e), delta=0.000001)
        
        self.mockTime.timeNow += 10000000
        
        self.assertEquals(float('inf'), b.clockDiff(c))
        self.assertEquals(float('inf'), b.clockDiff(d))
        self.assertAlmostEquals(0.001666667, b.clockDiff(e), delta=0.000001)
        
        c.tickRate = 1000
        self.assertEquals(0, b.clockDiff(c))

        c.speed = 1.01
        self.assertEquals(float('inf'), b.clockDiff(c))
        
if __name__ == "__main__":
    unittest.main()
