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



Accounting for error (dispersion)
---------------------------------

These clocks also support tracking and calculating error bounds on the values
they report. This is known as dispersion. It is useful if, for example, a clock
hierarchy is being used to estimate time based on imperfect measurements - such
as when a companion tries to estimate the Wall Clock of a TV.

Each clock in a hierarchy makes its own contribution to the overall dispersion.
When a clock is asked to calculate dispersion (using the :func:`dispersionAtTime`
method), the answer it gives is the sum of the error contributions from itself
and its parents, all the way back up to the root system clock.

A system clock has error bounds determined by the precision with which it can be measured (the smallest amount by which its values change).

When using a dependent clock, such as a :class:`CorrelatedClock`, the
correlation being used to set its relationship to its parent might also have some uncertainty in it. This information can be included in the :class:`Correlation`.
Uncertainty based on measurements/estimates can grow over time - e.g. because
the clocks in a TV and companion gradually drift. So there are two parameters
that you can provide in a :class:`Correlation` - the *initial error* and the
*growth rate*. As time passes, the error for the clock using this correlation
is calculated as the initial error plus the growth rate multiplied by how much
time has passed since the point of correlation.


Usage examples
--------------

Simple hierarchies of clocks
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Here is a simple example where a clock represents a timeline and
another represents a timeline related to the first by a correlation:

.. code-block:: python

    from dvbcss.clock import SysClock
    from dvbcss.clock import CorrelatedClock
    from dvbcss.clock import Correlation
    
    # create a clock based on dvbcss.monotonic_time.time() that ticks in milliseconds
    sysClock = SysClock(tickRate=1000)
    
    # create a clock to represent a timeline 
    corr = Correlation(parentTicks=0, childTicks=0)
    baseTimeline = CorrelatedClock(parentClock=sysClock, tickRate=25, correlation=corr)
    
    # create a clock representing another timeline, where time zero corresponds to time 100
    # on the parent timeline
    corr2 = Correlation(parentTicks=100, childTicks=0)
    subTimeline = CorrelatedClock(parentClock=baseTimeline, tickRate=25, correlation=corr2)
    
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
    
    >>> baseTimeline.correlation = Correlation(0,25)
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
    from dvbcss.clock import Correlation
    
    # create a clock based on dvbcss.monotonic_time.time() that ticks in milliseconds
    sysClock = SysClock(tickRate=1000)
    
    #                                       +------------+
    #                                   .-- | mediaClock |
    # +----------+     +-----------+ <--'   +------------+
    # | sysClock | <-- | wallClock | 
    # +----------+     +-----------+ <--.   +-----------------+
    #                                   '-- | otherMediaClock |
    #                                       +-----------------+

    wallClock = CorrelatedClock(parentClock=sysClock, tickRate=1000000000, correlation=Correlation(0,0))
    mediaClock = CorrelatedClock(parentClock=wallClock, tickRate=25, correlation=Correlation(500021256, 0))
    otherMediaClock = CorrelatedClock(parentClock=wallClock, tickRate=30, correlation=Correlation(21093757, 0))
    
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


Let us now suppose that the wall clock is actually an estimate of a Wall Clock
on another device. When we set the correlation we therefore include error
information that is calculated from the proces by which the Wall Clock of the
other device is estimated:

.. code-block:: python

    wallClock.correlation = Correlation(24524535, 34342, initialError=0.012, errorGrowthRate=0.00005)

Here we are saying that the error bounds of the estimate at the point in time
represented by the correlation is +/- 0.012 seconds. This will grow by 0.00005
seconds for every tick of the parent clock.

