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
There are two classes provided for implementing CSS-TS clients:

* :class:`TSClientClockController` wraps a TSClientConnection and provides a higher level interface that
  provides information about timeline availability and drives a :mod:`~dvbcss.clock` object to match the
  timeline.
  
* :class:`TSClientConnection` implements the core functionality of connecting to a CSS-TS server
  and providing methods and callbacks to manage the connection and send and receive :mod:`timestamp <dvbcss.protocol.ts>`
  messages.
  
An :doc:`example <examples>` client is provided in this package that uses the :class:`TSClientClockController` class.



Using TSClientClockController
-----------------------------

This class provides a high level interface that drives a :class:`~dvbcss.clock.CorrelatedClock` object to match
the timeline provided by a CSS-TS server. Subclass to get notifications of connection, disconnection and timing
changes or changes in timeline availability.

Create it, passing the URL of the server to connect to, and a :class:`~dvbcss.clock.CorrelatedClock`object for
the controller to manage, then call  :func:`~TSClientClockController.connect` and
:func:`~TSClientClockController.disconnect` to connect and disconnect from the server.

The clock you provide must be a :class:`~dvbcss.clock.CorrelatedClock` object and the parent clock of that clock must represent
the *wall clock*. The tick rate of this clock must match that of the timeline and the tick rate of the wall clock
must be 1 tick per nanosecond (1e9 ticks per second).
This should therefore be used in conjunction with a
:class:`~dvbcss.protocol.client.WallClockClient` to ensure the wall clock is meaningfully synchronised to the same server.

The :class:`~TSClientClockController` object maintains the connection and automatically adjusts the
:data:`~dvbcss.clock.CorrelatedClock.correlation` of the clock to synchronise it, using the information in the
Control Timestamps received from the server.
It adjusts the :func:`~dvbcss.clock.CorrelatedClock.speed` to match speed changes of the timeline.
It also sets the availability of the clock to reflect the availability of the timeline.

You can set a minimum threshold for how much the timing must change before the the timeline clock will be adjusted.

You can also provide separate clock objects to represent the earliest and latest presentation timings that your
application can achieve (and that you wish to convey to the server). These must also be
:class:`~dvbcss.clock.CorrelatedClock` objects. Use the :func:`TSClientClockController.sendAptEptLpt` method to
cause that information to be sent to the server.

A simple example:

.. code-block:: python

    from dvbcss.protocol.client.ts import TSClientClockController
    from dvbcss.clock import CorrelatedClock, SysClock
    
    sysClock = SysClock()
    wallClock = CorrelatedClock(parent=sysClock, tickRate=1000000000)  # 1 nanosecond per tick
    timelineClock = CorrelatedClock(parent=wallClock, tickRate=90000)  # will represent PTS
    
    # NOTE: need a Wall Clock Client too (not shown in this example)
    #       to ensure wallClock is synchronised 
    
    class MyTSClient(TSClientClockController):
        
        def onConnected(self):
            print "Conected!"
        
        def onDisconnected(self):
            print "Disconnected :-("
        
        def onTimelineAvailable(self):
            print "Timeline is available!"
            
        def onTimelineUnavailable(self):
            print "Timeline is not available :-("

        def onTimingChange(self, speedHasChanged):
            print "Timing of clock has been adjusted."
            if speedHasChanged:
                print "The speed of the clock has altered."
                
    # make connection. Want PTS timeline for any DVB service.
    client = MyTSClient("ws://192.168.1.1:7682/ts",
                        "dvb://",
                        "urn:dvb:css:timeline:pts",
                        timelineClock)
    client.connect()
    
    for i in range(0,60):
        time.sleep(1)
        print "Timeline available?", timelineClock.isAvailable()
        if timelineClock.isAvailable():
            print "Timeline currently at tick value = ", timelineClock.ticks
            print "         ... and moving at speed = ", timelineClock.speed
        
    client.disconnect()

The client runs in a separate thread managed by the websocket client library, so the `onXXX` methods are called while the main thread sleeps.


Using TSClientConnection
------------------------

This class provides the lowest level interface to a CSS-TS server. It only implements
the parsing of incoming Control Timestamp messages and sending of outgoing Actual, Earliest
and Latest Presentation Timestamp messages. It does not try to understand the meaning of the
messages sent or received.

You can use the class either by subclassing and overriding the various stub methods or by
creating an instance and replacing the stub methods with your own function handlers dynamically.

