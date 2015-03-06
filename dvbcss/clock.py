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

r"""\
The dvbcss.clock module provides software synthesised clock objects that can be chained together into dependent hierarchies.
Use in conjunction with :mod:`dvbcss.task` to sleep and run code at set times on these clocks.

Introduction
------------

The classes in this module implement software synthesised clocks
from which you can query a current time value.
A clock counts in whole numbers of ticks (unlike the standard library :func:`time.time` function which
counts in seconds and fractions of a second) and has a tick rate (expresed in ticks per second). 

To use clocks as timers or to schedule code to run later, you must use them with the functions of the :mod:`dvbcss.task` module.

To use clocks begin with a root clock that is based on a underlying timing source.
The following root clocks are provided:

* :class:`SysClock` **is an root clock based on the** :func:`dvbcss.monotonic_time.time` **function as the underlying time source**

Other dependent clocks can then be created that have the underlying clock as their parent. 
and further dependent clocks can be created with those dependents as their parents, creating
chains of clocks, each based on their parent and leading back to an underlying clock.
The following dependent clocks are provided:

* :class:`CorrelatedClock` **is a fixed tick rate clock where you define the point of correlation between it and its parent.**
* :class:`TunableClock` **is a clock that can have its tick count tweaked and its frequency slewed on the fly.**
* :class:`RangleCorrelatedClock` **is a clock where the relationship to the parent is determined from two points of correlation.**

Dependent clocks can have a different tick rate to their parent and count their ticks from a
different starting point.

Dependent clocks allow their relationship to its parent clock
to be changed dynamically - e.g. the absolute value, or the rate at which
the clock ticks. If your code needs to be notified of such a change, it
can bind itself as a dependent to that clock.

The base :class:`ClockBase` class defines the set of methods common to
all clocks (both underlying and dependent)


Limitations on tick resolution (precision)
------------------------------------------

The Clock objects here do not run a thread that counts individual ticks. Instead, to determine the current tick value
they query the parent clock for its current tick value and then calculate what the tick value should be.

A clock is therefore **limited in the precision and resolution of its tick value by its parents.** :class:`SysClock`,
for example, is limited by the resolution of the underlying time source provided to it by :mod:`dvbcss.monotonic_time`
module's :func:`dvbcss.monotonic_time.time` function. And this will be operating system dependent. SysClock also outputs
ticks as integer values.

If a parent of a clock only reports whole number (integer) tick values then that also limits the resolution of any
clocks that depend on it. For example, a clock that counts in integer ticks only at 25 ticks per second will cause a
clock descended from it, with a tick rate of 100 ticks per second, to report tick values that increment 4 ticks
at a time ... or worse if a parent of both has an even lower tick rate.

With the clocks provided by this module, only :class:`SysClock` limits itself to integer numbers of ticks.
:class:`CorrelatedClock` and :class:`TunableClock` are capable of fractional numbers of ticks provided that the
parameters provided to them (e.g. the tickRate) are passed as floating point values (this will force python to
do the maths in floating point instead of integer maths).



Timers and Sleep functions
--------------------------

Use the functions of the :mod:`dvbcss.task` in conjunction with Clock objects
to create code that sleeps, or which triggers callbacks, based on time as
measured by these clocks.



Usage examples
--------------

Simple hierarchies of clocks
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Here is a simple example where a clock represents a timeline and
another represents a timeline related to the first by a correlation:

.. code-block:: python

    from dvbcss.clock import SysClock
    from dvbcss.clock import CorrelatedClock
    
    # create a clock based on dvbcss.monotonic_time.time() that ticks in milliseconds
    sysClock = SysClock(tickRate=1000)
    
    # create a clock to represent a timeline 
    baseTimeline = CorrelatedClock(parentClock=sysClock, tickRate=25, correlation=(0,0))
    
    # create a clock representing another timeline, where time zero corresponds to time 100
    # on the parent timeline
    subTimeline = CorrelatedClock(parentClock=baseTimeline, tickRate=25, correlation=(100,0)
    
At some point later in time during the program, we query the values of all the clocks,
confirming that the sub timeline is always 100 ticks ahead of the base timeline.

.. code-block:: python

    def printTimes():
        sys  = sysClock.ticks()
        base = baseTimeline.ticks()
        sub  = subTimeline.ticks()
        print "SysClock      ticks = %d", sys
        print "Base timeline ticks = %d", base
        print "Sub timeline  ticks = %d", sub
        
    >>> printTimes()
    SysClock      ticks = 20000
    Base timeline ticks = 500
    Sub timeline  ticks = 600 

*Note that in these examples, for clarity, the tick count on the sysClock is artificially low. It would likely be a much larger value.*

We then change the correlation for the base timeline, declaring tick 25 on its baseline to correspond to tick 0 on its parent timeline,
and both the base timeline and the sub timeline reflect this:

.. code-block:: python
    
    >>> baseTimeline.correlation = (0,25)
    >>> printTimes()
    SysClock      ticks = 30000
    Base timeline ticks = 775
    Sub timeline  ticks = 875 


Clock speed adjustment
~~~~~~~~~~~~~~~~~~~~~~
    
All clocks have a :data:`speed` property. Normally this is 1.0. Some clock classes support changing this value. This scales the rate at which
the clock ticks relative to its parent. For example, 0.5 corresponds to half speed; 2.0 = double speed, 0 = frozen and -1.0 = reverse.

Clocks will take speed into account when returning their current tick position or converting it to or from the tick value of a parent clock. However
it does not alter the tickRate property. A child clock will similarly ignore the speed property of a parent clock. In this way, the speed property can be
used to tweak the speed of time, or to emulate speed control (fast forward, rewind, pause) for a media timeline.

Here is an example where we create 3 clocks in a chain and all tick initially at 100 ticks per second:

.. code-block:: python

    >>> import time
    >>> baseClock = Sysclock(tickRate=100)
    >>> clock1 = TunableClock(parent=baseClock, tickRate=100)
    >>> clock2 = TunableClock(parent=clock1, tickRate=100)
    
We confirm that both clock1 and its child - clock2 - tick at 100 ticks per second:

.. code-block:: python

    >>> print clock1.ticks; time.sleep(1.0); print clock1.ticks
    5023
    5123
    >>> print clock2.ticks; time.sleep(1.0); print clock2.ticks
    2150
    2250

If we change the tick rate of clock1 this affects clock1, but its child - clock2 - continues to tick at 100 ticks every second:

.. code-block:: python

    >>> clock1.tickRate = 200
    >>> print clock1.ticks; time.sleep(1.0); print clock1.ticks
    5440
    5640
    >>> print clock2.ticks; time.sleep(1.0); print clock2.ticks
    4103
    4203

But if we *instead* change the speed multiplier of clock1 then this not only affects the ticking rate of clock1 but also of its child - clock2:

.. code-block:: python

    >>> clock1.tickRate = 100
    >>> clock1.speed = 2.0
    >>> print clock1.ticks; time.sleep(1.0); print clock1.ticks
    5740
    5940
    >>> print clock2.ticks; time.sleep(1.0); print clock2.ticks
    4603
    4803
    
    
Translating tick values between clocks
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The clock classes provide mechanisms to translate a tick value from one clock to a tick value of another clock such that it still
represents the same moment in time. So long as both clocks share a common ancestor clock, the conversion will be possible.

:func:`~ClockBase.toParentTicks` and :func:`~ClockBase.fromParentTicks` converts tick values for a clock to/from its parent clock.
:func:`~ClockBase.toOtherClockTicks` will convert a tick value for this clock to the corresponding tick value for any other clock
with a common ancestor to this one.

.. code-block:: python

    from dvbcss.clock import SysClock
    from dvbcss.clock import CorrelatedClock
    
    # create a clock based on dvbcss.monotonic_time.time() that ticks in milliseconds
    sysClock = SysClock(tickRate=1000)
    
    #                                       +------------+
    #                                   .-- | mediaClock |
    # +----------+     +-----------+ <--'   +------------+
    # | sysClock | <-- | wallClock | 
    # +----------+     +-----------+ <--.   +-----------------+
    #                                   '-- | otherMediaClock |
    #                                       +-----------------+

    wallClock = CorrelatedClock(parentClock=sysClock, tickRate=1000000000, correlation=(0,0))
    mediaClock = CorrelatedClock(parentClock=wallClock, tickRate=25, correlation=(500021256, 0))
    otherMediaClock = CorrelatedClock(parentClock=wallClock, tickRate=30, correlation=(21093757, 0))
    
    # calculate wall clock time 'w' corresponding to a mediaClock time 1582:
    t = 1582
    w = mediaClock.toParentTicks(t)    
    print "When MediaClock ticks =", t, " wall clock ticks =", w

    # calculate mediaClock time 'm' corresponding to wall clock time 1920395
    w = 1920395
    m = mediaClock.fromParentTicks(w)
    print "When wall clock ticks =", w, " media clock ticks =", m

    # calculate other media clock time corresponding to media clock time 2248
    t = 2248
    o = mediaClock.toOtherClockTicks(otherMediaClock, t)
    print "When MediaClock ticks =", t, " other media clock ticks =", o



Implementing new clocks
~~~~~~~~~~~~~~~~~~~~~~~

Implement a new clock class by subclassing :class:`ClockBase` and implementing the stub methods.

For example, here is a clock that is the same as its parent (same tick rate) except that its
current tick value differs by a fixed offset.

.. code-block:: python

    from dvbcss.clock import ClockBase
    
    class FixedTicksOffsetClock(ClockBase):
    
        def __init__(self, parent, offset):
            super(FixedTicksOffsetClock,self).__init__()
            self._parent = parent
            self._offset = offset
            
        def calcWhen(self, ticksWhen):
            return self._parent.calcWhen(ticksWhen - self._offset)
            
        def fromParentTicks(self, ticks):
            return ticks + self._offset
            
        def getParent(self):
            return self._parent
            
        @property
        def tickRate(self):
            return self._parent.tickRate
        
        @property
        def ticks(self)
            return self._parent.ticks + self._offset
            
        def toParentTicks(self, ticks):
            return ticks - self._offset

In use:

.. code-block:: python

    >>> f = FixedTicksOffsetClock(parentClock, 100)
    >>> print parentClock.ticks, f.ticks
    216 316

When doing this, you must decide whether to allow the speed to be adjusted. If you do, then it must be taken into account in the calculations for the methods:
:func:`calcWhen`, :func:`fromParentTicks` and :func:`toParentTicks`.    
"""