.. code-block:: python

    print "Dispersion is +/-", wallClock.dispersionAtTime(wallClock.ticks), "seconds"
    
    print "In 1000 ticks from now, dispersion will be +/-", wallClock.dispersionAtTime(wallClock.ticks + 1000), "seconds"



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

        def _errorAtTime(self,t):
            return 0

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
        self._availability = True
        
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
            clock = clock.getParent()
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

    def isAvailable(self):
        """\
        Returns whether this clock is available, taking into account the availability of any (parent) clocks on which it depends.
        
        :returns: True if available, otherwise False.
        """
        parent = self.getParent()
        return self._availability and (parent is None or parent.isAvailable())
        
    def setAvailability(self, availability):
        """\
        Set the availability of this clock.
        
        :param availability: True if this clock is available, otherwise False.
        
        If setting the availability of this clock changes the overall availability of this clock (as returned by :func:`isAvailable`) then
        dependents will be notified of the change.
        """
        isChange = self._availability != availability
        parent = self.getParent()
        if parent is not None:
            isChange = isChange and parent.isAvailable()
        
        self._availability = availability
        
        if isChange:
            self.notify(self)

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
        
    def getRoot(self):
        """\
        :return: The root clock for this clock (or itself it has no parent).
        """
        p=self
        p2=p.getParent()
        while p2:
            p=p2
            p2=p.getParent() 
        return p
        
    def fromRootTicks(self, t):
        """\
        Return the time for this clock corresponding to a given time of the root clock.
        
        :param t: Tick value of the root clock.
        :returns: Corresponding tick value of this clock.
        """
        p=self.getParent()
        if p is None:
            return t
        else:
            x = p.fromRootTicks(t)
            return self.fromParentTicks(x)
            
    def toRootTicks(self, t):
        """\
        Return the time for the root clock corresponding to a given time of this clock.
        
        :param t: Tick value for this clock.
        :returns: Corresponding tick value of the root clock.
        """
        p=self.getParent()
        if p is None:
            return t
        else:
            x = self.toParentTicks(t)
            return p.toRootTicks(x)
    
    def toOtherClockTicks(self, otherClock, ticks):
        """\
        Converts a tick value for this clock into a tick value corresponding to the timescale of another clock.
        
        :param otherClock: A :class:`~dvbcss.clock` object representing another clock.
        :param ticks: A time (tick value) for this clock
        
        :returns: The tick value of the `otherClock` that represents the same moment in time.
        
        :throws NoCommonClock: if there is no common ancestor clock (meaning it is not possible to convert
        """
        # establish the ancestry of both clocks up to a root
        selfAncestry = self.getAncestry()
        otherAncestry = otherClock.getAncestry()
        
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
        
        
    def getAncestry(self):
        """\
        Retrieve the ancestry of this clock as a list.
        
        :returns: A list of clocks, starting with this clock, and proceeding to its parent, then its parent's parent etc, ending at the root clock.
        """
        ancestry = [self]
        for c in ancestry:
            p=c.getParent()
            if p is not None:
                ancestry.append(p)
        return ancestry
        
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
        
    def clockDiff(self, otherClock):
        """\
        Calculate the potential for difference between this clock and another clock.
        
        :param otherClock: The clock to compare with.
        :returns: The potential difference in units of seconds. If effective speeds or  tick rates differ, this will always be :class:`float` ("+inf").
        
        If the clocks differ in effective speed or tick rate, even slightly, then this
        means that the clocks will eventually diverge to infinity, and so the returned 
        difference will equal +infinity.
        """
        thisSpeed = self.getEffectiveSpeed()
        otherSpeed = otherClock.getEffectiveSpeed()
        
        if thisSpeed != otherSpeed:
            return float('inf')
        elif self.tickRate != otherClock.tickRate:
            return float('inf')
        else:
            root = self.getRoot()
            t = root.ticks
            t1 = self.fromRootTicks(t)
            t2 = otherClock.fromRootTicks(t)
            return abs(t1-t2) / self.tickRate
    
    def dispersionAtTime(self, t):
        """\
        Calculates the dispersion (maximum error bounds) at the specified
        clock time. This takes into account the contribution to error of this
        clock and its ancestors.
        
        :returns: Dispersion (in seconds) at the specified clock time.
        """
        disp = self._errorAtTime(t)
        
        p = self.getParent()
        if p is not None:
            pt = self.toParentTicks(t)
            disp += p.dispersionAtTime(pt)
        
        return disp
    
    def _errorAtTime(self, t):
        """\
        |stub-method|
        
        :param t: Time of this clock.

        :returns: the potential for error (in seconds) arising from this clock
        at a given time of this clock. Does not include the contribution of
        any parent clocks.
        
        This is an internal method that is used by :func:`dispersionAtTime`.
        """
        raise NotImplemented

    def getRootMaxFreqError(self):
        """\
        Return potential error of underlying clock (e.g. system clock).
        
        :returns: The maximum potential frequency error (in parts-per-million) of the underlying root clock.
        
        *This is a partial stub method. It must be re-implemented by root clocks.*
        
        For a clock that is not the root clock, this method will pass through
        the call to the same method of the root clock.
        """
        root = self.getRoot()
        if root == self:
            raise NotImplemented
        else:
            return self.getRoot().getRootMaxFreqErrPpm()



