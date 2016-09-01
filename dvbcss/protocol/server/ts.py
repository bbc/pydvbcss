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
The :class:`TSServer` class implements a CSS-TS server that can be plugged into the cherrypy
web server engine.

To create a CSS-TS Server, first create and mount the server in a cherrypy web server. Then
you can start the cherrypy server and the CSS-TS server will start to accept connections from
clients.

The CSS-TS Server needs a *timeline source* to be given to it in order for it to serve these to clients.
A timeline source provides the Control Timestamps given a particular timeline selector.
A CSS-TS server can have multiple timelines sources plugged into it, and they can be added or removed dynamically while
the server is running.

An :doc:`example <examples>` server is provided in this package.



Using TSServer and Timeline Sources
-----------------------------------

1. Imports and initialisation
'''''''''''''''''''''''''''''

To run a CSS-TS server, you must import both ws4py's cherrypy server and the `dvbcss.protocol.server.ts` module.
When the `dvbcss.protocol.server.ts` module is imported, it will register as a "tool" with cherrypy, so it must
be imported after cherrypy is imported.

Next, subscribe the ws4py websocket plugin to cherrypy.

.. code-block:: python

    import cherrypy
    from ws4py.server.cherrypyserver import WebSocketPlugin
    from dvbcss.protocol.server.ts import TSServer

    # initialise the ws4py websocket plugin
    WebSocketPlugin(cherrypy.engine).subscribe()


2. Create and mount the TS server
''''''''''''''''''''''''''''''''''
You can now create an instance of a TSServer and mount it into the cherrypy server at a path of your choosing.

The configuration for that path (see example code below) must turn on the "dvb_ts" tool and pass a "handler_cls" argument whose value is the
handler class that the TS Server instance provides via the :data:`TSServer.handler` attribute.

The TS Server needs, at initialisation, to be told the initial contentId that it is providing timelines for
and it also needs to be provided with a :mod:`~dvbcss.clock` object representing the Wall Clock (ticking at
the correct rate of 1e9 ticks per second). It needs the WallClock so it can set the WallClockTime property in
Control Timestamps that notify clients of a timeline being unavailable.

For example, to create a TS Server mounted at the URL path "/ts":

.. code-block:: python

    # create a Wall Clock
    from dvbcss.clock import SysClock, CorrelatedClock
    sysClock = SysClock()
    wallClock = CorrelatedClock(parentClock=sysClock, tickRate=1000000000)
    
    # create TS Server
    tsServer = TSServer(contentId="dvb://1004", wallClock=wallClock, maxConnectionsAllowed=10)

    # bind it to the URL path /ts in the cherrypy server
    class Root(object):
        @cherrypy.expose
        def ts(self):
            pass
    
    # construct the configuration for this path, providing the handler and turning on the tool hook
    cfg = {"/ts": {'tools.dvb_ts.on': True,
                    'tools.dvb_ts.handler_cls': tsServer.handler
                   }
          }
    
    cherrypy.tree.mount(Root(), "/", config=cfg)    

3. Start cherrypy running
'''''''''''''''''''''''''

Start cherrypy running and our TS server will start to accept connections from clients:

.. code-block:: python

    # configure cherrypy to serve on port 7681
    cherrypy.config.update({"server.socket_port":7682})
    
    # activate cherrypy web server (non blocking)
    cherrypy.engine.start()

The cherrypy engine runs in a background thread when the cherrypy engine is started. Callbacks from
the :class:`TSServer` happen on the ws4py websocket library's thread(s) for handling received messages.


4. Providing timelines through the TS Server
''''''''''''''''''''''''''''''''''''''''''''

To make a timeline available to clients, we create a source for that timeline. For example, a :class:`SimpleClockTimelineSource`
based on a :mod:`~dvbcss.clock` object that corresponds to the ticking of progress on the timeline.
We also decide the timeline selector that clients must use to obtain that timeline.

For example, we might create a Timeline Source to represent ticking of a PTS timeline:

