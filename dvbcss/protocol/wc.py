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
The :class:`WCMessage` class represents a CSS-WC protocol message.

The :class:`Candidate` class represents the measurement resulting from a
request-response exchange of messages with a server. This is a "candidate"
that could be used to update the client's estimate of the Wall Clock and is
therefore used by a Wall Clock Client algorithm. A candidate is calculated
from a :class:`WCMessage` that represents a Wall Clock protocol response
message received from a server.

A candidate can calculate the correlation needed to set a
:class:`~dvbcss.clock.CorrelatedClock` to model the server's Wall Clock.


Example usage
-------------

Creating a request message at a Wall Clock Client:

.. code-block:: python

    >>> from dvbcss.protocol.wc import WCMessage
    >>> import time
    
    >>> t1 = time.time() * 1000000000
    
    >>> msg = WCMessage(msgtype=WCMessage.TYPE_REQUEST, precision=-10, maxFreqError=256*50, originateNanos=t1, receiveNanos=0, transmitNanos=0)
    >>> packedMessage = msg.pack()
    >>> packedMessage
    "\x00\x00\xf6\x00\x00\x002\x00TvH'3\xf5\xfc\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"

    
Processing a received response message at a Wall Clock Client:

.. code-block:: python

    >>> from dvbcss.protocol.wc import Candidate
    
    >>> t4 = <nanoseconds-at-which-message-was-received>
    >>> msg = WCMessage.unpack(receivedData)
    >>> msg.msgtype
    1
    >>> c = Candidate(msg, t4)
    >>> c.rtt
    459734573
    