@dvbcss._inheritDocs(ClockBase)
class SysClock(ClockBase):
    """\
    A clock based directly on the standard library timer function :func:`monotonic_time.time`.
    Returns `integer` ticks when its :data:`ticks` property is queried.
    
    The default tick rate is 1 million ticks per second, but a different tick rate can be chosen during initialisation.
    
    :param tickRate: Optional (default=1000000). The tick rate of this clock (ticks per second).
    :param maxFreqErrorPpm: Optional (default=500). The maximum frequency error (in units of parts-per-million) of the clock, or an educated best-estimate of it.
    
    The precision is automatically estimated using the :func:`measurePrecision`
    function when this clock is created. So creating a SysClock, particularly
    one with a low tickrate, may incur a noticeable delay at initialisation.
    
    The measured precision is then reported as the dispersion of this clock.
    
    It is not permitted to change the :data:`tickRate` or :data:`speed` property of this clock because it directly represents a system clock.
    """
    
    def __init__(self,tickRate=1000000, maxFreqErrorPpm=500, **kwargs):
        """\
        :param tickRate: (int) tick rate for this clock (in ticks per second)
        """
        super(SysClock,self).__init__(**kwargs)
        if tickRate <= 0 or not isinstance(tickRate, numbers.Number):
            raise ValueError("Cannot set tickRate to "+repr(tickRate))
        self._freq = tickRate
        s = min(10000,max(10,tickRate/10))
        self._precision = measurePrecision(self, sampleSize=s)
        self._maxFreqErrorPpm = maxFreqErrorPpm
        
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
    
    def setAvailability(self, availability):
        """\
        SysClock is always available, and so availability cannot be set.
        
        :raise NotImplementedError: Always raised.
        """
        raise NotImplementedError("Changing availability is not supported for this clock.")

    def _errorAtTime(self, t):
        """\
        :returns: The precision of the clock
        """
        return self._precision

    def getRootMaxFreqError(self):
        return self._maxFreqErrorPpm


