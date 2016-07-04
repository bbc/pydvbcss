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

The algorithm object determines when (and how often) a WallClockClient sends CSS-WC protocol requests
and processes the results of requests and responses to adjust the :mod:`~dvbcss.clock` object representing
the Wall Clock.


Dispersion algorithm
~~~~~~~~~~~~~~~~~~~~

The :class:`~dvbcss.protocol.client.wc.algorithm.LowestDispersionCandidate` algorithm is the recommended algorithm.
It uses the candidate with the lowest dispersion.


Simple algorithm
~~~~~~~~~~~~~~~~

The :class:`~dvbcss.protocol.client.wc.algorithm.MostRecent` algorithm is a simple naive algorithm that uses
the most recent candidate irrespective of its quality (e.g. how long the round-trip time of the measurement was)


Writing new algorithms
~~~~~~~~~~~~~~~~~~~~~~

An algorithm is an object that has the following method:

.. method:: .algorithm(self)

    A `python generator <http://www.jeffknupp.com/blog/2013/04/07/improve-your-python-yield-and-generators-explained>`_
    function that yields whenever it wants a Wall Clock protocol measurement to be taken:

    .. code-block:: python

        candidateOrNone = yield timeoutSecs
    
    The yield must pass a timeout in seconds. This is the maximum amount of time the Wall Clock client will
    wait for a response to its request before timing out.
    
    .. versionchanged:: 0.4

        The yield statement will return either :class:`None` or a :class:`~dvbcss.protocol.wc.Candidate` object representing
        the result of the measurement.
    
    The algorithm can then use the Candidate object in its algorithm for estimating the wall clock (and in
    the case of most practical implementations: adjusting a :mod:`~dvbcss.clock` object).

    
Here is an example of a simple naive algorithm that adjusts a :class:`~dvbcss.clock.CorrelatedClock` object
using the most recent measurement, irrespective of influencing factors such as previous measurements or
network latency (round trip time). It makes requests at most once per second and has a timeout on waiting
for responses of 0.5 seconds:

.. code-block:: python

    class NaiveAlgorithm(object):

        def __init__(self,clock):
            self.clock = clock
        
        def algorithm(self):
            while True:
                candidate=(yield 0.5)
                if candidate is not None:
                    self.clock.correlation = candidate.calcCorrelationFor(self.clock)
                    time.sleep(1.0)

    
