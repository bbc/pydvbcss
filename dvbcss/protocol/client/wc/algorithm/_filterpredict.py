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

"""\
Composable Filter and prediction algorithm
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

There is also a simple modular framework for building up an algorithm out of two parts:

* *Filters* - processes measurement candidates, determining whether to reject them.
* *A Predictor* - takes the measurement candidates outputted from the filtering step and use them to adjust the clock.

Use the :func:`~dvbcss.protocol.client.wc.algorithm.FilterAndPredict` function to compose zero, one or more Filters,
and a Predictor into an algorithm that can be used with a :class:`~dvbcss.protocol.client.wc.WallClockClient`.

.. versionchanged:: 0.4

    When using this algorithm, you provide a :class:`~dvbcss.clock.CorrelatedClock` object to it, whose parent is the
    clock given to the :class:`~dvbcss.protocol.client.wc.WallClockClient`.
    This algorithm controls the :class:`~dvbcss.clock.CorrelatedClock` object by settings its
    :data:`~dvbcss.clock.CorrelatedClock.correlation` property to that returned by the
    predictor. The parent of this clock is the clock used by the :class:`~dvbcss.protocol.client.wc.WallClockClient`
    in generating the measurement candidates. So the job of the predictor is to
    determine the best correlation for modelling the relationship between that
    (parent) clock and the wall clock of the server.
    

Here is a simple example that uses a simple predictor and a round-trip-time threshold filter:

.. code-block:: python

    from dvbcss.clock import CorrelatedClock, SysClock
    from dvbcss.protocol.client.wc.algorithm import FilterAndPredict, FilterRttThreshold, PredictSimple
    from dvbcss.protocol.client.wc import WallClockClient
    
    sysClock = SysClock(tickRate=1000000000)
    wallClock = CorrelatedClock(parentClock=sysClock, tickRate=1000000000)
    
    filters = [ FilterRttThreshold(thresholdMillis=10.0) ]
    predictor = PredictSimple(wallClock)
    
    algorithm = FilterAndPredict(wallClock, repeatSecs, timeoutSecs, filters, predictor)
    
    bind = ("0.0.0.0", 6677)
    server = ("192.168.0.115", 6677)
    
    wc_client=WallClockClient(bind, server, wallClock, algorithm)
    wc_client.start()

The Clock object given to the algorithm must be :mod:`~dvbcss.clock.CorrelatedClock`
whose parent is the clock object provided to the WallClockClient object.


Round-trip time threshold Filter
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The :class:`~dvbcss.protocol.client.wc.algorithm.FilterRttThreshold` class implements a filter that eliminates any candidate
where the round-trip time exceeds a threshold.

Lowest dispersion candidate filter
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The :class:`~dvbcss.protocol.client.wc.algorithm.FilterLowestDispersionCandidate` class implements a filter that eliminates
any candidate if it does not have a lower dispersion that any candidate that came before it.


Simple Predictor
^^^^^^^^^^^^^^^^

The :class:`~dvbcss.protocol.client.wc.algorithm.PredictSimple` class is a simple predictor that uses the candidate
most recently provided to it and directly transforms that into a :class:`dvbcss.clock.Correlation`.


Writing your own Filter
^^^^^^^^^^^^^^^^^^^^^^^

You can write your own Filter by creating a class with the following method defined:

  .. method:: .checkCandidate(self, candidate)
  
      :param candidate: A (:class:`dict`)  containing two :class:`~dvbcss.protocol.wc.Candidate` objects
            representing the result of the measurement in units of ticks (dict key `"ticks"`) and units
            of nanoseconds (dict key `"nanos"`):



Writing your own Predictor
^^^^^^^^^^^^^^^^^^^^^^^^^^

You can write your own Predictor by creating a class with the following methods defined:

    .. method:: .addCandidate(self, candidate)
      
        :param candidate: A (:class:`dict`)  containing two :class:`~dvbcss.protocol.wc.Candidate` objects
            representing the result of the measurement in units of of nanoseconds.
      
      This method is called whenever a measurement candidate resulting from a request-response measurement
      survives the filtering process.
      
  .. method:: .predictCorrelation(self)
  
      :return: A :class:`~dvbcss.clock.Correlation`
      
      The returned Correlation must represent the relationship between the
      clock and its parent, such that the clock becomes an estimate of the
      server's Wall Clock. This must be in the correct units (tick rate)
      for the clock and its parent.



"""

import logging
import dvbcss.monotonic_time as time

from dvbcss.clock import CorrelatedClock, Correlation

class PredictSimple(object):
    """\
    Simple naive predictor that chooses the correlation represented by the most recent candidate
    """
    def __init__(self, clock):
        """\
        :param clock: The :class:`~dvbcss.clock.CorrelatedClock` that is to be set.
        
        Note that this predictor does not actually set the clock. It just needs it in order to calculate the correct correlation for it.
        """
        self.clock = clock
        self.correlation = Correlation(0,0,0,float("+inf"))
    def addCandidate(self, candidate):
        self.correlation = candidate.calcCorrelationFor(self.clock)
    def predictCorrelation(self):
        return self.correlation
        