import dvbcss.monotonic_time as time
import dvbcss
import numbers

class NoCommonClock(Exception):
    """\
    Exception that is raised if an operation cannot be completed because there is no common
    ancestor clock shared between the clocks involved in the operation.
    """
    def __init__(self, clockA, clockB):
        super(NoCommonClock,self).__init__("Unable to complete operation because there is no common ancestor clock of "+str(clockA)+" "+str(clockB))
        self.clocks = (clockA, clockB)


def measurePrecision(clock,sampleSize=10000):
    r"""\
    Do a very rough experiment to work out the precision of the provided clock.
    
    Works by empirically looking for the smallest observable difference in the tick count.
    
    :param clock: (:class:dvbcss.clock.ClockBase) Clock to measure
    :param sampleSize: (int) Number of iterations (sample size) to estimate the precision over
    :return: (float) estimate of clock measurement precision (in seconds)
    """
    diffs=[]
    while len(diffs) < sampleSize:
        a=clock.ticks
        b=clock.ticks
        if a < b:
            diffs.append(b-a)
    return float(min(diffs))/clock.tickRate



class ClockBase(object):
    """\
    Base class for all clock classes.
    
    By default, adjusting tickRate and speed are not permitted unless a subclass overrides and implements a property setter.
    """
    def __init__(self,**kwargs):
        super(ClockBase,self).__init__(**kwargs)
        self.dependents = {}
        
    @property    
    def ticks(self):
        """\
        (read only) The tick count for this clock.
        
        |stub-method|
        """
        raise NotImplemented
        
    @property
    def speed(self):
        """\
        (read/write :class:`float`) The speed at which the clock is running.
        Does not change the reported tickRate value, but will affect how ticks are calculated
        from parent clock ticks. Default = 1.0 = normal tick rate.
        """
        return 1.0
    
    @speed.setter
    def speed(self, newValue):
        if newValue != 1.0:
            raise NotImplementedError("Changing speed is not implemented for this clock.")

    def getEffectiveSpeed(self):
        """\
        Returns the 'effective speed' of this clock.
        
        This is equal to multiplying together the speed properties of this clock and all of the parents up to the root clock.
        """
        s = 1.0
        clock = self
        while clock is not None:
            s = s*clock.speed;
            clock = self.getParent()
        return s

    @property
    def tickRate(self):
        """\
        (read only)The tick rate (in ticks per second) of this clock.
        
        |stub-method|
        """
        raise NotImplemented
    
    @property
    def nanos(self):
        """\
        (read only) The tick count of this clock, but converted to units of nanoseconds, based on the current tick rate (but ignoring the `speed` property).
        """
        return self.ticks*1000000000/self.tickRate
        
    def nanosToTicks(self,nanos):
        """\
        Convert the supplied nanosecond to number of ticks given the current tick rate of this clock (but ignoring the `speed` property).
        
        :param nanos: nanoseconds value
        :returns: number of ticks equivalent to the supplied nanosecond value
        """
        return nanos*self.tickRate/1000000000
        
    def notify(self,cause):
        """\
        Call to notify this clock that the clock on which it is based (its parent) has changed relative to the underlying timing source.
        
        :param cause: The clock that is calling this method.
        
        Will notify all dependents of this clock (entities that have registered themselves by calling :func:`bind`).
        """
        for dependent in self.dependents:
            dependent.notify(self)
        
    def bind(self,dependent):
        """\
        Bind for notification if this clock changes.
        
        :param dependent: When this clock changes, the :func:`notify` method of this dependent will be called, passing a single argument that is this clock.
        
        """
        self.dependents[dependent]=True
        
    def unbind(self,dependent):
        """\
        Unbind from notification if this clock changes.
        
        :param dependent: The dependent to unbind from receiving notifications.
        """
        del self.dependents[dependent]

    def calcWhen(self, ticksWhen):
        """\
        :Return: "when" in terms of the underlying clock behind the root clock implementation (e.g. :func:`monotonic_time.time` in the case of :class:`SysClock`)
        
        |stub-method|
        """
        raise NotImplemented
    
    def toOtherClockTicks(self, otherClock, ticks):
        """\
        Converts a tick value for this clock into a tick value corresponding to the timescale of another clock.
        
        :param otherClock: A :class:`~dvbcss.clock` object representing another clock.
        :param ticks: A time (tick value) for this clock
        
        :returns: The tick value of the `otherClock` that represents the same moment in time.
        
        :throws NoCommonClock: if there is no common ancestor clock (meaning it is not possible to convert
        """
        # establish the ancestry of both clocks up to a root
        selfAncestry=[self]
        for c in selfAncestry:
            p=c.getParent()
            if p is not None:
                selfAncestry.append(p)
        
        otherAncestry=[otherClock]
        for c in otherAncestry:
            p=c.getParent()
            if p is not None:
                otherAncestry.append(p)
        
        # work out if there is a common ancestor and eliminate common ancestors
        common=False
        while len(selfAncestry) and len(otherAncestry) and selfAncestry[-1] == otherAncestry[-1]:
            del selfAncestry[-1]
            del otherAncestry[-1]
            common=True
        if not common:
            raise NoCommonClock(self,otherClock)
        
        # now we have a path from both clocks to a common ancestor.
        # note that the lists do NOT include the common ancestor itself
        
        # 1) walk the path to the common ancestor converting tick values
        for c in selfAncestry:
            ticks = c.toParentTicks(ticks)
        
        # 2) walk the path back up from the common ancestor to the other clock, converting tick values
        otherAncestry.reverse()
        for c in otherAncestry:
            ticks = c.fromParentTicks(ticks)
            
        return ticks
        
        
    def toParentTicks(self, ticks):
        """\
        |stub-method|

        Method to convert from a tick value for this clock to the equivalent tick value (representing the same point in time) for the parent clock.
        
        Implementations should use the parent clock's :data:`tickRate` and :data:`speed` properties when performing the conversion.

        :returns: The specified tick value of this clock converted to the timescale of the parent clock.
        
        :throws StopIteration: if this clock has no parent
        """
        raise NotImplemented
    
    def fromParentTicks(self, ticks):
        """\
        |stub-method|
        
        Method to convert from a tick value for this clock's parent to the equivalent tick value (representing the same point in time) for this clock.

        Implementations should use the parent clock's :data:`tickRate` and :data:`speed` properties when performing the conversion.

        :returns: The specified tick value for the parent clock converted to the timescale of this clock.
        
        :throws StopIteration: if this clock has no parent
        """
        raise NotImplemented
    
    def getParent(self):
        """\
        |stub-method|

        :returns: :class:`ClockBase` representing the immediate parent of this clock, or None if it is a root clock.
        """
        raise NotImplemented
    
    
        