class Correlation(object):
    r"""\
    Immutable object representing a correlation. This can also optionally include bounds
    for the potential for error if the correlation is used to model a clock.
    
    The correlation (`parentTicks`, `ticks`) represents a relationship between
    a (child) clock and its parent. The time `parentTicks` of the parent
    corresponds to the time `ticks` of the child.
    
    :param parentTicks: Time of the parent clock.
    :param childTcks: Corresponding time of the clock using this correlation.
    :param initialError: Optional (default=0). The amount of potential error (in seconds) at the moment represented by the correlation. 
    :param errorGrowthRate: Optional (default=0). The amount that the potential for error will grow by for every tick of the parent clock.

    This class is intended to be immutable. Instead of modifying a correlation,
    create a new one based on an existing one. The :func:`butWith` method is
    designed to assist with this.
    """
    def __init__(self, parentTicks, childTicks, initialError=0, errorGrowthRate=0):
        super(Correlation,self).__init__()
        self._parentTicks = parentTicks 
        self._childTicks = childTicks
        self._initialError = initialError
        self._errorGrowthRate = errorGrowthRate
    
    def butWith(self, parentTicks=None, childTicks=None, initialError=None, errorGrowthRate=None):
        """\
        Return a new correlation the same as this one but with the specified changes.
        
        :param parentTicks: Optional. A new Time of the parent clock.
        :param childTcks: Optional. The corresponding time of the clock using this correlation.
        :param initialError: Optional. The amount of potential error (in seconds) at the moment represented by the correlation. 
        :param errorGrowthRate: Optional. The amount that the potential for error will grow by for every tick of the parent clock.
        
        :returns: New :class:`Correlation` based on this one, but with the changes specified by the parameters.
        
        If a parameter is set to `None` or not provided, then the existing value
        is taken from this correlation object.
        """
        if parentTicks is None:
            parentTicks = self.parentTicks
        if childTicks is None:
            childTicks = self.childTicks
        if initialError is None:
            initialError = self.initialError
        if errorGrowthRate is None:
            errorGrowthRate = self.errorGrowthRate
        return Correlation(parentTicks, childTicks, initialError, errorGrowthRate)

    @property
    def parentTicks(self):
        """\
        Number representing a time of the parent clock.
        """
        return self._parentTicks

    @property
    def childTicks(self):
        """\
        Number representing a time of the child clock, that corresponds to the `parentTicks` time of the parent clock.
        """
        return self._childTicks

    @property
    def initialError(self):
        """\
        Number representing the amount of potential error (in units of seconds) at the moment represented by the correlation. Default value is 0 if not set.
        """
        return self._initialError

    @property
    def errorGrowthRate(self):
        """\
        Number representing the amount that the potential for error will grow by
        (in units of seconds) for every tick of the parent clock. Default value is 0 if not set.
        """
        return self._errorGrowthRate

    def calcErrorAtParentTicks(self, pt):
        """\
        Returns the error at a given parent clock time.
        
        :param pt: Time of the parent clock
        :returns: Error attributable to this correlation
        """
        delta = pt - self._parentTicks
        return self._initialError + delta * self._errorGrowthRate
        
        
    def __str__(self):
        return "Correlation(%s, %s, %s, %s)" %\
            (str(self._parentTicks), str(self._childTicks), str(self._initialError), str(self._errorGrowthRate))
    
    def __repr__(self):
        return "Correlation(parentTicks=%s, childticks=%s, initialError=%s, errorGrowthRate=%s)" %\
            (repr(self._parentTicks), repr(self._childTicks), repr(self._initialError), repr(self._errorGrowthRate))
            
    def __eq__(self, obj):
        if isinstance(obj, Correlation):
            return obj._parentTicks == self._parentTicks \
                and obj._childTicks == self._childTicks \
                and obj._initialError == self._initialError \
                and obj._errorGrowthRate == self._errorGrowthRate
        else:
            return False