Pass the WebSocket URL of the CSS-TS server during initialisation then call the :func:`~TSClientConnection.connect`
and :func:`~TSClientConnection.disconnect` methods to connect and disconnect from the server.
The `onXXX()` methods are called when connection or disconnection takes place, if there is a protocol
error (e.g. a message was received that could not be parsed as Control Timestamp) or a new Control Timestamp is
received.

A simple example:

.. code-block:: python

    from dvbcss.protocol.client.ts import TSClientConnection
    from dvbcss.protocol.ts import AptEptLpt
    from dvbcss.protocol import OMIT
    
    class MyClientConnection(TSClientConnection):
        def onConnected(self):
            print "Connected!"
            e = Timestamp(0, float("-inf"))
            l = Timestamp(0, float("+inf"))
            aptEptLpt = AptEptLpt(earliest=e, latest=l, actual=OMIT)
            client.sendTimestamp(aptEptLpt)
            
        def onDisconnected(self, code, reason):
            print "Disconnected :-("
            
        def onControlTimestamp(self, ct):
            print "Received a ControlTimestamp: "+str(ct)
    
    # make connection. Want PTS timeline for any DVB service.
    client = MyTSClientConnection("ws://127.0.0.1/ts", "dvb://", "urn:dvb:css:timeline:pts")
    client.connect()
    
    time.sleep(60)      # run only for 60 seconds then disconnect
    
    client.disconnect()