.. code-block:: python

    from dvbcss.protocol.server.ts import SimpleClockTimelineSource
    from dvbcss.clock import Correlation
    
    ptsClock = CorrelatedClock(parentClock=wallClock, tickRate=90000)
    ptsTimelineSrc = SimpleClockTimelineSource(timelineSelector="urn:dvb:css:timeline:pts", wallClock=wallClock, clock=ptsClock)
    
    # set that ptsClock to start counting from zero starting NOW:
    ptsClock.correlation = Correlation(wallClock.ticks, 0)

When we want that timeline to become available to connected clients we add it to the TS Server:

.. code-block:: python

    tsServer.attachTimelineSource(ptsTimelineSrc)
    tsServer.updateAllClients()

When we make any change (adding or removing timlelines, or changing a timeline in any way) then we must call :func:`TSServer.updateAllClients`
to ensure Control Timestamp messages are sent immediately to all connected clients to notify them of any changes.

Any new client connections or existing connections, that ask for that timeline (using the timeline selector and matching the content id)
will have the timeline made available to them.

If at some point the relationship between PTS and wall clock changes, or the
clock availability changes, then we must instruct the TS Server to send new Control Timestamps out if needed:

.. code-block:: python

    # lets reset the pts timeline position to zero again
    ptsClock.correlation = Correlation(wallClock.ticks, 0)
    tsServer.updateAllClients()
    
When we want to make the timeline unavailable, we can simply update the availability
of the clock:

.. code-block:: python

    ptsClock.setAvailability(False)
    tsServer.updateAllClients()

Or if we wish to stop more permanently, we can instead detatch the timeline source from the TS Server:

.. code-block:: python

    tsServer.removeTimelineSource(ptsTimelineSrc)
    tsServer.updateAllClients()

If there are clients connected that have asked for that timeline, then the update call will cause Control Timestamps to be sent to them
that indicate that the timeline is no longer available.

We can also change the contentId for which the timelines are being provided. If we do this, then again, it may change
whether timelines are available to any currently connected clients:

5. Changing content id
''''''''''''''''''''''

.. code-block:: python

    tsServer.contentId = "http://myservice.com/new-content-id"
    tsServer.updateAllClients()



What does TSServer do for you and what does it not?
---------------------------------------------------

:class:`TSServer` handles the connection and disconnection of clients without requiring any further intervention.
It handles the initial setup-data message and uses the information in that to determine which :class:`TimelineSource`
it should obtain Control Timestamps from. It will also automatically ensure 'null' Control Timestamp messages are
sent if there is no suitable timeline source.

Your code (or a :class:`TimelineSource` that you create) must call the :func:`updateClient` or
:func:`updateAllClients` to notify the TSServer that it needs to potentialy send updated Control Timestamps to clients.



More about Timeline Sources
---------------------------

A timeline source is any object that implements the methods defined by the :class:`TimelineSource` base class.

Exising timeline source implementations
'''''''''''''''''''''''''''''''''''''''

Two implementations are provided:

* :class:`SimpleTimelineSource` is a timeline source where you directly specify the Control Timestamp that will be sent to clients.
* :class:`SimpleClockTimelineSource` is a timeline source where Control Timestamps are generated from :mod:`Clock <dvbcss.clock>` objects representing the position of the timeline and the Wall Clock.

The CSS-TS server does *not* automatically push out new Control Timestamps to connected clients. It will only do so
when the :func:`updateAllClients` or :func:`updateClient` methods are called. This allows you to do things like swap
out and replace a timeline source object without causing spurious Control Timestamps to be sent.