@dvbcss._inheritDocs(ClockBase)
class CorrelatedClock(ClockBase):
    r"""\
    A clock locked to the tick count of the parent clock by a correlation and frequency setting.
    
    Correlation is either a :class:`Correlation` object or a simple tuple
    `(parentTicks, selfTicks)`. The object form also allows you to specify error
    bounds information that this clock will track and propagate to other clocks.
    
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
        c.correlation = Correlation( parent.ticks, c.ticks )
        c.speed = 0.5
    
    .. note::
    
       The maths to calculate and convert tick values will be performed, by default, as integer maths
       unless the parameters controlling the clock (tickRate etc) are floating point, or the ticks property
       of the parent clock supplies floating point values.
    
    """
    
    def __init__(self, parentClock, tickRate, correlation=Correlation(0,0), **kwargs):
        """\
        :param parentClock: The parent clock for this clock.
        :param tickRate: (int) tick rate for this clock (in ticks per second)
        :param correlation: (:class:`Correlation`) The intial correlation for this clock.
        
        """
        super(CorrelatedClock,self).__init__(**kwargs)
        if tickRate <= 0 or not isinstance(tickRate, numbers.Number):
            raise ValueError("Cannot set tickRate to "+repr(tickRate))
        self._freq = tickRate
        self._parent=parentClock
        self._speed = 1.0
        self._correlation=correlation
        parentClock.bind(self)
    
    @property
    def ticks(self):
        return self._correlation.childTicks + (self._parent.ticks - self._correlation.parentTicks)*self._freq*self.speed/self._parent.tickRate
        
    def __repr__(self):
        return "CorrelatedClock(t=%d, freq=%f, correlation=%s) at speed=%f" % (self.ticks, self._freq, str(self._correlation), self.speed)

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
        initError = self._correlation.calcErrorAtParentTicks(parentTickValue)

        self._correlation = self._correlation.butWith( \
            parentTicks = parentTickValue, \
            childTicks = tickValue, \
            initialError = initError
            )
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
        self._correlation=value
        self.notify(self)
        
    def setCorrelationAndSpeed(self, newCorrelation, newSpeed):
        """\
        Set both the correlation and the speed to new values in a single operation. Generates a single notification for descendents as a result.
        
        :param newCorrelation: A :class:`Correlation` representing the new correlation. Must be a tuple. Not a list.
        :param newSpeed: New speed as a :class:`float`. 
        """
        self._correlation = newCorrelation
        self._speed = float(newSpeed)
        self.notify(self)
        
    def calcWhen(self,ticksWhen):
        if self.speed == 0:
            refticks=self._correlation.parentTicks   # return any arbitrary position if the speed of this clock is zero (pause)
        else:
            refticks=self._correlation.parentTicks + (ticksWhen - self._correlation.childTicks)*self._parent.tickRate/self._freq/self.speed
        return self._parent.calcWhen(refticks)

    def toParentTicks(self, ticks):
        if self.speed == 0:
            return self._correlation.parentTicks   # return any arbitrary position if the speed of this clock is zero (pause)
        else:
            return self._correlation.parentTicks + (ticks - self._correlation.childTicks)*self._parent.tickRate/self._freq/self.speed

    def fromParentTicks(self, ticks):
        return self._correlation.childTicks + (ticks - self._correlation.parentTicks)*self._freq*self.speed/self._parent.tickRate
    
    def getParent(self):
        return self._parent
    
    def quantifyChange(self, newCorrelation, newSpeed):
        """\
        Calculate the potential for difference in tick values of this clock if a different correlation and speed were to be used.

        :param newCorrelation: A :class:`Correlation`
        :param newSpeed: New speed as a :class:`float`. 
        :returns: The potential difference in units of seconds. If speeds differ, this will always be :class:`float` ("+inf").
        
        If the new speed is different, even slightly, then this means that the ticks reported by this clock will eventually differ by infinity,
        and so the returned value will equal +infinity. If the speed is unchanged then the returned value reflects the difference between
        old and new correlations.
        """
        if newSpeed != self._speed:
            return float('inf')
        else:
            nx, nt = newCorrelation.parentTicks, newCorrelation.childTicks
            if newSpeed != 0:
                ox = self.toParentTicks(nt)
                return abs(nx-ox) / self.getParent().tickRate
            else:
                ot = self.fromParentTicks(nx)
                return abs(nt-ot) / self.tickRate

    def isChangeSignificant(self, newCorrelation, newSpeed, thresholdSecs):
        """\
        Returns True if the potential for difference in tick values of this clock (using a new correlation and speed) exceeds a specified threshold.
        
        :param newCorrelation: A :class:`Correlation`
        :param newSpeed: New speed as a :class:`float`. 
        :returns: True if the potential difference can/will eventually exceed the threshold.

        This is implemented by applying a threshold to the output of :func:`quantifyChange`.
        """
        delta = self.quantifyChange(newCorrelation, newSpeed)
        return delta > thresholdSecs

    def _errorAtTime(self, t):
        return self._correlation.calcErrorAtParentTicks(self.toParentTicks(t))



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
        self._baseErr = 0
        self._baseErrParentTime = self._last
        self._errGrowthRate = 0
            
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
        
    def setError(self, current, growthRate=0):
        """\
        Set the current error bounds of this clock and the rate at which it grows
        per tick of the parent clock.
        
        :param current: Potential error (in seconds) of the clock at this time.
        :param growthRate: Amount by which error will grow for every tick of the parent clock.
        """
        self._baseErr = current
        self._baseErrParentTime = self.getParent().ticks
        self._errGrowthRate = growthRate
        
    def _errorAtTime(self, f):
        tDelta = self.getParent().ticks - self._baseErrParentTime
        growth = abs(tDelta) * self._errGrowthRate
        return self._baseErr + growth
        