class FilterRttThreshold(object):
    """\
    Simple filter that rejects all candidates where round trip time exceeds a specified threshold.
    """
    def __init__(self, thresholdMillis=1.0):
        """\
        :param thresholdMillis: (:class:`float`) The threshold to use (in milliseconds)
        """
        self.thresholdSecs = thresholdMillis/1000
    def checkCandidate(self, candidate):
        return candidate.rtt <= self.thresholdSecs
            

class FilterLowestDispersionCandidate(object):
    """\
    Simple filter that will reject a candidate unless its dispersion is lower than that currently
    being used by the clock.
    
    Note that at initialisation, the clock's dispersion is forced to +infinity.
    """
    def __init__(self, clock):
        """\
        :param clock: A :class:`~dvbcss.clock.CorrelatedClock` object representing that will be adjusted to match the Wall Clock.
        """
        self.clock = clock
        self.clock.correlation = clock.correlation.butWith(initialError=float("+inf"))
        self.tmpClock = CorrelatedClock(self.clock.getParent(), self.clock.tickRate)
    def checkCandidate(self, candidate):
        self.tmpClock.correlation = candidate.calcCorrelationFor(self.clock)
        t = self.clock.ticks
        if self.clock.dispersionAtTime(t) > self.tmpClock.dispersionAtTime(t):
            return True
        else:
            return False
    

class FilterAndPredict(object):
    """\
    Combines zero, one or more Filters and a Predictor and returns an algorithm for a WallClockClient.
    
    :param clock: A :class:`~dvbcss.clock.CorrelatedClock` object that will be adjusted to match the Wall Clock.
    :param repeatSecs: (:class:`float`) The rate at which Wall Clock protocol requests are to be sent (in seconds).
    :param timeoutSecs: (:class:`float`) The timeout on waiting for responses to requests (in seconds).
    :param filters: (:class:`list` of Filters) A list of zero, one or more Filters
    :param predictor: (Predictor) The Predictor to use, or None to default to :class:`PredictSimple`
    
    This algorithm controls the :class:`~dvbcss.clock.CorrelatedClock` object by settings its
    :data:`~dvbcss.clock.CorrelatedClock.correlation` property to that provided by the
    predictor.
    
    The parent of this `clock` is the clock used by the :class:`~dvbcss.protocol.client.wc.WallClockClient`
    in generating the measurement candidates. So the job of the predictor is always to estimate the 
    :class:`~dvbcss.clock.Correlation` needed by the `clock`.
    
    Requests are made at the repetition rate specified. If a response is received within the timeout period it
    is then it is transformed into a measurement candidate and passed to the filters.
    Filters are applied in the order you list them. If a candidate survives filtering, then it is passed to the
    predictor. Every time a candidate is provided to the predictor, the correlation returned by the predictor replaces
    the previous correlation.
    
    .. note:: The Clock object must be :mod:`~dvbcss.clock.CorrelatedClock` whose parent is the clock object
              that is measured when generating the candidates.
    
    The tick rate of the Clock can be any tick rate (it does not have to be one tick per nanosecond),
    but too low a tick rate will limit clock synchronisation precision.
    
    
    """
    def __init__(self,clock,repeatSecs=1.0,timeoutSecs=0.2,filters=[],predictor=None):
        self.clock = clock
        self.repeatSecs = repeatSecs
        self.timeoutSecs = timeoutSecs
        self.filters = filters
        if predictor is None:
            self.predictor = PredictSimple(clock)
        else:
            self.predictor = predictor
        self.log=logging.getLogger("dvbcss.protocol.client.wc.algorithm.FilterAndPredict")

    def onClockAdjusted(self, timeAfterAdjustment, adjustment, oldDispersionNanos, newDispersionNanos, dispersionGrowthRate):
        """\
        This method is called immediately after a clock adjustment has been made,
        and gives details on how the clock was changed and the effect on the dispersion.
        
        :param timeAfterAdjustment: The wall clock time (in ticks) immedaitely after the adjustment took place
        :param adjustment: The amount by which the wall clock instaneously changed (in ticks)
        :param oldDispersionNanos: The dispersion (in nanoseconds) just prior to adjustment
        :param newDispersionNanos: The dispersion (in nanoseconds) immediately after adjustment
        :param dispersionGrowthRate: The rate at which dispersion will continue to grow.
        
        To calculate a future dispersion at time T:
            futureDispersion = newDispersionNanos + (t-timeOfAdjustment) * dispersionGrowthRate
            
        |stub-method|
        """
        pass
        
    def getCurrentDispersion(self):
        """\
        :returns: Current dispersion at this moment in time in units of nanoseconds.
        """
        return self.clock.dispersionAtTime(self.clock.ticks)*1000000000
    


    def algorithm(self):
        while True:
            candidate=(yield self.timeoutSecs)
            if candidate is not None:
                
                # apply filters
                if None in [f.checkCandidate(candidate) for f in self.filters]:
                    self.log.debug("Candidate filtered out\n")
                    time.sleep(self.repeatSecs)
                else:
                    
                    # filters passed, so now feed the candidate into the predictor
                    # and retrieve a new estimate of the correlation
                    self.predictor.addCandidate(candidate)
                    self.clock.correlation = self.predictor.predictCorrelation()

                    # act on it
                    self.log.debug("Candidate accepted. New Correlation = ", self.clock.correlation)

                    time.sleep(self.repeatSecs)
            else:
                self.log.debug("Response timeout\n")
                