@dvbcss._inheritDocs(ClockBase)
class SysClock(ClockBase):
    """\
    A clock based directly on the standard library timer function :func:`monotonic_time.time`.
    Returns `integer` ticks when its :data:`ticks` property is queried.
    
    The default tick rate is 1 million ticks per second, but a different tick rate can be chosen during initialisation.
    
    It is not permitted to change the :data:`tickRate` or :data:`speed` property of this clock because it directly represents a system clock.
    """
    
    def __init__(self,tickRate=1000000, **kwargs):
        """\
        :param tickRate: (int) tick rate for this clock (in ticks per second)
        """
        super(SysClock,self).__init__(**kwargs)
        if tickRate <= 0 or not isinstance(tickRate, numbers.Number):
            raise ValueError("Cannot set tickRate to "+repr(tickRate))
        self._freq = tickRate
        
    @property
    def ticks(self):
        return int(time.time() * self._freq)
        
    @property
    def tickRate(self):
        return self._freq

    def calcWhen(self, ticksWhen):
        return ticksWhen / float(self._freq)
        
    def __repr__(self):
        return "SysClock( t=%d, freq=%d )" % (self.ticks, self._freq)

    def toParentTicks(self, ticks):
        raise StopIteration()

    def fromParentTicks(self, ticks):
        raise StopIteration()
    
    def getParent(self):
        return None
    