@dvbcss._inheritDocs(ClockBase)
class RangeCorrelatedClock(ClockBase):
    r"""\
    A clock locked to the tick count of the parent clock by two different points of correlation.
    
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
        :param correlation1: (:class:`Correlation`) The first point of correlation for this clock.
        :param correlation2: (:class:`Correlation`) The second point of correlation for this clock.
        """
        super(RangeCorrelatedClock,self).__init__(**kwargs)
        if tickRate <= 0 or not isinstance(tickRate, numbers.Number):
            raise ValueError("Cannot set tickRate to "+repr(tickRate))
        self._parent=parentClock
        self._freq = tickRate
        self._correlation1=correlation1
        self._correlation2=correlation2
        parentClock.bind(self)
    
    @property
    def ticks(self):
        return (self._parent.ticks - self._correlation1.parentTicks) * (self._correlation2.childTicks - self._correlation1.childTicks) / (self._correlation2.parentTicks - self._correlation1.parentTicks) + self._correlation1.childTicks
        
    def __repr__(self):
        return "CorrelatedClock(t=%d, freq=%f, correlation=(%d,%d)) at speed=%f" % (self.ticks, self._freq, self._correlation.parentTicks, self._correlation.childTicks, self.speed)

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
        Read or change the first correlation of this clock to its parent clock.
        
        Assign a new :class:`Correlation` to change the correlation. 
        """
        return self._correlation1
    
    @correlation1.setter
    def correlation1(self,value):
        self._correlation1=value
        self.notify(self)
        
    @property
    def correlation2(self):
        """\
        Read or change the first correlation of this clock to its parent clock.
        
        Assign a new :class:`Correlation` to change the correlation. 
        """
        return self._correlation2
    
    @correlation2.setter
    def correlation2(self,value):
        self._correlation2=value
        self.notify(self)
        

    def calcWhen(self,ticksWhen):
        refticks = self.toParentTicks(ticksWhen)
        return self._parent.calcWhen(refticks)

    def toParentTicks(self, ticks):
        return (ticks - self._correlation1.childTicks) / (self._correlation2.childTicks - self._correlation1.childTicks) * (self._correlation2.parentTicks - self._correlation1.parentTicks) + self._correlation1.parentTicks

    def fromParentTicks(self, ticks):
        return (ticks - self._correlation1.parentTicks) / (self._correlation2.parentTicks - self._correlation1.parentTicks) * (self._correlation2.childTicks - self._correlation1.childTicks) + self._correlation1.childTicks
        
    def getParent(self):
        return self._parent

    def _errorAtTime(self, t):
        pt = self.toParentTicks(t)
        c1err = self._correlation1.calcErrorAtParentTicks(pt)
        c2err = self._correlation2.calcErrorAtParentTicks(pt)
        return min(c1err, c2err)


__all__ = [
    "ClockBase",
    "SysClock",
    "Correlation",
    "CorrelatedClock",
    "RangeCorrelatedClock",
    "TunableClock",
    "measurePrecision"
]

 
