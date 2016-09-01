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

import logging
import dvbcss.monotonic_time as time

class MostRecent(object):
    """\
    Simple (naive) Wall Clock client algorithm.
    
    Crash locks the supplied clock based on the offset observed in the
    result of every successful request/response.
    
     .. note:: The Clock object must be the same one that is provided to the WallClockClient, otherwise
               this algorithm will not synchronise correctly.
    
    The tick rate of the Clock can be any tick rate (it does not have to be one tick per nanosecond),
    but too low a tick rate will limit clock synchronisation precision.

    """
    def __init__(self,clock,repeatSecs=1.0,timeoutSecs=0.2):
        """\
        *Initialisation takes the following parameters:*
        
        :param clock: A :class:`~dvbcss.clock.CorrelatedClock` object representing that will be adjusted to match the Wall Clock.
        :param repeatSecs: (:class:`float`) The rate at which Wall Clock protocol requests are to be sent (in seconds).
        :param timeoutSecs: (:class:`float`) The timeout on waiting for responses to requests (in seconds).
        """
        self.log=logging.getLogger("dvbcss.protocol.client.wc.algorithm.MostRecent")
        self.clock = clock
        self.repeatSecs = repeatSecs
        self.timeoutSecs = timeoutSecs
    
    def algorithm(self):
        while True:
            candidate=(yield self.timeoutSecs)
            if candidate is not None:
                self.log.info("Candidate: "+str(candidate)+"\n")
                self.clock.correlation = candidate.calcCorrelationFor(self.clock, 500) # guess as to local max freq error
                time.sleep(self.repeatSecs)
            else:
                self.log.debug("Response timeout\n")
                
    def getCurrentDispersion(self):
        """\
        Calling this method will always result in `ValueError` being raised.
        
        :raises ValueError: This algorithm does not model clock synchronisation accuracy.
        """
        raise ValueError("Unknown")