"""

import logging
import socket

from dvbcss.protocol.ts import SetupData
from dvbcss.protocol.ts import ControlTimestamp, AptEptLpt, Timestamp
from dvbcss.protocol.client import WrappedWebSocket
from dvbcss.protocol.client import ConnectionError
from dvbcss.clock import CorrelatedClock, Correlation



class TSClientConnection(object):
    """\
    Simple object for connecting to a CSS-TS server (an MSAS) and handling the connection.
    
    Use by subclassing and overriding the following methods or assigning your own functions to them at runtime:
    
    * :func:`onConnected`
    * :func:`onDisconnected`
    * :func:`onControlTimestamp`
    * :func:`onProtocolError`

    If you do not wish to subclass, you can instead create an instance of this class and replace the methods listed above with your own functions dynamically.

    Use the :func:`sendTimestamp` method to send Actual, Earliest and Latest Presentation Timestamps to the server.
    
    This class has the following properties:
    
    * :data:`connected` (read only) whether the client is connected or not
    """
    
    def __init__(self, url, contentIdStem, timelineSelector):
        """\
        **Initialisation takes the following parameters:**
        
        :param str url: The WebSocket URL of the TS Server to connect to. E.g. "ws://127.0.0.1/mysystem/ts"
        :param str contentIdStem: The stem of the content id to be included in the SetupData message that is sent as soon as the connection is opened.
        :param str timelineSelector: The timeline selector to be included in the SetupData message that is sent as soon as the connection is opened.
        """
        super(TSClientConnection,self).__init__()
        self.log = logging.getLogger("dvbcss.protocol.ts.TSClientConnection")
        self._ws = WrappedWebSocket(url, self)
        
        self._isOpen=False
        
        self._contentIdStem = contentIdStem
        self._timelineSelector = timelineSelector
        
    def onDisconnected(self):
        """\
        This method is called when the connection is closed.
        
        |stub-method|
        """
        pass

    def onConnected(self):
        """\
        This method is called when the connection is opened and the setup-data message has been sent.
        
        |stub-method|
        """
        pass

    def onControlTimestamp(self, controlTimestamp):
        """\
        This method is called when a Control Timestamp message is received from the server.
        
        |stub-method|
        
        :param controlTimestamp: A :class:`~dvbcss.protocol.ts.ControlTimestamp` object representing the received message.
        """
        pass
    
    def onProtocolError(self, msg):
        """\
        This method is called when there has been an error in the use of the TS protocol - e.g. receiving the wrong kind of message.
           
        |stub-method|
       
        :param msg: A :class:`str` description of the problem.
        """
        pass
    
    @property
    def connected(self):
        """This property is True if the connection is connect, otherwise False"""
        return self._isOpen
    
    def connect(self):
        """\
        Open the connection.
        
        :throws ConnectionError: if there was a problem and the connection could not be opened.
        """
        if not self._isOpen:
        
            self.log.debug("Opening connection")
            try:
                self._ws.connect()
            except ConnectionError, e:
                raise e
            except socket.error, e:
                raise ConnectionError()

    def disconnect(self, code=1001, reason=''):
        """\
        Close the connection.
        
        :param code:   (optional :class:`int`) The connection closure code to be sent in the WebSocket disconnect frame
        :param reason: (optional :class:`str`) The human readable reason for the closure
        """
        self._isOpen = False
        self._ws.close(code, reason)
        self._ws.close_connection()
        
    def sendTimestamp(self, aptEptLpt):
        """\
        Send an Actual, Earliest and Latest Presentation Timestamp message to the TS Server.
        
        :param aptEptLpt: The :class:`~dvbcss.protocol.ts.AptEptLpt` object representing the Actual, Earliest and Latest Presentation Timestamp to be sent.
        """
        self.log.debug("Sending message")
        self._ws.send(aptEptLpt.pack())

    def _ws_on_open(self):
        self._isOpen=True
        self.log.debug("Connection opened.")
        
        msg = SetupData(self._contentIdStem, self._timelineSelector)
        self._ws.send(msg.pack())
        
        self.onConnected()
        
    def _ws_on_close(self, code, reason=None):
        self._isOpen=False
        self.log.debug("Connection closed.")
        self.onDisconnected(code, reason)
        
    def _ws_on_disconnected(self):
        self._isOpen=False

    def _ws_on_error(self, msg):
        self.log.error("TS Protocol error: "+msg+"\n")
        self.onProtocolError(msg)
    
    def _ws_on_message(self, msg):
        self.log.debug("Message received.")
        if not msg.is_text:
            self._ws_on_error("Protocol error - message received was not a text frame")
            return
        try:
            ct = ControlTimestamp.unpack(msg.data)
        except Exception, e:
            self.log.error(str(e))
            self.log.error("Unable to parse message. Was not a correctly formed Control Timestamp message? Message was: "+str(msg)+"\nContinuing anyway.\n")
            return
        if self.onControlTimestamp is not None:
            self.onControlTimestamp(ct)


class TSClientClockController(object):
    """\
    This class manages a CSS-TS protocol connection and controls a :class:`~dvbcss.clock.CorrelatedClock` to synchronise it to the timeline
    provided by the server.
    
    Subclass and override the following methods when using this class:
    
    * :func:`onConnected`
    * :func:`onDisconnected`
    * :func:`onTimingChange`
    * :func:`onTimelineAvailable`
    * :func:`onTimelineUnavailable`
    * :func:`onProtocolError`

    If you do not wish to subclass, you can instead create an instance of this class and replace the methods listed above with your own functions dynamically.

    Create an instance of this class and use the :func:`connect` and :func:`disconnect` methods to start and stop its connection to
    the server. The `contentIdStem` and `timelineSelector` you specify are sent to the server in a
    :class:`~dvbcss.protocol.ts.SetupData` message to choose the timeline to receive from the server.
    
    While connected, while the timeline is available, the timelineClock you provided will have its :data:`~dvbcss.clock.CorrelatedClock.correlation`
    updated to keep it in sync with the timeline received from the server.
    
    The :data:`~dvbcss.clock.CorrelatedClock.speed` property of the timeline clock will also be adjusted to match
    the timeline speed indicated by the server. For example: it will be set to zero when the timeline is paused,
    or 2.0 when the timeline speed is x2. The :data:`~dvbcss.clock.CorrelatedClock.tickRate` property of the clock
    is not changed.
    
    Requirements for the timeline clock you provide:
    
    * The :data:`~dvbcss.clock.CorrelatedClock.tickRate` of the **timeline clock** must match that of the timeline.
    * Its parent must represent the **wall clock**
    * The **wall clock** must have a `~dvbcss.clock.CorrelatedClock.tickRate` that matches the wall clock tick rate.

    The TSClientClockController has the following properties:
    
    * :data:`connected` (read only) is the client connected?
    * :data:`timelineAvailable` (read only) is the timeline available?
    * :data:`latestCt` (read only) is the most recently received :class:`~dvbcss.protocol.ts.ControlTimestamp` message
    * :data:`earliestClock` (read/write) A clock object representing earliest possible presentation timing, or :class:`None`
    * :data:`latestClock` (read/write) A clock object representing latest possible presentation timing, or :class:`None`
    """
    def __init__(self, tsUrl, contentIdStem, timelineSelector, timelineClock, correlationChangeThresholdSecs=0.0001, earliestClock=None, latestClock=None):
        """\
        **Initialisation takes the following parameters:**
        
        :param str url: The WebSocket URL of the TS Server to connect to. E.g. "ws://127.0.0.1/mysystem/ts"
        :param str contentIdStem: The stem of the content id to be included in the SetupData message that is sent as soon as the conncetion is opened.
        :param str timelineSelector: The timeline selector to be included in the SetupData message that is sent as soon as the conncetion is opened.
        :param timelineClock: A clock object whose parent must represent the wall clock.
        :type timelineClock: :class:`~dvbcss.clock.CorrelatedClock`
        :param float correlationChangeThresholdSecs: Minimum threshold for the change in the timeline (in units of seconds) that will result in the timeline clock being adjusted.
        :param earliestClock: An optional clock object representing the earliest possible presentation timing that this client can achieve (expressed on the same timeline)
        :param latestClock: An optional clock object representing the latest possible presentation timing that this client can achieve (expressed on the same timeline)
        :type earliestClock: :class:`~dvbcss.clock.CorrelatedClock` or :class:`None`
        :type latestClock: :class:`~dvbcss.clock.CorrelatedClock` or :class:`None`
        """
        super(TSClientClockController,self).__init__()
        self.log=logging.getLogger("dvbcss.protocol.ts.TSClientClockController")
        
        self._conn = TSClientConnection(tsUrl, contentIdStem, timelineSelector)
        self._conn.onControlTimestamp = self._onControlTimestamp
        self._conn.onConnected = self._onConnectionOpen
        self._conn.onDisconnected = self._onConnectionClose
        self._conn.onProtocolError = self._onProtocolError
        
        self.timelineClock = timelineClock

        self.connected = False #: (:class:`bool`) True if currently connected to the server, otherwise False.
        
        self._changeThreshold = correlationChangeThresholdSecs
        
        self.latestCt = None #: (:class:`~dvbcss.protocol.ts.ControlTimestamp`) A copy of the most recently received Control Timestamp.
        
        self.earliestClock = earliestClock #: :data:`None` or a :class:`~dvbcss.clock.CorrelatedClock` correlated to the WallClock representing the earliest possible presentation timing.
        self.latestClock   = latestClock #: :data:`None` or a :class:`~dvbcss.clock.CorrelatedClock` correlated to the WallClock representing the latest possible presentation timing.
        
    @property
    def timelineAvailable(self):
        """\
        (:class:`bool`) True if the most recently received Control Timestamp indicates that the timeline is available.
        
        .. versionchanged:: 0.4
        
           It is now recommended to not use this method. Instead, use the :func:`~dvbcss.clock.ClockBase.isAvailable` method of a :mod:`~dvbcss.clock` instead.
        """
        return self.latestCt is not None and self.latestCt.timestamp.contentTime is not None
        
    def onConnected(self):
        """\
        This method is called when the connection is opened and the setup-data message has been sent.
        
        |stub-method|
        """
        pass
    
    def onDisconnected(self):
        """\
        This method is called when the connection is closed.
        
        |stub-method|
        """
        pass
    
    def onTimelineUnavailable(self):
        """\
        This method is called when the server indicates that the timeline is unavailable.
        
        |stub-method|
        """
        pass
    
    def onTimelineAvailable(self):
        """\
        This method is called when the server indicates that the timeline is available.
        
        |stub-method|
        """
        pass
    
    def onTimingChange(self, speedChanged):
        """\
        This method is called when the server indicates that the timeline timing has changed.
        
        This means that a received Control Timestamp has changed the timing of the clock relative
        to the wall clock by the threshold amount or more, or that the speed of the timeline has changed.
        (as indicated by the timelineSpeedMultiplier property of received Control Timestamps).

        |stub-method|

        :param speedChanged: (:class:`bool`) True if the speed of the timeline has changed, otherwise False.
        """
        pass
    
    def onProtocolError(self, msg):
        """\
        This method is called when there has been an error in the use of the CII protocol - e.g. receiving the wrong kind of message.
           
        |stub-method|
        
        :param msg: A :class:`str` description of the problem.
     """
        pass
    
    def connect(self):
        """\
        Start the client by trying to open the connection.
        
        If the connection opens successfully, a :class:`~dvbcss.protocol.ts.SetupData` message will be sent automatically.
        
        :throws ConnectionError: if there was a problem and the connection could not be opened.
        """
        self._conn.connect()
        
    def disconnect(self):
        """\
        Disconnect from the server.
        """
        self._conn.disconnect()
        
    def _onConnectionOpen(self):
        self.connected=True
        self.onConnected()
        
    def _onConnectionClose(self, code, reason=None):
        self.connected=False
        if self.timelineClock.isAvailable():
            self.timelineClock.setAvailability(False)
            self.onTimelineUnavailable(self)
        self.onDisconnected()
    
    def _onProtocolError(self, msg):
        self.log.error("There was a protocol error: "+msg+". Continuing anyway.")
        self.onProtocolError(msg)
        
    def _onControlTimestamp(self, ct):
        self.latestCt = ct
        self.log.debug("New Control Timestamp: "+str(ct))

        available = ct.timestamp.contentTime is not None
        availChanged = bool(available) != bool(self.timelineClock.isAvailable())
        
        # only extract new corelation and and compare to existing clock 
        # if the control timestamp indicates that the timeline is actually available
        
        if available:
            speed = float(ct.timelineSpeedMultiplier)
            corr = Correlation(ct.timestamp.wallClockTime, ct.timestamp.contentTime)
            corrSpeedChanged = self.timelineClock.isChangeSignificant(corr, speed, self._changeThreshold)
            speedChanged = self.timelineClock.speed != speed
        else:
            corrSpeedChanged = False

        # update correlation and speed, then update availability, to
        # ensure a correlation is not changed immediately *after* the clock
        # becomes available. Better it happens before, so downstream processing
        # can ignore while unavailable.

        if corrSpeedChanged:
            self.timelineClock.setCorrelationAndSpeed(corr, speed)
        
        if availChanged:
            self.timelineClock.setAvailability(available)

        # notification calls
        if available and corrSpeedChanged:
            self.log.debug("Speed has changed and/or correlation has changed by more than threshold amount")
            self.onTimingChange(speedChanged=speedChanged)

        if availChanged:
            if available:
                self.log.debug("Timeline has become available.")
                self.onTimelineAvailable()
            else:
                self.log.debug("Timeline has become unavailable.")
                self.onTimelineUnavailable()
        
                
    def sendAptEptLpt(self, includeApt=True):
        """\
        Sends an Actual, Earliest and Latest presentation timestamp to the CSS-TS server.
        
        * The EPT is derived from the :data:`earliestClock` property, if it is not None and it is a clock that is available.
        * The LPT is derived from the :data:`latestClock` property, if it is not None and it is a clock that is available.
        * The APT is only included if the includeApt argument is True (default=True) and it is a clock that is available.
        
        :param includeApt: (:class:`bool`) Set to False if the Actual Presentation Timestamp is *not* to be included in the message (default=True)
        """
        ael = AptEptLpt()
        now = self.timelineClock.ticks

        if self.earliestClock is not None and self.earliestClock.isAvailable():
            ael.earliest = Timestamp( \
                contentTime   = self.earliestClock.correlation.childTicks,
                wallClockTime = self.earliestClock.correlation.parentTicks \
            )
        else:
            ael.earliest = Timestamp(contentTime = now, wallClockTime = float("-inf"))
        
        if self.latestClock is not None and self.earliestClock.isAvailable():
            ael.latest = Timestamp( \
                contentTime   = self.latestClock.correlation.childTicks,
                wallClockTime = self.latestClock.correlation.parentTicks \
            )
        else:
            ael.latest = Timestamp(contentTime = now, wallClockTime = float("+inf"))
    
        if includeApt and self.timelineClock.isAvailable():
            ael.actual = Timestamp( \
                contentTime   = self.timelineClock.correlation.childTicks,
                wallClockTime = self.timelineClock.correlation.parentTicks \
            )
        
        self._conn.sendTimestamp(ael)
                    
    def getStatusSummary(self):
        """\
        :returns str: A human readable string describing the state of the timeline and the connection. 
        """
        if self.latestCt is None:
            return "Nothing received from TV yet."
        speed = self.timelineClock.speed
        pos = float(self.timelineClock.ticks) / float(self.timelineClock.tickRate)
        available = self.timelineClock.isAvailable()
        text="Status: "
        if available:
            text += "AVAILABLE.    "
            text += "  Speed = %5.2f  Timeline position = %10.3f secs" % (speed,pos)
        else:
            text += "NOT available."
            text += "  Speed = -----  Timeline position = ----------     "
        return text
          


__all__ = [
    "TSClientConnection",
    "TSClientClockController",
]

