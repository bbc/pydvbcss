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
The :class:`~dvbcss.protocol.client.wc.WallClockClient` class provides a complete Wall Clock Client implementation.
It is used in conjunction with an :ref:`algorithm <algorithms>` for adjusting a :mod:`~dvbcss.clock` object
so that it mirrors the server's Wall Clock.


Using a Wall Clock Client
-------------------------

Recommended simplest use is to instantiate a :class:`~dvbcss.protocol.client.wc.WallClockClient` and provide it with an
instance of the :class:`~dvbcss.protocol.client.wc.algorithm.LowestDispersionCandidate` algorithm to control how it updates a clock.

A simple example that connects to a wall clock server at 192.168.0.115 port 6677 and sends requests once per second:

.. code-block:: python

    from dvbcss.clock import SysClock as SysClock
    from dvbcss.protocol.client.wc import WallClockClient
    from dvbcss.protocol.client.wc.algorithm import LowestDispersionCandidate
    
    sysClock=SysClock()
    wallClock=CorrelatedClock(sysClock,tickRate=1000000000)
    
    algorithm = LowestDispersionCandidate(wallClock,repeatSecs=1,timeoutSecs=0.5)
    
    bind = ("0.0.0.0", 6677)
    server = ("192.168.0.115", 6677)
    
    wc_client=WallClockClient(bind, server, wallClock, algorithm)
    wc_client.start()

    # wall clock client is now running in the background


After the :func:`~WallClockClient.start` method is called, the WallClockClient
runs in a separate thread and execution continues.

:class:`WallClockClient` is used by providing it with an object implementing the clock
synchronisation :ref:`algorithm <algorithms>`. The Wall Clock client handles the
protocol interaction (sending the requests and parsing the responses) at the times
specified by the algorithm and passes the results of each request-response measurement
(a :class:`~dvbcss.protocol.wc.Candidate`) to the algorithm. The algorithm then
adjusts the clock.

.. image:: wc-client-clock-model.png
       :width: 384pt
       :align: center
       
.. versionchanged:: 0.4

    The measurement process involves taking a reading from the local clock when
    the request is about to be sent, and when the response is received. This measurement
    is taken from the *parent* of the clock you provide. The candidate represents
    a possible relationship between that (parent) clock and the Wall Clock of the
    server given the results of the request-response measurement. The algorithm
    processes this and makes a decision as to the :class:`~dvbcss.clock.Correlation`
    that is to be used.

Although the WallClockClient class does not require the tickrate of the
Wall Clock to be 1 tick per nanosecond, it is recommended to set it as such.
This is because the next step (using the CSS-TS protocol) assumes a Wall Clock
ticking at this rate.