@dvbcss._inheritDocs(ClockBase)
class CorrelatedClock(ClockBase):
    r"""\
    A clock locked to the tick count of the parent clock by a correlation and frequency setting.
    
    Correlation is a tuple `(parentTicks, selfTicks)`
    
    When the parent clock ticks property has the value `parentTicks`, the ticks property of this clock
    shall have the value `selfTicks`.

    This relationship can be illustrated as follows:

    .. image:: correlated-clock.png
       :width: 384pt
       :align: center

    You can alter the correlation and tickRate and speed of this clock dynamically. Changes to tickRate and speed
    will not shift the point of correlation. This means that a change in tickRate or speed will probably cause the
    current tick value of the clock to jump. The amount it jumps by will be proportional to the distance the current
    time is from the point of correlation:
    
    .. image:: correlated-clock-speed-change-issue.png
       :width: 384pt
       :align: center
    
    If you want a speed change to only affect the ticks from a particular point (e.g. the current tick value) onwards
    then you must re-base the correlation. There is a function provided to do that in some circumstances:
    
    .. code-block:: python
    
        c = CorrelatedClock(parentClock=parent, tickRate=1000, correlation=(50,78))
        
           ... time passes ...
           
        # now freeze the clock AT ITS CURRENT TICK VALUE
        
        c.rebaseCorrelationAtTicks(c.ticks)
        c.speed = 0
    
        # now resume the clock but at half speed, but again without the tick value jumping
        c.correlation = ( parent.ticks, c.ticks )
        c.speed = 0.5
    
    .. note::
    
       The maths to calculate and convert tick values will be performed, by default, as integer maths
       unless the parameters controlling the clock (tickRate etc) are floating point, or the ticks property
       of the parent clock supplies floating point values.
    
    """
    
    def __init__(self, parentClock, tickRate, correlation=(0,0), **kwargs):
        """\
        :param parentClock: The parent clock for this clock.
        :param tickRate: (int) tick rate for this clock (in ticks per second)
        :param correlation: (tuple(int, int)) The intial correlation for this clock. A tuple (parent tick value, this clock tick value)
        """
        super(CorrelatedClock,self).__init__(**kwargs)
        if tickRate <= 0 or not isinstance(tickRate, numbers.Number):
            raise ValueError("Cannot set tickRate to "+repr(tickRate))
        self._freq = tickRate
        self._parent=parentClock
        self._speed = 1.0
        if not isinstance(correlation,tuple) or len(correlation) != 2:
            raise ValueError("Correlation must be a 2-tuple of tick values")
        self._correlation=correlation
        parentClock.bind(self)
    
    @property
    def ticks(self):
        return self.correlation[1] + (self._parent.ticks - self._correlation[0])*self._freq*self.speed/self._parent.tickRate
        
    def __repr__(self):
        return "CorrelatedClock(t=%d, freq=%f, correlation=(%d,%d)) at speed=%f" % (self.ticks, self._freq, self._correlation[0], self._correlation[1], self.speed)

    @property
    def tickRate(self):
        """\
        Read or change the tick rate (in ticks per second) of this clock. The value read is not affected by the value of the :data:`speed` property.
        """
        return self._freq
    
    @tickRate.setter
    def tickRate(self,value):
        self._freq = value
        self.notify(self)
        
    @property
    def speed(self):
        return self._speed
    
    @speed.setter
    def speed(self, newSpeed):
        self._speed = float(newSpeed)
        self.notify(self)

    def rebaseCorrelationAtTicks(self, tickValue):
        """\
        Changes the :data:`correlation` property to an equivalent correlation (that does not change the timing relationship between
        parent clock and this clock) where the tick value for this clock is the provided tick value.
        """
        parentTickValue = self.toParentTicks(tickValue)   
        self._correlation = (parentTickValue, tickValue)
        # no need to 'notify' because we have not changed the timing relationship

    @property
    def correlation(self):
        """\
        Read or change the correlation tuple `(parentTicks, selfTicks)` of this clock to its parent clock.
        
        Assign a new tuple `(parentTicks, selfTicks)` to change the correlation. 
        This value must be a tuple, not a list.
        """
        return self._correlation
    
    @correlation.setter
    def correlation(self,value):
        if not isinstance(value,tuple) or len(value) != 2:
            raise ValueError("Correlation must be a 2-tuple of tick values")
        self._correlation=value
        self.notify(self)
        
    def calcWhen(self,ticksWhen):
        if self.speed == 0:
            refticks=self._correlation[0]   # return any arbitrary position if the speed of this clock is zero (pause)
        else:
            refticks=self._correlation[0] + (ticksWhen - self._correlation[1])*self._parent.tickRate/self._freq/self.speed
        return self._parent.calcWhen(refticks)

    def toParentTicks(self, ticks):
        if self.speed == 0:
            return self._correlation[0]   # return any arbitrary position if the speed of this clock is zero (pause)
        else:
            return self._correlation[0] + (ticks - self._correlation[1])*self._parent.tickRate/self._freq/self.speed

    def fromParentTicks(self, ticks):
        return self._correlation[1] + (ticks - self._correlation[0])*self._freq*self.speed/self._parent.tickRate
    
    def getParent(self):
        return self._parent
    


