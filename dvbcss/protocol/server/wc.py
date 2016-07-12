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
The :class:`WallClockServer` class implements a standalone CSS-WC server.

The server can be started and stopped. While running it runs in its own separate
thread of execution in the background.

An :doc:`example <examples>` server is provided in this package.


Example usage
-------------

To use it, you need to provide a :mod:`~dvbcss.clock` object that represents the "wall clock".
Although it is not required, it is recommended to set the tick rate of that clock to
match the required tick rate of the wall clock (1e9 ticks per second).

First, create the clock:

.. code-block:: python

    from dvbcss.clock import SysClock
    
    mfe = 45
    
    sysClock = SysClock(tickRate=1000000000, maxFreqErrorPpm=mfe)
    wallClock = sysClock
    
The server will need to know the potential maximum frequency error and measurement
precision of the clock. Fortunately the SysClock already estimates this and it
is passed through any dependent clocks.

Fortunately the SysClock internally estimates the measurement precision automatically
when it is created. It also defaults to assuming the maximum frequency error is
500ppm, unless you specify otherwise.

Maximum frequency error will depend on oscillator accuracy in the hardware the
code is running on, and whether an NTP client is running (and which therefore
may slew the clock).

For example, above we have guessed that
the combined worst case of NTP client slew and hardware oscillator accuracy
is approx 45 ppm:

So next we create and start the wall clock server.

.. code-block:: python

    from dvbcss.protocol.wc.server import WallClockServer
    
    wcServer = WallClockServer(wallClock)
    wcServer.start()
    