"""

import threading
import socket
import logging
import dvbcss.monotonic_time as time

from dvbcss.protocol.wc import WCMessage, Candidate

import algorithm

class UdpRequestResponseClient(object):
    """\
    Engine for running a simple request-response system.
    
    After creating, call start() to kick off the thread.

    stop() will stop the thread the next time the handler asks to
    send a request.
    
    You provide a handler to implement the protocol specifics.
    It should be a python generator function.
    
    The handler should 'yield' the following tuple whenever it wants
    a request sent to a server:
       ((payload, (addr,port), timeoutSecs)
    or if you don't want to send a message but want to wait to receive
    another message:
        (None, timeoutSecs)
       
    payload = the bytes to send, as a string
    addr    = the IP address to send to, as a string
    port    = the port number to send to, as a number
    timeoutSecs = the number of seconds (or fractions of a second) to wait for a response
                  before timing out.
                  
    The yield statement will return a tuple:
      (None, None) ... if timeout happened, otherwise...
      (reply, (srcaddr, srcport))
      
    reply = the bytes received, as a string   
    srcaddr = the IP address it came from, as a string
    srcport = the port number it came from, as a number
    
    
    e.g. a simple handler that sends a request every second(ish),
         and waits up to half a second for a reply
    
      def handler():
        timeout=0.5
        request="request packet"
        dest=("127.0.0.1",5678)
        while True:
            print "Sending request to ",dest
            (reply,src) = (yield (req,dest),timeout)
            if reply is None:
                print "Timeout"
            else:
                print "Reply received from ",src
            print "Will wait 1 second before trying again"
            time.sleep(1.0)
    """
    def __init__(self, socket, handlerIterator, maxMsgSize, **kwargs):
        """\
        :param socket:  (udp socket) Bound socket ready to receive (and send) UDP packets
        :param handlerIterator: (generator) Handler for initiating and receiving results of request-response interactions
        :param maxMsgSize: (int) Maximum anticipated message size in bytes.
        """
        super(UdpRequestResponseClient,self).__init__(**kwargs)
        self.log=logging.getLogger("dvbcss.protocol.client.wc.UdpRequestResponseClient")
        self.socket = socket
        self.handler=handlerIterator
        self.maxMsgSize=maxMsgSize
        self.thread=None

    def start(self):
        """\
        Call this method to start the client running. This function call returns immediately
        and the client proceeds to run in a thread in the background.
        
        Does nothing if the client is already running.
        """
        if self.thread is not None:
            return
        self._pleaseStop=False
        self.thread = threading.Thread(target=self.run)
        self.thread.daemon=True
        self.log.debug("Starting")
        self.thread.start()
        
    def stop(self):
        """\
        Call this method to stop the client running. Returns once the client has stopped.
        
        If the client is not running then nothing happens and this call returns immediately.
        """
        if self.thread is None:
            return
        self._pleaseStop=True
        self.log.debug("Stopping")
        self.thread.join()
        self.log.debug("Stopped")
        
    def run(self):
        try:
            sendRequest, waitTimeSecs = self.handler.next()
            while not self._pleaseStop:
                if sendRequest is not None:
                    sendPayload,sendDest = sendRequest
                    self.socket.sendto(sendPayload,sendDest)
                self.socket.settimeout(waitTimeSecs)
                try:
                    reply,src=self.socket.recvfrom(self.maxMsgSize)
                    sendRequest, waitTimeSecs = self.handler.send((reply,src))
                except socket.timeout:
                    sendRequest, waitTimeSecs = self.handler.send((None,None))
        except StopIteration:
            pass


def _createUdpSocket((bindaddr, bindport)):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.settimeout(1.0)
    s.bind((bindaddr,bindport))
    return s


class WallClockClient(UdpRequestResponseClient):
    """\
    Simple object implementing the client side of the CSS-TS protocol.

    Use by initialising and supplying with an algorithm object and Clock object.
    
    The :class:`~dvbcss.protocol.wc.Candidate` objects provided to the algorithm
    represent the relationship between the parent of the provided clock and the
    server's Wall Clock.
    
    The algorithm is then expected to set the :class:`dvbcss.clock.Correlation`
    of the clock object such that it becomes an estimate of the server's
    Wall Clock.
        
    It is recommended to use the :class:`~dvbcss.protocol.client.wc.algorithm.LowestDispersionCandidate` algorithm.
    """
    def __init__(self, (bindaddr,bindport), (dstaddr,dstport), wallClock, wcAlgorithm):
        """\
        **Initialisation takes the following parameters:**
        
        :param (bindaddr,bindport): (:class:`str`, :class:`int`) A tuple containing the IP address (as a string) and port (as an int) to bind to to listen for incoming packets
        :param (dstaddr,dstport): (:class:`str`, :class:`int`) A tuple containing the IP address (as a string) and port (as an int) of the Wall Clock server
        :param wallClock: (:mod:`~dvbcss.clock`) The local clock that will be controlled to be a Wall Clock. Measurements will be taken from its parent and candidates provided to the algorithm will represent the relationship between that (parent) clock and the server's wall clock.
        :param wcAlgorithm: (:ref:`algorithm <algorithms>`) The algorithm for the client to use to update the clock.
        
        .. versionchanged: 0.4
        
           The `clock` provided should be a :class:`~dvbcss.clock.CorrelatedClock`, Although
           :class:`~dvbcss.clock.TunableClock` should still work becuase it is a subclass of
           :class:`~dvbcss.clock.CorrelatedClock`.
        """
        self.algorithm = wcAlgorithm #: (read only) The :ref:`algorithm <algorithms>` object being used with this WallClockClient
        algGenerator = self.algorithm.algorithm()
        socket=_createUdpSocket((bindaddr,bindport))
        msgSize=WCMessage.MSG_SIZE
        handler = algorithm.algorithmWrapper((dstaddr,dstport), wallClock.getParent(), algGenerator)
        super(WallClockClient, self).__init__(socket, handler, msgSize)



__all__ = [ "WallClockClient", "algorithm" ]