Creating new Timeline Sources
'''''''''''''''''''''''''''''

Create new Timeline Source types by subclasing :class:`TimelineSource` and,
at minimum, implementing the stubs :func:`~TimelineSource.recognisesTimelineSelector`
and :func:`~TimelineSource.getControlTimestamp`.

For example, here is a timeline source that recognises a timeline selector
"urn:pretend-timeline:N" where N is the ticks per second of the timeline. The progress
of this timeline is controlled by the code outside of this object periodcally calling
the ``setTimelinePositionNow`` method. It needs a :mod:`~dvbcss.clock` object representing
the WallClock to be passed to it. It can serve different tick rates to different clients.

.. code-block:: python

    from dvbcss.protocol.server.ts import TimelineSource
    from dvbcss.protocol.ts import ControlTimestamp, Timestamp
    from dvbcss.clock import Correlation
    import re

    class PretendTimelineSource(TimelineSource):
        def __init__(self, wallClock):
            super(PretendTimelineSource,self).__init__()
            self.wallClock = wallClock
            self.correlation = Correlation(0,0)
                    
        def recognisesTimelineSelector(self, timelineSelector):
            return re.match("^urn:pretend-timeline:([0-9]+)$", timelineSelector)
        
        def getControlTimestamp(self, timelineSelector):
            match = re.match("^urn:pretend-timeline:([0-9]+)$", timelineSelector)
            if not match:
                raise RuntimeError("This should never happen.")
            elif self.correlation is None:
                # timeline not yet available, so return 'null' control timestamp
                return ControlTimestamp(Timestamp(None, self.wallClock.ticks), None)
            else:
                tickRate = int(match.group(1))
                contentTime = tickRate * self.correlation.childTicks
                wallClockTime = self.correlation.parentTicks
                speed = 1
                return ControlTimestamp(Timestamp(contentTime, wallClockTime), speed)
    
        def setTimelinePositionNow(self, timelineSecondsNow):
            self.correlation = Correlation(self.wallClock.nanos, timelineSecondsNow)

The base class also has stub methods to support notification of when a sink is attached
to the timeline source and also methods to notify of when a particular timeline selector
is being requested by at least one client and when it is no longer required by any clients.
See the documentation for :class:`TimelineSource` for more details.
"""

import cherrypy

from dvbcss.protocol.server import WSServerTool
from dvbcss.protocol.server import WSServerBase
from dvbcss.protocol.ts import SetupData, AptEptLpt, ControlTimestamp, Timestamp
from dvbcss.protocol import OMIT

cherrypy.tools.dvb_ts = WSServerTool()

            
class TSServer(WSServerBase):
    """\
    Implements a server for the CSS-TS protocol that serves timelines provided by sources that are plugged into this server object.
    
    Use by instantiating. You may subclass if you wish to optionally override the following methods:
    
    * :func:`onClientConnect`
    * :func:`onClientDisconnect`
    * :func:`onClientMessage`
    * :func:`onClientSetup`
    
    When the server is "disabled" it will refuse attempts to connect by sending the HTTP status response 403 "Forbidden".
    
    When the server has reached its connection limit, it will refuse attempts to connect by sending the HTTP status response 503 "Service unavailable".
    
    This object has the following properties:
    
    * :data:`enabled` (read/write) controls whether the server is enabled
    * :data:`contentId` (read/write) controls the contentId that timelines are being served for
    * :data:`handler` (read) the class that must be passed as part of the cherrypy configuration for the URL path this server is attached to.

    The :data:`contentId` and :data:`enabled` attributes can be changed at runtime. Whether the contentId matches that provided by a client
    when it initially connects is part of determining whether the timeline is available to the client.
    
    Use :func:`attachTimelineSource` and :func:`removeTimelineSource` to add and remove sources of timelines. Adding or removing a
    source of a timeline will affect availablilty of a timeline to a client.
    
    This server does not automatically send `Control Timestamp` messages to clients.
    After you make a change (e.g. to the :data:`contentId` or a state change in a timeline source
    or attaching or removing a timeline source) then you must call updateAllClients() to cause messages to be sent.
    
    The only exception to this is changes to the :data:`enabled` state which takes effect immediately.
    
    """
    
    connectionIdPrefix = "ts"
    loggingName = "dvb-css.protocol.server.ts.TSServer"
     
    def __init__(self, contentId, wallClock, maxConnectionsAllowed=-1, enabled=True):
        """\
        **Initialisation takes the following parameters:**
        
        :param str contentId: The content-id for which timelines will be made available.
        :param wallClock: The wall clock
        :type wallClock: :mod:`~dvbcss.clock`
        :param int maxConnectionsAllowed: (int, default=-1) Maximum number of concurrent connections to be allowed, or -1 to allow as many connections as resources allow.
        :param bool enabled: Whether this server starts off enabled or disabled.
        """
        super(TSServer,self).__init__(maxConnectionsAllowed=maxConnectionsAllowed, enabled=enabled)
        self.contentId = contentId  #: (read/write :class:`str`) The content ID for all timelines currently being served. Can be changed at runtime.
        self._wallClock = wallClock
        self._timelineSources = {}
        self._timelineSelectors = {}
    
    def getDefaultConnectionData(self):
        """\
        Internal method. Creates empty 'connection data' for the connection consisting of: a dict: ``{ "setup":None, "prevCt":None, "aptEptLpt":None }``
        
        This reflects that no setup-data has been received yet, and no Control Timestamps have been sent, and no AptEptLpt has been received either
        """
        return { "setup":None, "prevCt":None, "aptEptLpt":None }
   
        
    def onClientConnect(self, webSock):
        """\
        Called when a client establishes a connection.
        
        If you override, make sure you call the superclass implementation of this method.
        
        :param webSock: The connection from the client.
        """
        self.log.info("Client connected"+webSock.id())
    
    def onClientDisconnect(self, webSock, connectionData):
        """\
        Called when a client disconnects.
        
        If you override, make sure you call the superclass implementation of this method.
        
        :param webSock: The connection from the client.
        :param connectionData: A :class:`dict` containing data relating to this (now closed) connection
        """

        with self._lock:
            # update list of timeline selectors being used
            # if this one is no longer needed by any clients, then notify sources that this is the case
            setupData = connectionData["setup"]

            if setupData is not None:
                tSel = setupData.timelineSelector
                self._timelineSelectors[tSel] -= 1

                if self._timelineSelectors[tSel] == 0:
                    del self._timelineSelectors[tSel]
                    for src in self._timelineSources:
                        src.timelineSelectorNotNeeded(tSel)


    def onClientSetup(self, webSock):
        """\
        Called when a client has connected and submitted its SetupData message to provide context for the connection.
        
        |stub-method|
        
        :param webSock: The connection from the client.
        """
        pass
    
    def onClientMessage(self, webSock, message):
        """\
        Called when a message is received from a client.
        
        If you override, make sure you call the superclass implementation of this method.
        
        :param webSock: The connection from the client.
        :param msg: (:class:`Message <ws4py.messaging.Message>`) WebSocket message that has been received. Will be either a :class:`Text <ws4py.messaging.TextMessage>` or a :class:`Binary <ws4py.messaging.BinaryMessage>` message.
        """
        self.log.info("Received message on connection"+webSock.id()+" : "+str(message))

        with self._lock:
            connection = self.getConnections()[webSock]

            if connection["setup"] is None:
                # waiting for a SetupData message
                try:
                    setupData = SetupData.unpack(str(message))
                except ValueError, e:
                    self.log.info("Expected a valid SetupData message, but got this instead: "+str(message))
                    return
                connection["setup"] = setupData
                connection["webSocket"] = webSock

                # if no other clients already requesting this timeline selector, then notify sources it is now needed
                tSel = setupData.timelineSelector
                if tSel in self._timelineSelectors:
                    self._timelineSelectors[tSel] += 1
                else:
                    self._timelineSelectors[tSel] = 1
                if self._timelineSelectors[tSel] == 1:
                    for src in self._timelineSources:
                        src.timelineSelectorNeeded(tSel)

                # notify of client now setup, and then try to send first control timestamp to it
                self.onClientSetup(webSock)
                self.updateClient(webSock)

            else:
                # doing normal timestamp thing
                # expect AptEptLpt message
                try:
                    aptEptLpt = AptEptLpt.unpack(str(message))
                except ValueError, e:
                    self.log.info("Expected a valid AptEptLpt message, but got this instead: "+str(message))
                    return
                connection["aptEptLpt"] = aptEptLpt
                self.onClientAptEptLpt(webSock, aptEptLpt)

    def onClientAptEptLpt(self, webSock, apteptlpt):
        """\
        Called when a client has sent an updated AptEptLpt message

        |stub-method|

        :param webSock: The connection from the client.
        :param aptEptLpt: (:class:`~dvbcss.protcol.ts.AptEptLpt`) object representing the received timestamp message.
        """
        pass
            
    def attachTimelineSource(self, timelineSource):
        """\
        Attach (add) a source of a timeline to this CSS-TS server. This causes the timeline to become available immediately
        to any connected clients that might be requesting it.
        
        This causes the :func:`addSink` method of the timeline source to be called, to notify it that this CSS-TS server
        is now a recipient (sink) for this timeline.
        
        :param timelineSource: Any object implementing the methods of the :class:`TimelineSource` base class
        """
        self._timelineSources[timelineSource] = True
        timelineSource.attachSink(self)
        
    def removeTimelineSource(self, timelineSource):
        """\
        Remove a source of a timeline from this CSS-TS server. This causes the timeline to become unavailable immediately
        to any connected clients that are using it.
        
        This causes the :func:`removeSink` method of the timeline source to be called, to notify it that this CSS-TS server
        is no longer a customer (sink) for this timeline.
        
        :param timelineSource: Any object implementing the methods of the :class:`TimelineSource` base class
        """
        del self._timelineSources[timelineSource]
        timelineSource.removeSink(self)
        
    def updateClient(self,webSock):
        """\
        Causes an updated :class:`ControlTimestamp` to be sent to the WebSocket connection specified.
        
        The ControlTimestamp is only sent if it is different to the last time this was done for this connection.
        
        The value of the Control Timestamp is determined by searching all attached timeline sources to find one that
        can supply a Control Timestamp for this connection.
        """
        with self._lock:
            connection = self._connections[webSock]
            setup = connection["setup"]
            if setup is None:
                return

            prevCt = connection["prevCt"]

            # default 'timeline is unavailable' control timestamp
            ct = ControlTimestamp(Timestamp(None, self._wallClock.ticks), None)

            # check if contentIdStem matches current CI
            if ciMatchesStem(self.contentId, setup.contentIdStem):

                for source in self._timelineSources:
                    if source.recognisesTimelineSelector(setup.timelineSelector):
                        ct = source.getControlTimestamp(setup.timelineSelector)

            # if None, then a timeline source is saying "please don't send a control timestamp yet"
            # otherwise, check if the Control Timestamp is basically the same as the previous one sent
            # and only send if it is different
            if ct is not None and isControlTimestampChanged(prevCt, ct):
                connection["prevCt"] = ct
                webSock.send(ct.pack())

                
    def updateAllClients(self):
        """\
        Causes an update to be sent to all clients that need it
        (i.e. if the ControlTimestamp that would be sent now is different to the one most recently sent to that client)
        """
        with self._lock:
            for webSock in self._connections:
                self.updateClient(webSock)

def ciMatchesStem(ci, stem):
    """\
    Checks if a content identifier stem matches a content identifier. A match is when the content identifier
    starts with the stem and is the same length as the stem, or longer.
    
    :param ci: Content identifier
    :type ci: :class:`str` or :data:`~dvbcss.protocol.OMIT`
    :param str stem: Content identifier stem
    
    :returns: True if the supplied content identifier stem (stem) matches the content identifier. If the ci is :data:`~dvbcss.protocol.OMIT` then always returns False.
    """
    if ci == OMIT:
        return False
    return (ci is not None) and ci.startswith(stem)


def isControlTimestampChanged(prev, latest):
    """\
    Checks whether a new (latest) Control Timestamp is different when compared to a old (previous) Control Timestamp.
    
    Note that this does not check equivalency (if two Control Timestamps represent the same mapping between Wall clock time and content time)
    but instead checks if the property values comprising the two timestamps are exact matches.
    
    :param prev: :class:`None` or a previous :class:`~dvbcss.protocol.ts.ControlTimestamp` 
    :param latest: A new  :class:`~dvbcss.protocol.ts.ControlTimestamp` 
    
    :returns: True if the previous Control Timestamp is supplied is None, or if any of its properties differ in value to that of the latest Control Timestamp
    
    :throws ValueError: The new Control Timestamp supplied is None instead of a Control Timetamp
    """
    
    # sanity check
    if latest is None:
        raise ValueError("Latest control timestamp cannot be None")

    # if we don't have a previous CT yet, then we always take the latest
    if prev is None:
        return True
    
    # check if timeline remains unavailable, then irrespective of wallClockTime, it is unchanged
    if (prev.timestamp.contentTime is None) and (latest.timestamp.contentTime is None):
        return False
    
    # if values have changed, then it has changed
    if prev.timestamp.contentTime != latest.timestamp.contentTime:
        return True
    if prev.timestamp.wallClockTime != latest.timestamp.wallClockTime:
        return True
    if prev.timelineSpeedMultiplier != latest.timelineSpeedMultiplier:
        return True
    return False

    
        
class TimelineSource(object):
    """\
    Base class for timeline sources. 
    
    Subclass and implement the stub methods to create Timeline Source:
    
    * :func:`recognisesTimelineSelector`
    * :func:`getControlTimestamp`
    
    If your source needs to be informed of when a timeline is needed and when it becomes
    no longer needed (e.g. so you can allocate/deallocate resources needed to extract it)
    then also implement these stub methods:
        
    * :func:`timelineSelectorNeeded`
    * :func:`timelineSelectorNotNeeded`
    
    You can also optionally override the following methods, provided your
    code still calls through to the base class implementations:
    
    * :func:`attachSink` (see note)
    * :func:`removeSink` (see note)
    
    The :func:`attachSink` and :func:`removeSink` methods will be called by parties
    interested in the TimelineSource (such as a :class:`TSServer`) when they wish to
    use the timeline source. The base class implementations of these methods maintain
    the :data:`sinks` attribute as a dictionary indexed by sink.

    **Note:** When subclassing :func:`attachSink` and :func:`removeSink` remember to call
    the base class implementations of these methods.
    
    """

    def __init__(self):
        super(TimelineSource,self).__init__()
        self.sinks = {}
        
    def timelineSelectorNeeded(self, timelineSelector):
        """\
        Called to notify this Timeline Source that there is a need to provide a timeline for the specified
        timeline selector.
        
        :param timelineSelector:  (:class:`str`) A timeline selector supplied by a CSS-TS client that has not been specified by any other currently connected clients.
        
        This is useful to, for example, initiate processes needed to extract the timeline for the specified
        timeline selector. You will not receive repeats of the same notification.
        
        If the timeline is no longer needed then the :func:`timelineSelectorNotNeeded`
        function will be called to notify of this. After this, then you might be notified again in future if
        a timeline for the timeline selector becomes needed again.

        NOTE: If you override this in your subclass, ensure you still call this implementation in the base class.
        """
                
    def timelineSelectorNotNeeded(self, timelineSelector):
        """\
        Called to notify this Timeline Source that there is no longer a need to provide a timeline for the specified
        timeline selector.
        
        :param timelineSelector:  (:class:`str`) A timeline selector that was previously needed by one or more CSS-TS client(s) but which is no longer needed by any.
        
        NOTE: If you override this in your subclass, ensure you still call this implementation in the base class.
        """
                
    def recognisesTimelineSelector(self, timelineSelector):
        """\
        |stub-method|

        :param timelineSelector: (:class:`str`) A timeline selector supplied by a CSS-TS client
        
        :returns: True if this Timeline Source can provide a Control Timestamp given the specified timeline selector

        """        
        raise NotImplementedError("Subclass and implement this method. Return True or False")
    
    def getControlTimestamp(self, timelineSelector):
        """\
        Get the Control Timestamp from this Timeline Source given the supplied timeline selector.
        
        This method
        will only be called with timelineSelectors for which the :func:`recognisesTimelineSelector` method
        returned True.

        |stub-method|

        The return value should be a :class:`~dvbcss.protocol.ts.ControlTimestamp` object. If the timeline
        is known to be unavailable, then the contentTime and speed properties of that Control Timestamp must
        be None.
        
        If, however, you want the TS Server to not send any Control Timestamp to clients at all, then return
        None instead of a Control Timestamp object. Use this when, for example, you are still awaiting an result
        from code that has only just started to try to extract the timeline and doesn't yet know if there is one
        available or not.
        
        :param timelineSelector: (:class:`str`) A timeline selector supplied by a CSS-TS client

        :returns: A :class:`~dvbcss.protocol.ts.ControlTimestamp` object for this timeline source appropriate to the timeline selector, or None if the timleine is recognised no Control Timestamp should yet be provided.

        """
        raise NotImplementedError("Subclass and implement this method. Return a Control Timestamp")
    
    def attachSink(self, sink):
        """\
        Called to notify this Timeline Source that there is a sink (such as a :class:`~dvbcss.protocol.server.ts.TSServer`) that wishes to use this timeline source.
        
        :param sink: The sink object (e.g. a :class:`~dvbcss.protocol.server.ts.TSServer`)
        
        A TimelineSource implementation can use knowledge of what sinks are attached in whatever way it wishes.
        For example: it might use this to proactively call :func:`updateAllClients` on the attached TSServer when its
        Timeline's relationship to wall clock changes in some way. It is up to the individual implementation whether
        it chooses to do this or not.
        
        NOTE: If you override this in your subclass, ensure you still call this implementation in the base class.
        """
        self.sinks[sink] = True
        
    def removeSink(self, sink):
        """\
        Called to notify this Timeline Source that there is a sink that no longer wishes to use this timeline source.
        
        :param sink: The sink object
        
        NOTE: If you override this in your subclass, ensure you still call this implementation in the base class.
        """
        del self.sinks[sink]
        
    
    
class SimpleTimelineSource(TimelineSource):
    """\
    A simple Timeline Source implementation for a fixed timeline selector
    and where the Control Timestamp is specified manually.
    """
    
    def __init__(self, timelineSelector, controlTimestamp, *args, **kwargs):
        """\
        **Initialisation takes the following parameters:**
        
        :param timelineSelector: (:class:`str`) The exact timeline selector that this Timeline Source will provide Control Timestamps for.
        :param controlTimestamp: (:class:`~dvbcss.protocol.ts.ControlTimestamp`) The initial value of the Control Timestamp 
        """
        super(SimpleTimelineSource,self).__init__(*args, **kwargs)
        self.controlTimestamp = controlTimestamp
        self._timelineSelector = timelineSelector
        
    def recognisesTimelineSelector(self, timelineSelector):
        return self._timelineSelector == timelineSelector

    def getControlTimestamp(self, timelineSelector):
        return self.controlTimestamp
    
    
class SimpleClockTimelineSource(TimelineSource):
    """\
    Simple subclass of :class:`TimelineSource` that is based on a :mod:`~dvbcss.clock` object.
    
    The Control Timestamp returned by the :func:`~dvbcss.protocol.server.ts.SimpleClockTimelineSource.getControlTimestamp` method
    reflects the state of the clock.
    
    Note that this does **not** result in a new Control Timestamp being pushed to clients, unless you set the auto update
    parameter to True when initialising this object. By default (with no auto-updating), you still
    have to call :func:`~TSServer.updateAllClients` manually yourself to cause that to happen.
    
    Use auto-updating with caution: if you have multiple Timeline Sources driven by a common clock, then a change to that clock
    will cause each Timeline Source to call :func:`~TSServer.updateAllClients`, resulting in multiple unnecessary calls.
    
    The tick rate is fixed to that of the supplied clock and timeline selectors are only matched as an exact match.
    
    The speed property of the clock will be used as the timelineSpeedMultiplier value, unless a different clock is
    provided as the optional speedSource argument at initialisation.
    This is useful if the speed of the timeline is set by setting the speed property of a parent clock, and not the
    speed property of this clock (e.g. in situations where a single clock represents timeline progress but there
    are multiple clocks as children of that to represent the timeline on different scales - e.g. PTS, TEMI etc).
    
    The availability of the clock is mapped to whether the timeline is available.
    
    SimpleClockTimelineSource generates its correlation by observing the current tick value of the wallClock and the provided
    clock whenever a ControlTimestamp needs to be provided.
    """
    def __init__(self, timelineSelector, wallClock, clock, speedSource=None, autoUpdateClients=False):
        """\
        **Initialisation takes the following parameters:**
        
        :param timelineSelector: (:class:`str`) The timeline selector that this TimelineSource will provide Control Timestamps for
        :param wallClock: (:class:`~dvbcss.clock.ClockBase`) A clock object representing the Wall Clock
        :param clock: (:class:`~dvbcss.clock.ClockBase`) A clock object representing the flow of ticks of the timeline.
        :param speedSource: (None or :class:`~dvbcss.clock.ClockBase`) A different clock object from which the timelineSpeedMultiplier is determined (from the clock's speed property), or None if the clock for this is not different.
        :param autoUpdateClients: (:class:`bool`) Automatically call updateAllClients() if there is a change in the clock or wallClock
        """
        super(SimpleClockTimelineSource,self).__init__()
        self._timelineSelector = timelineSelector
        self._wallClock = wallClock
        self._clock = clock
        self._changed = True
        self._latestCt = None
        if speedSource == None:
            self._speedSource = clock
        else:
            self._speedSource = speedSource
        self.autoUpdateClients = autoUpdateClients
        
    def attachSink(self, sink):
        super(SimpleClockTimelineSource,self).attachSink(sink)
        # bind to clocks for notifications of changes IF we've gone from having
        # no sinks to suddenly having a sink
        if len(self.sinks) == 1:
            self._clock.bind(self)
            self._wallClock.bind(self)
            if self._clock != self._speedSource:
                self._speedSource.bind(self)
        
    def removeSink(self, sink):
        super(SimpleClockTimelineSource,self).removeSink(sink)
        # unbind if we no longer have any sinks
        if len(self.sinks) == 0:
            self._clock.unbind(self)
            self._wallClock.unbind(self)
            if self._clock != self._speedSource:
                self._speedSource.unbind(self)
        
    def notify(self,cause):
        """\
        Called by clocks to notify of changes (because this class binds itself to the clock object).
        
        If auto-updating is enabled then this will result in a call to :func:`updateAllClients` on all sinks.
        """
        self._changed=True
        if self.autoUpdateClients:
            for sink in self.sinks:
                sink.updateAllClients()
        
    def recognisesTimelineSelector(self, timelineSelector):
        return self._timelineSelector == timelineSelector

    def getControlTimestamp(self, timelineSelector):
        if self._changed:
            self._changed=False
            if self._clock.isAvailable():
                self._latestCt = ControlTimestamp(Timestamp(self._clock.ticks, self._wallClock.ticks), timelineSpeedMultiplier=self._speedSource.speed)
            else:
                self._latestCt = ControlTimestamp(Timestamp(None, self._wallClock.ticks), None)
        return self._latestCt
        
        
    