"""

from dvbcss.protocol.wc import WCMessage, Candidate

from dvbcss.protocol.client.wc.algorithm._dispersion import LowestDispersionCandidate
from dvbcss.protocol.client.wc.algorithm._simple import MostRecent
from dvbcss.protocol.client.wc.algorithm._filterpredict import FilterAndPredict, PredictSimple, FilterRttThreshold, FilterLowestDispersionCandidate

import dvbcss.monotonic_time as time



def algorithmWrapper(dest,measureClock,algorithm):
    """\
    UdpRequestResponseClient handler function that wraps up the act of sending and receiving a WallClockMessage.
    Also handles the optional "follow-up" response type of message. If a response is received that indicates
    a follow-up is due, it will also wait for the follow-up. However the total time it will wait since the
    original request will not exceed the specified timeout. If only a response-promising-follow-up is received
    then that is what shall be returned.
    
    In turn, you plug an algorithm into it that is also a generator function. However that algorithm
    need only yield the timeout, and the return value will be a :class:`~dvbcss.protocol.wc.Candidate`
    object in units of nanoseconds. If timeout occurs the return value is None instead of a dict.
    
    :param dest: ("<ip-addr>",port) The destination address of the server (to which the requests should be sent)
    :param measureClock: The :mod:`~dvbcss:Clock` from which the readings are taken (being `t1` and `t4` in the resulting candidate)
    :param algorithm: A generator that yields to request a WallClock request be sent, and acts on the responses.
    
    The generator function you provide, should use `yield` as follows:
    * to pass the timeout for waiting for a response as the yield value
    * to receive a :class:`~dvbcss.protocol.wc.Candidate` object representing the response.
                
    Example algorithm:
    
    .. code-block:: python
    
      def algorithm():
          timeoutSecs=0.2
          while True:
              candidate=(yield timeoutSecs)
              if candidate is not None:
                  print "Candidate received! ",candidate
              else:
                  print "Timeout"
              print "Now waiting 1 second"
              time.sleep(1)
              
       sysClock = SysClock()
       wallClock = CorrelatedClock(sysClock, tickRate=1000000000)
              
       algWrapper = algorithmWrapper(destIpPort, sysClock, wallClock, algorithm())
       
    """
    try:
        # hand control to the algorithm. when it wants a request sent, it will
        # return and supply the timeout for waiting for a response
        timeoutSecs = algorithm.next()
        while True:
            # assemble a request
            reqMsg=WCMessage(WCMessage.TYPE_REQUEST, 0, 0, measureClock.nanos, 0, 0)
            toSend=reqMsg.pack(), dest
            
            # we'll send the request then seek the best quality response
            # until timeout, or terminating early if we get a quality > 2
            # response (meaning that it was a non-followed-up response or a
            # follow-up response). A lower quality response is one where
            # a follow-up is expected or if it related to a previous request
            
            # this design means it will pick the best response, but in the
            # absence of a reasonable one, it will still make do with whatever
            # it can get (e.g. a response relating to an earlier request)  
             
            responseQuality   = -999
            responseMsg       = None
            responseRecvNanos = None

            timeoutBy     = time.time() + timeoutSecs
            remainingTime = timeoutBy - time.time()

            while responseQuality < 3 and remainingTime > 0:
                # wait for a response. if first time round, send the request too
                latestResponse,src = (yield toSend,remainingTime)
                toSend=None      
                
                # note when response was received
                latestResponseNanos=measureClock.nanos
                
                
                # did we get a response? did it come from the server we sent
                # the request to?
                if latestResponse is not None and src == dest:

                    # assess the response and work out if better than any previous
                    # response we're received
                    latestResponseMsg = WCMessage.unpack(latestResponse)
                    newQuality=calcQuality(reqMsg, latestResponseMsg) 
                    if newQuality >= responseQuality:
                        responseQuality=newQuality
                        responseMsg=latestResponseMsg
                        responseRecvNanos=latestResponseNanos
                        
                # work out how long left until timeout
                remainingTime=timeoutBy - time.time()
                        

            if responseMsg is not None:
                candidate=Candidate(responseMsg,responseRecvNanos)
            else:
                # no message, no candidate
                candidate=None
            # pass the result to the algorithm, and wait for it to return when it
            # next wants a request to be sent (again supplying the response timeout)
            timeoutSecs=algorithm.send(candidate)
    except StopIteration:
        pass


def calcQuality(reqMsg,respMsg):
    """\
    Generate measure of how good the response was. Quality < 0 means response
    corresponded to a different request.
    
    Quality = 3 or 4 means it was a response for which no follow-up is expected
    or a follow-up response.
    
    Quality = 2 means it was a response for which a follow-up is expected
    """
    if reqMsg.originateNanos == respMsg.originateNanos:
        # response corresponds to the request
        offset = 0
    else:
        # penalise because response corresponds to a different (presumably older)
        # request
        offset = -10
        
    if respMsg.msgtype == WCMessage.TYPE_RESPONSE:
        return offset+3
    elif respMsg.msgtype == WCMessage.TYPE_RESPONSE_WITH_FOLLOWUP:
        return offset+2
    elif respMsg.msgtype == WCMessage.TYPE_FOLLOWUP:
        return offset+4



__all__ = [
    "algorithmWrapper",
    "LowestDispersionCandidate",
    "MostRecent",
    "PredictSimple",
    "FilterRttThreshold",
    "FilterAndPredict",
    "FilterLowestDispersionCandidate",
]
