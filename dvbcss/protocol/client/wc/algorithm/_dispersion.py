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
import logging

from dvbcss.clock import measurePrecision

class LowestDispersionCandidate(object):
    """\
    Algorithm that selects the candidate (request-response measurement result) with the lowest
    dispersion.
    
    Dispersion is a formal measure of the error bounds of the Wall Clock estimate. This value is the sum
    of possible error due to:
    
    * measurement precision limitations (at both client and server) 
    * round-trip time
    * maximum potential for oscillator frequency error at the client and at the server server
      This grows as the candidate (that was used to most recently adjust the clock) ages.
    
     .. note:: The Clock object must be the same one that is provided to the WallClockClient, otherwise
               this algorithm will not synchronise correctly.
    
    The tick rate of the Clock can be any tick rate (it does not have to be one tick per nanosecond),
    but too low a tick rate will limit clock synchronisation precision.
    """
    def __init__(self,clock,repeatSecs=1.0,timeoutSecs=0.2,localMaxFreqErrorPpm=500):
        """\
        *Initialisation takes the following parameters:*
        
        :param clock: A :class:`~dvbcss.clock.TunableClock` object representing that will be adjusted to match the Wall Clock.
        :param repeatSecs: (:class:`float`) The rate at which Wall Clock protocol requests are to be sent (in seconds).
        :param timeoutSecs: (:class:`float`) The timeout on waiting for responses to requests (in seconds).
        :param localMaxFreqErrorPpm: (:class:`float`) The maximum frequency error of the local oscillator that underpins the clock object provided (in ppm).
        """
        super(LowestDispersionCandidate,self).__init__()
        self.log=logging.getLogger("dvbcss.protocol.client.wc.algorithm.BestCandidateByDispersion")
        self.clock = clock
        self.repeatSecs = repeatSecs
        self.timeoutSecs = timeoutSecs
        self.dispCalc = DispersionCalculator(clock, measurePrecision(clock), localMaxFreqErrorPpm)
        
    def getCurrentDispersion(self):
        """\
        :returns: Current dispersion at this moment in time in units of nanoseconds.
        """
        x=self.bestCandidate["nanos"]
        if x is None:
            return (2**64)-1
        else:
            return self.dispCalc.calc(x)
    
    def algorithm(self):
        cumulativeOffset=None
        self.bestCandidate={"nanos":None,"ticks":None}
        while True:
            update=False
            candidate=(yield self.timeoutSecs)
    
            bestDispersion = self.getCurrentDispersion()
    
            if candidate is not None:
                cn=candidate['nanos']
                ct=candidate['ticks']
                dispersion=self.dispCalc.calc(cn)
                
                if bestDispersion >= dispersion:
                    self.bestCandidate = candidate
                    update=True
                    self.clock.adjustTicks(ct.offset)
                    if cumulativeOffset is None:
                        cumulativeOffset=0
                    else:
                        cumulativeOffset+=ct.offset
                else:
                    pass
                self.log.info("Old / New dispersion (millis) is %.5f / %.5f ... offset=%20d  new best candidate? %s\n" % (bestDispersion/1000000.0, dispersion/1000000.0, cumulativeOffset, str(update)))
            else:
                self.log.info("Timeout.  Dispersion (millis) is %.5f\n" % (bestDispersion/1000000.0))
            # retry more quickly if we didn't get an improved candidate
            if update:
                time.sleep(self.repeatSecs)
            else:
                time.sleep(self.timeoutSecs)

   
class DispersionCalculator(object):
    def __init__(self, clock, localPrecisionSecs, localMaxFreqErrorPpm):
        super(DispersionCalculator,self).__init__()
        self.clock = clock
        self.precision = localPrecisionSecs
        self.maxFreqError = localMaxFreqErrorPpm
        
    def calc(self, candidate):
        return 1000000000*(candidate.precision + self.precision) \
             + ( candidate.maxFreqError*(candidate.t3-candidate.t2)    \
               + self.maxFreqError*(candidate.t4-candidate.t1)
               + (candidate.maxFreqError+self.maxFreqError)*(self.clock.nanos - candidate.t4) \
               ) / 1000000 + \
               candidate.rtt/2
               