@dvbcss._inheritDocs(ClockBase)
class TunableClock(ClockBase):
    """\
    A clock whose tick offset and speed can be adjusted on the fly.
    Must be based on another clock.
    
    Advancement of time of this clock is based on the tick count and rates reported by
    the supplied parent clock.
    
    If you adjust the tickRate or speed, then the change is applied going forward from the moment it is made.
    E.g. if you are observing the rate of increase of the ticks property, then doubling the speed wil cause
    the ticks property to start increasing faster but will not cause it to suddenly jump value.
    
    .. note::
    
       The maths to calculate and convert tick values will be performed, by default, as integer maths
       unless the parameters controlling the clock (tickRate etc) are floating point, or the ticks property
       of the parent clock supplies floating point values.
    """

    def __init__(self, parentClock, tickRate, ticks=0, **kwargs):
        """\
        :param parentClock: The parent clock for this clock.
        :param tickRate: The tick rate (ticks per second) for this clock.
        :param ticks: The starting tick value for this clock.
        
        The specified starting tick value applies from the moment this object is initialised.
        """
        super(TunableClock,self).__init__(**kwargs)
        if tickRate <= 0 or not isinstance(tickRate, numbers.Number):
            raise ValueError("Cannot set tickRate to "+repr(tickRate))
        self._parent = parentClock
        self._freq = tickRate
        self._ticks = ticks
        self._speed = 1.0
        self._last=self._parent.ticks
        parentClock.bind(self)
        # self._last and self.ticks constitute a correlation
            
    def _rebase(self):
        now = self._parent.ticks
        delta = now-self._last
        
        self._ticks += delta*self._freq*self._speed/self._parent.tickRate
        
        self._last = now
    
    @property
    def tickRate(self):
        """\
        Read or change the tick rate (in ticks per second) of this clock. The value read is not affected by the value of the :data:`speed` property.
        """
        return self._freq
    
    @tickRate.setter
    def tickRate(self,value):
        self._rebase()
        self._freq = value
        self.notify(self)

    @property
    def speed(self):
        return self._speed
    
    @speed.setter
    def speed(self, newSpeed):
        self._rebase()
        self._speed = float(newSpeed)
        self.notify(self)

    @property
    def slew(self):
        """\
        This is an alternative method of querying or adjusting the speed property.
        
        The slew (in ticks per second) currently applied to this clock.
        
        Setting this property will set the speed property to correspond to the specified slew.
        
        For example: for a clock with tickRate of 100, then a slew of -25 corresponds to a speed of 0.75
        """
        return (self._speed-1.0)*self._freq  
    
    @slew.setter
    def slew(self, slew):  
        self.speed = (float(slew) / self._freq) + 1.0
        
    @property
    def ticks(self):
        now = self._parent.ticks
        delta = now - self._last
        
        return self._ticks + delta*self._freq*self.speed/self._parent.tickRate
        
    def adjustTicks(self,offset):
        """\
        Change the tick count of this clock by the amount specified.
        """
        self._ticks=self._ticks+offset
        self.notify(self)
    

    def calcWhen(self,ticksWhen):
        if self._speed == 0:
            refticks = self._last
        else:
            refticks=self._last + (ticksWhen - self._ticks)*self._parent.tickRate/self._freq/self._speed
        return self._parent.calcWhen(refticks)
        
    def __repr__(self):
        return "TunableClock( t=%d, freq=%d ) at speed %f" % (self.ticks, self.tickRate, self._speed)

    def toParentTicks(self, ticks):
        if self._speed == 0:
            return self._last
        else:
            return self._last + (ticks - self._ticks)*self._parent.tickRate/self._freq/self._speed

    def fromParentTicks(self, ticks):
        if self._speed == 0:
            return self._ticks
        else:
            return self._ticks + (ticks - self._last)*self._freq*self._speed/self._parent.tickRate
    
    def getParent(self):
        return self._parent
    


