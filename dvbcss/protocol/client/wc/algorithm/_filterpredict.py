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

When using this algorithm, you provide a :class:`~dvbcss.clock.CorrelatedClock` object to it, whose parent is the
clock given to the :class:`~dvbcss.protocol.client.wc.WallClockClient.

This algorithm controls the :class:`~dvbcss.clock.CorrelatedClock` object by settings its
:data:`~dvbcss.clock.CorrelatedClock.correlation` property to (0,offset) where `offset` is provided by the
predictor. The parent of this clock is the clock used by the :class:`~dvbcss.protocol.client.wc.WallClockClient`
in generating the measurement candidates. So the job of the predictor is always to estimate the current absolute
offset between that clock and the wall clock of the server.
    

Here is a simple example that uses a simple predictor and a round-trip-time threshold filter:

.. code-block:: python

    from dvbcss.protocol.wc.algorithm import FilterAndPredict, FilterRttThreshold, PredictSimple
    
    sysClock = SysClock(tickRate=1000000000)
    wallClock = CorrelatedClock(parentClock=sysClock, tickRate=1000000000, correlation=(0,0))
    
    filters = [ FilterRttTreshold(thresholdMillis=10.0) ]
    predictor = PredictSimple()
    
    algorithm = FilterAndPredict(wallClock, repeatSecs, timeoutSecs, filters, predictor)
    
    bind = ("0.0.0.0", 6677)
    server = ("192.168.0.115", 6677)
    
    wc_client=WallClockClient(bind, server, wallClock, algorithm)
    wc_client.start()

.. note:: The Clock object given to the algorithm must be :mod:`~dvbcss.clock.CorrelatedClock`
          whose parent is the clock object provided to the WallClockClient object.
          
          Both clocks must have the same tick rate.


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
most recently provided to it and uses the offset calculated by that candidate as the prediction.


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
            representing the result of the measurement in units of ticks (dict key `"ticks"`) and units
            of nanoseconds (dict key `"nanos"`):
      
      This method is called whenever a measurement candidate resulting from a request-response measurement
      survives the filtering process.
      
  .. method:: .predictOffset(self)
  
      This method must return the difference between the clock used and the server wall clock. The clock used
      by the client is a fixed clock. The difference therefore represents the difference between that clock and
      the Wall Clock on the server.
  
      :return: The offset (in ticks) between the client clock and the wall clock



"""

import logging
import dvbcss.monotonic_time as time

from dvbcss.protocol.client.wc.algorithm import DispersionCalculator

class PredictSimple(object):
    """\
    Simple naive predictor that uses the offset calculated by the most recent candidate.
    """
    def __init__(self):
        self.offset=None
    def addCandidate(self, candidate):
        self.offset=candidate.offset
    def predictOffset(self):
        return self.offset
        
class FilterRttThreshold(object):
    """\
    Simple filter that rejects all candidates where round trip time exceeds a specified threshold.
    """
    def __init__(self, thresholdMillis=1.0):
        """\
        :param thresholdMillis: (:class:`float`) The threshold to use (in milliseconds)
        """
        self.thresholdNanos = thresholdMillis*1000000
    def checkCandidate(self, candidate):
        return candidate.rtt <= self.thresholdNanos
            

class FilterLowestDispersionCandidate(object):
    """\
    Simple filter that will reject a candidate unless its dispersion is lower than any candidate seen
    previously.
    """
    def __init__(self, clock, precisionSecs, maxFreqErrorPpm):
        """\
        :param clock: A :class:`~dvbcss.clock.TunableClock` object representing that will be adjusted to match the Wall Clock.
        :param precisionSecs: (:class:`float`) The measurement precision of the local clock (in units of seconds).
        :param maxFreqErrorPpm: (:class:`float`) The maximum frequency error of the local oscillator that underpins the clock object provided (in ppm).
        """
        self.dispCalc = DispersionCalculator(clock,precisionSecs,maxFreqErrorPpm)
        self.bestCandidate = None
    def checkCandidate(self, candidate):
        if self.bestCandidate is None:
            self.bestCandidate = candidate
            return True
        elif self.dispCalc.calc(self.bestCandidate) > self.dispCalc(candidate):
            self.bestCandidate = candidate
            return True
        else:
            return False
    

def FilterAndPredict(clock,repeatSecs=1.0,timeoutSecs=0.2,filters=[],predictor=PredictSimple()):
    """\
    Combines zero, one or more Filters and a Predictor and returns an algorithm for a WallClockClient.
    
    :param clock: A :class:`~dvbcss.clock.CorrelatedClock` object that will be adjusted to match the Wall Clock.
    :param repeatSecs: (:class:`float`) The rate at which Wall Clock protocol requests are to be sent (in seconds).
    :param timeoutSecs: (:class:`float`) The timeout on waiting for responses to requests (in seconds).
    :param filters: (:class:`list` of Filters) A list of zero, one or more Filters
    :param predictor: (Predictor) The Predictor to use.
    
    :returns: An algorithm object embodying the filtering and prediction process, that is suitable to be passed to a
            :class:`~dvbcss.protocol.client.wc.WallClockClient`.
    
    This algorithm controls the :class:`~dvbcss.clock.CorrelatedClock` object by settings its
    :data:`~dvbcss.clock.CorrelatedClock.correlation` property to (0,offset) where `offset` is provided by the
    predictor. The parent of this clock is the clock used by the :class:`~dvbcss.protocol.client.wc.WallClockClient`
    in generating the measurement candidates. So the job of the predictor is always to estimate the current absolute
    offset between that clock and the wall clock of the server.
    
    Requests are made at the repetition rate specified. If a response is received within the timeout period it
    is then it is transformed into a measurement candidate and passed to the filters.
    Filters are applied in the order you list them. If a candidate survives filtering, then it is passed to the
    predictor. Every time a candidate is provided to the predictor, the offset returned by the predictor replaces
    the previous offset.
    
    .. note:: The Clock object must be :mod:`~dvbcss.clock.CorrelatedClock` whose parent is the clock object
              provided to the WallClockClient object with which this algorithm is used.
              
              *It must not be the same clock object.* However both must have
              the same tick rate. If the same clock object is used or different tick rates are used then
              the Wall Clock will not synchronise correctly..
    
    The tick rate of the Clock can be any tick rate (it does not have to be one tick per nanosecond),
    but too low a tick rate will limit clock synchronisation precision.
    
    
    """
    log=logging.getLogger("dvbcss.protocol.client.wc.algorithm.FilterAndPredict")
    prevOffset=0
    while True:
        candidate=(yield timeoutSecs)
        if candidate is not None:
            
            # apply filters
            if None in [f.checkCandidate(candidate['nanos']) for f in filters]:
                log.debug("Candidate filtered out\n")
                time.sleep(repeatSecs)
            else:
                
                # filters passed, so now feed the candidate into the predictor
                # and retrieve a new estimate of the offset
                predictor.addCandidate(candidate['nanos'])
                offsetNanos=predictor.predictOffset()
                offsetTicks=round(offsetNanos * clock.tickRate / 1000000000.0)

                # act on it
                log.debug("Candidate accepted. Predicted offset (ticks)=%20d   delta (ticks)=%20d\n" % (offsetTicks, offsetTicks-prevOffset))
                clock.correlation=(0,offsetTicks)
                prevOffset=offsetTicks

                time.sleep(repeatSecs)
        else:
            log.debug("Response timeout\n")
                