Creating a correlation to configure a :class:``dvbcss.clock.CorrelatedClock`
representing the client estimate of the server's wall clock:

.. code-block:: python

    >>> corr = c.calcCorrelationFor(wallClock, localMaxFreqErrorPpm=wallClock.getRootMaxFreqError())
    >>> wallClock.correlation = corr

"""
import logging

import struct
import math

from dvbcss.clock import Correlation

class WCMessage(object):

    TYPE_REQUEST=0 #: Constant: Message type 0 "request"
    TYPE_RESPONSE=1 #: Constant: Message type 1 "response with no follow-up"
    TYPE_RESPONSE_WITH_FOLLOWUP=2 #: Constant: Message type 2 "response to be followed by a follow-up response"
    TYPE_FOLLOWUP=3 #: Constant: Message type 3 "follow-up response"
    
    TYPE_ANY_RESPONSE = [1,2,3]
    TYPE_ANY_FIRST_RESPONSE = [1,2]

    STRUCT_FMT=">BBbBLLLLLLL"
    
    MSG_SIZE=32
    
    def __init__(self, msgtype,precision,maxFreqError,originateNanos,receiveNanos,transmitNanos,originalOriginate=None):
        r"""\
        Create object representing a CSS-WC wall clock request or response message.
        
        **Initialisation takes the following parameters:**
        
        :param int msgtype: Type of message. One of: :data:`TYPE_REQUEST`, :data:`TYPE_RESPONSE`, :data:`TYPE_RESPONSE_WITH_FOLLOWUP` and :data:`TYPE_FOLLOWUP`
        :param int precision: Precision (of the server's wall clock) encoded in log base 2 seconds between -128 and +127 inclusive.
        :param int maxFreqError: Maximum frequency error (of the server's wall clock) in units of  1/256ths ppm.
        :param int originateNanos: Originate timevalue in integer number of nanoseconds
        :param int receiveNanos: Receive timevalue in integer number of nanoseconds
        :param int transmitNanos: Transmit timevalue in integer number of nanoseconds
        :param originalOriginate: Optional original encoding of the originate timevalue as (seconds, nanos). Overrides `originateNanos` if not `None`. 
        :type originalOriginate: :obj:`None` or (:class:`int`, :class:`int`) 
        
        The originalOriginate parameter, if not None, overrides the originateNanos parameter.
        
        Convert to and from a string containing the binary encoding of this message
        using the :func:`pack` method and :func:`unpack` class method.
        """
        super(WCMessage,self).__init__()
        self.log = logging.getLogger("dvbcss.protocol.wc.WCMessage")

        self.msgtype = msgtype #: (read/write :class:`int`) Type of message. 0=request, 1=response, 2=response-with-followup, 3=followup
        self.precision = precision #: (read/write :class:`int`) Precision encoded in log base 2 seconds between -128 and +127 inclusive. For example: -10 encodes a precision value of roughly 0.001 seconds.
        self.maxFreqError = maxFreqError #: (read/write :class:`int`) Maximum frequency error in units of  1/256ths ppm. For example: 12800 encodes a max freq error of 50ppm.
        self.originateNanos = originateNanos #: (read/write :class:`int`) Originate timevalue in integer number of nanoseconds
        self.receiveNanos = receiveNanos #: (read/write :class:`int`) Receive timevalue in integer number of nanosecond
        self.transmitNanos = transmitNanos #: (read/write :class:`int`) Transmit timevalue in integer number of nanosecond
        self.originalOriginate = originalOriginate #: (read/write :obj:`None` or (:class:`int`, :class:`int`)) Optional original encoding of the originate timevalue as (seconds, nanos). Overrides `originateNanos` when the message is packed if the value is not `None`. 
        
        
    def pack(self):
        r"""\
        Pack wall clock message into binary representation.
        
        :returns: String containing the wall clock message in final bitstream form.
        """
        if self.originalOriginate is None:
            os, on = divmod(self.originateNanos,1000000000)
        else:
            os, on = self.originalOriginate
        rs, rn = divmod(self.receiveNanos,  1000000000)
        ts, tn = divmod(self.transmitNanos, 1000000000)
        msg = struct.pack(WCMessage.STRUCT_FMT, 0, self.msgtype, self.precision, 0, self.maxFreqError, os, on, rs, rn, ts, tn) 
        return msg
    
    @classmethod
    def unpack(cls, data):
        r"""\
        Class method that takes a string containing a wall clock message and unpacks
        it to a :class:`WCMessage` object.
        
        :param str data: String containing binary representation of a Wall Clock message as received from a client or server.

        :returns: :class:`WCMessage` object representing the wall clock message.
        """
        if len(data)!=cls.MSG_SIZE:
            raise ValueError("Wall Clock WCMessage wrong length")
        version, msgtype, precision, _, maxFreqError, os, on, rs, rn, ts, tn = struct.unpack(WCMessage.STRUCT_FMT, data)
        if version != 0:
            raise ValueError("Wall Clock WCMessage version number not recognised.")
        if msgtype > WCMessage.TYPE_FOLLOWUP:
            raise ValueError("Wall Clock WCMessage type not recognised.")
        o=os*1000000000 + on
        r=rs*1000000000 + rn
        t=ts*1000000000 + tn
        if (on >= 1000000000):
            originalOriginate=(os,on)
        else:
            originalOriginate=None
        return WCMessage(msgtype, precision, maxFreqError, o, r, t, originalOriginate)
        
    def copy(self):
        "Duplicate this wallclock message object"
        return WCMessage(self.msgtype, self.precision, self.maxFreqError, self.originateNanos, self.receiveNanos, self.transmitNanos, self.originalOriginate)

    def getPrecision(self):
        "Get precision value in fractions of a second"
        return self.decodePrecision(self.precision)

    def setPrecision(self,precisionSecs):
        "Set precision value given a precision represented as factions of a second"
        self.precision=self.encodePrecision(precisionSecs)

    def getMaxFreqError(self):
        "Get frequency error in ppm"
        return self.decodeMaxFreqError(self.maxFreqError)

    def setMaxFreqError(self, maxFreqErrorPpm):
        "Set freq error given a freq error represented as ppm"
        self.maxFreqError=self.encodeMaxFreqError(maxFreqErrorPpm)

    @classmethod
    def encodePrecision(cls,precisionSecs):
        "Convert a precision value in seconds to the format used in these messages"
        return int(math.ceil(math.log(precisionSecs)/math.log(2)))

    @classmethod
    def encodeMaxFreqError(cls,maxFreqErrorPpm):
        from __builtin__ import int
        return int(math.ceil(maxFreqErrorPpm*256))

    @classmethod
    def decodePrecision(cls,precision):
        return 2**precision
    
    @classmethod
    def decodeMaxFreqError(self,maxFreqError):
        return maxFreqError/256.0

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return 'WCMessage(msgtype=%03d, precision=%4d, maxFreqError=%10d, originateNanos=%20d,receiveNanos=%20d,transmitNanos=%20d,originalOriginate=%s)' % \
            (self.msgtype, self.precision, self.maxFreqError, self.originateNanos, self.receiveNanos, self.transmitNanos, str(self.originalOriginate))
            

class Candidate(object):
    r"""\
    This object represents a measurement "candidate" to be fed into a Wall Clock Client's
    algorithm. It is calculated from a :class:`WCMessage` received as a response from a
    Wall Clock server.
    
    This object requires that response comes from a Wall Clock Client that
    measured the *parent* of the clock that will be used to model the wall
    clock locally.
    
    **Initialisation takes the following parameters:**
    
    :param WCMessage msg: Response message received from server
    :type msg: :class:`WCMessage`
    :param int nanosRx: the time, in nanoseconds, at which it was received (from the server)
    
    Pass in a received WallClockMessage that is a response and this will represent the
    candidate data derived from that request-response interaction.

    Populates properties of this objects with the candidate information.
    :data:`t1`, :data:`t2`, :data:`t3` and :data:`t4` represent the times of message sending
    and receiving as shown below:
    
    .. image:: wc-request-response.png
       :width: 128pt
       :align: center
    
    It also calculates and provides, as properties, the round-trip time (:data:`rtt`)
    and clock offset estimate (:data:`offset`) based on this measurement.
    
    All data is in units of nanoseconds, except for precision which is measured
    in seconds, and maximum frequency error which is measured in ppm.
    
    A helper function :func:`calcCorrelationFor` makes it easy to calculate the
    :class:`~dvbcss.clock.Correlation` needed to take this measurment candidate
    and use it to control a :class:`~dvbcss.clock.CorrelatedClock`.
    """
    
    def __init__(self, msg, nanosRx):
        super(Candidate,self).__init__()
        self.log=logging.getLogger("dvbcss.protocol.wc.Candidate")
        if msg.msgtype not in WCMessage.TYPE_ANY_RESPONSE:
            raise ValueError("Cannot create a candidate from a non-response message")
        self.t1 = msg.originateNanos #: (read only) The time "t1" at which the request was sent in the request-response measurement (nanoseconds)
        self.t2 = msg.receiveNanos   #: (read only) The time "t2" at which the request was received in the request-response measurement (nanoseconds)
        self.t3 = msg.transmitNanos  #: (read only) The time "t3" at which the response was sent in the request-response measurement (nanoseconds)
        self.t4 = nanosRx            #: (read only) The time "t4" at which the response was received in the request-response measurement (nanoseconds)
        self.offset = ((self.t3+self.t2)-(self.t4+self.t1))/2 #: (read only) Server<->client clock offset (nanoseconds)
        self.rtt = (self.t4-self.t1)-(self.t3-self.t2) #: (read only) Round trip time (nanoseconds)
        self.precision = msg.getPrecision()  #: (read only) The precision reported by the server in its response (units of factions of a second)
        self.maxFreqError = msg.getMaxFreqError() #: (read only) The maximum frequency error reported by the server in its response (units of ppm)
        self.msg = msg #: (read only :class:`WCMessage`) The response message from which this candidate was derived
        
    def __str__(self):
        return "Candidate: offset=%20d, rtt=%20d, t1=%20d, t2=%20d, t3=%20d, t4=%20d" % (self.offset, self.rtt, self.t1, self.t2, self.t3, self.t4)

    def calcCorrelationFor(self, clock, localMaxFreqErrorPpm=None):
        r"""\
        Calculates and returns the :class:`~dvbcss.clock.Correlation` for a
        :class:`~dvbcss.clock.CorrelatedClock` that is equivalent to this candidate.
        
        The returned correlation can then be applied to the clock to model the time
        at the server. This includes the error bounds information needed to
        enable the clock to correctly calculate dispersion.

        :param clock: :class:`~dvbcss.clock.CorrelatedClock` that will model the server clock. Its parent must be the one that was measured for `t1` and `t4` this candidate.
        :param localMaxFreqErrorPpm: Optional. By defeault the :func:`~dvbcss.clock.ClockBase.getRootMaxFreqError` of the `clock` is used. Provide this value to override that.
        
        :returns: :class:`~dvbcss.clock.Correlation` representing this `candidate`, and that can be used with the :class:`~dvbcss.clock.CorrelatedClock`.
        
        .. note::
            The parameters of the correlation are calculated by this function
            as follows:
            
            * **parentTicks** = (t1' + t4') / 2
            * **childTicks** = (t2' + t3') / 2
            * **initialError** = precision + ( rtt/2 + mfeC * (t4 - t1) + mfeS * (t3 - t2) ) / 10\ :sup:`9`
            * **errorGrowthRate** = mfeC + mfeS
            
            Where:
            
            * **t1**, **t2**, **t3** and **t4** are in units of nanoseconds
            * **t1'** and **t4'** are the same as t1 and t4 but converted to ticks of the parent of the specified clock
            * **t2'** and **t3'** are the same as t2 and t3 but converted to ticks of the specified clock
            * **mfeC** is the clock's :func:`~dvbcss.clock.ClockBase.getRootMaxFreqError`, converted from ppm to a fraction by dividing by 10\ :sup:`6`
            * **mfeS** is the max freq error reported by the server, converted from ppm to a fraction by dividing by 10\ :sup:`6`
        
        .. versionadded:: 0.4
        """
        # convert to units of the clock
        t1 = clock.getParent().nanosToTicks(self.t1)
        t4 = clock.getParent().nanosToTicks(self.t4)
        t2 = clock.nanosToTicks(self.t2)
        t3 = clock.nanosToTicks(self.t3)
        
        if localMaxFreqErrorPpm is None:
            localMaxFreqErrorPpm = clock.getRootMaxFreqError()
            
        mfeC = localMaxFreqErrorPpm/1000000.0   # ppm to fraction
        mfeS = self.maxFreqError/1000000.0   # ppm to fraction
        
        return Correlation(
            parentTicks = (t1+t4)/2.0,
            childTicks = (t2+t3)/2.0,
            initialError = 
                self.precision +  # server precision. does not include local clock precision since this is already accounted for
                ( self.rtt/2.0 + 
                  mfeC*(self.t4-self.t1) + 
                  mfeS*(self.t3-self.t2)
                ) / 1000000000.0,    # nanos to seconds
            errorGrowthRate = (mfeC+mfeS)
        )

    def toTicks(self,clock):
        """\
        Returns a new Candidate object the same as this one but whose measurements have been converted to match the timescale of a clock.

        :raises NotImplementedError: This function has been deprecated.

        .. warning::
            .. deprecated:: 0.4
            
               This function has been deprecated because of the architectural
               change to taking taking readings from a different clock to the
               one that is adjusted.
               
               Use :func:`calcCorrelationFor` instead as this will perform the
               necessary conversion to clock tick rate units as well as creating
               the correlation needed to configure that clock.
        """
        raise NotImplementedError("This method has been deprecated in v0.4")
        
__all__ = [ "WCMessage", "Candidate" ]