@dvbcss._inheritDocs(ClockBase)
class RangeCorrelatedClock(ClockBase):
    r"""\
    A clock locked to the tick count of the parent clock by two different points of correlation.
    
    Each correlation is a tuple `(parentTicks, selfTicks)`
    
    This relationship can be illustrated as follows:
    
    .. image:: range-correlated-clock.png
       :width: 384pt
       :align: center
       
    The tickRate you set is purely advisory - it is the tickRate reported to clocks that use this clock as the parent,
    and may differ from what the reality of the two correlations represents!
    
    """
    def __init__(self, parentClock, tickRate, correlation1, correlation2, **kwargs):
        """\
        :param parentClock: The parent clock for this clock.
        :param tickRate: The advisory tick rate (ticks per second) for this clock.
        :param correlation1: (tuple(int, int)) The first point of correlation for this clock. A tuple (parent tick value, this clock tick value)
        :param correlation2: (tuple(int, int)) The second point of correlation for this clock. A tuple (parent tick value, this clock tick value)
        """
        super(RangeCorrelatedClock,self).__init__(**kwargs)
        if tickRate <= 0 or not isinstance(tickRate, numbers.Number):
            raise ValueError("Cannot set tickRate to "+repr(tickRate))
        self._parent=parentClock
        self._freq = tickRate
        if not isinstance(correlation1,tuple) or len(correlation1) != 2:
            raise ValueError("correlation1 must be a 2-tuple of tick values")
        if not isinstance(correlation2,tuple) or len(correlation2) != 2:
            raise ValueError("correlations2 must be a 2-tuple of tick values")
        self._correlation1=correlation1
        self._correlation2=correlation2
        parentClock.bind(self)
    
    @property
    def ticks(self):
        return (self._parent.ticks - self._correlation1[0]) * (self._correlation2[1] - self._correlation1[1]) / (self._correlation2[0] - self._correlation1[0]) + self._correlation1[1]
        
    def __repr__(self):
        return "CorrelatedClock(t=%d, freq=%f, correlation=(%d,%d)) at speed=%f" % (self.ticks, self._freq, self._correlation[0], self._correlation[1], self.speed)

    @property
    def tickRate(self):
        """\
        Read the tick rate (in ticks per second) of this clock. The value read is not affected by the value of the :data:`speed` property.
        """
        return self._freq
    
    @property
    def speed(self):
        return 1.0
    

    @property
    def correlation1(self):
        """\
        Read or change the first correlation tuple `(parentTicks, selfTicks)` of this clock to its parent clock.
        
        Assign a new tuple `(parentTicks, selfTicks)` to change the correlation. 
        This value must be a tuple, not a list.
        """
        return self._correlation1
    
    @correlation1.setter
    def correlation1(self,value):
        if not isinstance(value,tuple) or len(value) != 2:
            raise ValueError("Correlation must be a 2-tuple of tick values")
        self._correlation1=value
        self.notify(self)
        
    @property
    def correlation2(self):
        """\
        Read or change the first correlation tuple `(parentTicks, selfTicks)` of this clock to its parent clock.
        
        Assign a new tuple `(parentTicks, selfTicks)` to change the correlation. 
        This value must be a tuple, not a list.
        """
        return self._correlation2
    
    @correlation2.setter
    def correlation2(self,value):
        if not isinstance(value,tuple) or len(value) != 2:
            raise ValueError("Correlation must be a 2-tuple of tick values")
        self._correlation1=value
        self.notify(self)
        

    def calcWhen(self,ticksWhen):
        refticks = self.toParentTicks(ticksWhen)
        return self._parent.calcWhen(refticks)

    def toParentTicks(self, ticks):
        return (ticks - self._correlation1[1]) / (self._correlation2[1] - self._correlation1[1]) * (self._correlation2[0] - self._correlation1[0]) + self._correlation1[0]

    def fromParentTicks(self, ticks):
        return (ticks - self._correlation1[0]) / (self._correlation2[0] - self._correlation1[0]) * (self._correlation2[1] - self._correlation1[1]) + self._correlation1[1]
        
    def getParent(self):
        return self._parent

__all__ = [
    "ClockBase",
    "SysClock",
    "CorrelatedClock",
    "RangeCorrelatedClock",
    "TunableClock",
    "measurePrecision"
]

 