"""

import socket
import logging
import threading

from dvbcss.protocol.wc import WCMessage as WCMessage


class UdpRequestServer(object):
    """\
    Simple request handling server framework.
    
    Pass it an open UDP socket object that blocks on receive,
    and it will call your handler, passing the socket, plus the received data.
    
    This all happens in a separate thread.
    
    Use start() and stop() methods to start and stop the handling thread.
    
    Socket must have set blocking and a timeout.
    
    
    
    """
    def __init__(self, socket, handler, maxMsgSize):
        """\
        :param socket: Bound socket ready to receive (and send) UDP packets
        :type socket: :class:`socket.socket`
        :param handler: (object) Object providing a :func:`handle` method.
        :param int maxMsgSize: The maximum message size (sets the UDP receive buffer size)
        
        The `handler` object must have a method with the following signature:
        
            .. py:function:: handle(socket, received_data, src_addr)
            
               :param socket: The :class:`~socket.socket` object for the connection on which the packet was received.
               :param str received_data: The received UDP packet payload
               :param src_addr: The source address. For an AF_INET connection this will be a tuple (:class:`str` host, :class:`int` port)
        """
        super(UdpRequestServer,self).__init__()
        self.log=logging.getLogger("dvscss.protocol.server.wc.UdpRequestServer")
        self.socket = socket
        self.handler=handler
        self.maxMsgSize=maxMsgSize
        self.thread=None

    def start(self):
        r"""\
        Starts the wall clock server running. It runs in a thread in the background.
        """
        if self.thread is not None:
            return
        self._pleaseStop=False
        self.thread = threading.Thread(target=self.run)
        self.thread.daemon=True
        self.log.debug("Starting")
        self.thread.start()
        
    def stop(self):
        r"""\
        Stops the wall clock server running. Does not return until the thread has terminated.
        """
        if self.thread is None:
            return
        self._pleaseStop=True
        self.log.debug("Stopping")
        self.thread.join()
        self.log.debug("Stopped")
        
    def run(self):
        """\
        Internal method - the main runloop of the thread.
        
        Runs in a loop calling the :func:`handle` method of the object assigned to the :data:`handler` property
        whenever a UDP packet is received. 
        
        Does not return until the _pleaseStop attribute of the object has been set to True
        """
        while not self._pleaseStop:
            try:
                data,srcaddr=self.socket.recvfrom(self.maxMsgSize)
                self.handler.handle(self.socket, data, srcaddr)
                
            except socket.timeout:
                self.log.debug("Socket timeout.")
                pass



class WallClockServerHandler(object):
    """\
    Simple Wall Clock Server Handler function.
    
    Provides a handle() method. Designed to be used with :class:`UdpRequestServer`
    
    """
    
    def __init__(self, wallClock, precisionSecs=None, maxFreqErrorPpm=None, followup=False, **kwargs):
        """\
        
        :param dvbcss.clock.ClockBase wallClock: The clock to be used as the wall clock for protocol interactions
        :param precisionSecs:   (float) Optional. Override using the precision of the provided clock and instead use this value. It is the precision (in seconds) to be reported for the clock in protocol interactions
        :param maxFreqErrorPpm: (float or None) Optional. Override using the :func:`~dvbcss.clock.ClockBase.getRootMaxFreqError` of the clock and instead use this value. It is the clock maximum frequency error in parts-per-million
        :param bool followup: Set to True if the Wall Clock Server should send follow-up responses
        """
        super(WallClockServerHandler,self).__init__(**kwargs)
        self.log=logging.getLogger("dvbcss.protocol.server.wc.WallClockServerHandler")
        self.clock=wallClock
        self.precision=precisionSecs
        self.maxFreqErrorPpm=maxFreqErrorPpm
        self.followup=followup
        
    def handle(self, socket, data, srcaddr):
        recv_ticks, tickrate=self.clock.ticks, self.clock.tickRate
        
        msg=WCMessage.unpack(data)
        reply=msg.copy()
        if msg.msgtype==WCMessage.TYPE_REQUEST:
            reply.receiveNanos = recv_ticks * 1000000000 / tickrate
        
            if self.followup:
                reply.msgtype = WCMessage.TYPE_RESPONSE_WITH_FOLLOWUP
            else:
                reply.msgtype = WCMessage.TYPE_RESPONSE
            reply.setPrecision(self.precision if self.precision is not None else self.clock.dispersionAtTime(recv_ticks))
            reply.setMaxFreqError(self.maxFreqErrorPpm if self.maxFreqErrorPpm is not None else self.clock.getRootMaxFreqError())
            reply.transmitNanos = self.clock.ticks * 1000000000 / tickrate
            socket.sendto(reply.pack(), srcaddr)
            
            if self.followup:
                followupReply = reply.copy()
                followupReply.transmitNanos = self.clock.ticks * 1000000000 / tickrate
                followupReply.msgtype = WCMessage.TYPE_FOLLOWUP
                socket.sendto(followupReply.pack(), srcaddr)
            
            self.log.debug("Received :"+str(msg)+"\n")
            self.log.info("Responding to request from %s port %d with originate time=%20d ns" % (srcaddr[0], srcaddr[1], msg.originateNanos))
            self.log.debug("Response :"+str(reply)+"\n")
            if self.followup:
                self.log.debug("Followed by:"+str(followupReply)+"\n")
        else:
            raise ValueError("Wall clock server received non request message")


def _createUdpSocket((bindaddr, bindport)):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.settimeout(1.0)
    s.bind((bindaddr,bindport))
    return s



class WallClockServer(UdpRequestServer):
    """\
    A CSS-WC server.
    
    Pass it a :mod:`~dvbcss.clock` object and information on clock precision and frequency stability,
    and tell it which network interface to listen on.
    
    Call start() and stop() to start and stop the server. It runs in its own separate thread in the background.
    
    You can optionally ask this server to operate in a mode where it will send *follow-up* responses. Note, however, that
    in this implementation the transmit-timevalue reported in the follow-up response is not guaranteed to be more accurate.
    This option exists primarily to check whether a Wall Clock Client has implemennted handling of *follow-up*
    responses at all.
    """
    def __init__(self, wallClock, precision=None, maxFreqError=None, bindaddr="0.0.0.0", bindport=6677, followup=False):
        """\
        :param wallClock:       (:class:dvbcss.clock.ClockBase) The clock to be used as the wall clock for protocol interactions
        :param precisionSecs:   (float) Optional. Override using the precision of the provided clock and instead use this value. It is the precision (in seconds) to be reported for the clock in protocol interactions
        :param maxFreqErrorPpm: (float) Optional. Override using the :func:`~dvbcss.clock.ClockBase.rootMaxFreqError` of the clock and instead use this value. It is the clock maximum frequency error in parts-per-million
        :param bindaddr:        (str, ip address) The ip address of the network interface to bind to, e.g. "127.0.0.1". Defaults to "0.0.0.0" which binds to all interfaces.
        :param bindport:        (int) The port number to bind to (defaults to 6677)
        :param followup:        (bool) Set to True if the Wall Clock Server should send follow-up responses. Defaults to False.
        """
        socket=_createUdpSocket((bindaddr,bindport))
        handler=WallClockServerHandler(wallClock, precision, maxFreqError, followup)
        super(WallClockServer,self).__init__(socket, handler, WCMessage.MSG_SIZE)
        self.log = logging.getLogger("dvbcss.protocol.server.wc.WallClockServer")


__all__ = [
    "WallClockServer",
    "WallClockServerHandler",
]
