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

import cherrypy
from cherrypy.process import plugins
from ws4py.websocket import WebSocket
from ws4py.server.cherrypyserver import WebSocketTool
from cherrypy.wsgiserver import HTTPConnection

import inspect
import threading

import logging

class ConnectionIdGen(object):
    """\
    Object for generating unique connection id strings.
    """
    nextId=1
    @classmethod
    def next(cls):
        """:return: new unique connection id string"""
        allocId = cls.nextId
        cls.nextId += 1
        return str(allocId)


class WSServerTool(WebSocketTool):
    """Subclass of the :class:`ws4py.server.cherrypyserver.WebSocketTool` tool to do a simultaneous connections limit check and enabled/disabled check for the end point before the handler is invoked"""
    def __init__(self):
        super(WSServerTool,self).__init__()
        self.log = logging.getLogger("dvbcss.protocol.server.WSServerTool")

    def upgrade(self, *args, **kwargs):
        """\
        Override of base implementation of the code to handle a connection "upgrade" (part of the WebSocket handshake).

        The "handler_cls" for this tool is passed as an argument and it implements methods to check whether:

        1. The end point is enabled. If not then a 403 "Forbidden" response is returned.
        2. A connection can be allocated (the connection limit is not yet reached). If not then a 503 "Service Unavailable" response is returned.

        If neither of these tests fail, then the superclass upgrade operation is allowed to proceed.
        """
        self.webSocket = None
        self.log.debug("Upgrade requested")
        cls=kwargs["handler_cls"]
        if not cls.isEnabled():
            raise cherrypy.HTTPError(403, "Forbidden. This end-point is currently unavailable")
        if not cls.canAllocateConnection():
            raise cherrypy.HTTPError(503, "Service Unavailable. No more connections to end-point permitted. Maximum limit reached.")
        retval = super(WSServerTool,self).upgrade(*args,**kwargs)
        self.webSocket = getattr(cherrypy.serving.request,"ws_handler")
        return retval

    def complete(self):
        """\
        Override of the base implementation of the code to install a callback to notify the websocket once
        the upgrade is complete.

        Cherrypy's normal "completion" callbacks fire /before/ cherrypy has flushed outgoing data to the socket connection,
        creating a race-condition between the flush happening and the websocket class starting to write outgoing messages.

        This replacement handler is guaranteed to fire /after/ cherrypy has flushed and is no longer using the socket connection.
        """
        super(WSServerTool,self).complete()

        # dereference now, in case WSServerTool is reused before the handler is invoked
        webSocket = self.webSocket

        # copy of pattern used in ws4py cherrypy server implementation
        # as we need to hook into close() method of the HTTPConnection in the WSGI
        # server in order to generate a callback that the WebSocket is now open
        # AFTER the cherrypy stack has finished sending the response headers
        # (the existing opened() callback on WebSocket gets triggered way too early
        # resulting in corruption of the HTTP response headers if you try to send() a
        # websocket data frame within the handler.
        current = inspect.currentframe()
        while True:
            if not current:
                break
            _locals = current.f_locals
            if 'self' in _locals:
                if type(_locals['self']) == HTTPConnection:
                    conn = _locals['self']
                    original = conn.close
                    if webSocket is not None:
                        def newClose():
                            webSocket.openComplete()
                            original()
                        _locals['self'].close = newClose
                    return
            _locals = None
            current = current.f_back


class WSServerBase(object):

    connectionIdPrefix = "serverbase"   #: prefix to be used for connection ids
    loggingName = "dvb-css.protocol.server.WSServerBase"  #: name used for logging messages

    def __init__(self, maxConnectionsAllowed=-1, enabled=True):
        """\
        Base class for WebSocket server endpoint implementation.

        :param int maxConnectionsAllowed: -1 to allow unlimited connections, otherwise sets the maximum number of concurrent connections from clients.
        :param bool enabled: Whether this server starts off enabled or disabled.

        When the server is "disabled" it will refuse attempts to connect by sending the HTTP status response 403 "Forbidden".

        When the server has reached its connection limit, it will refuse attempts to connect by sending the HTTP status response 503 "Service unavailable".


        Protocol specific implementations inherit from this base class and override stub methods and class attributes.
        When subclassing you will want to override:

        * :func:`getDefaultConnectionData`
        * :func:`onClientConnect`
        * :func:`onClientDisconnect`
        * :func:`onClientMessage`

        The :class:`~ws4py.websocket.WebSocket` connection object representing each connection is used as a handle for
        the connection.

        This class stores per connection connection data. What that data is is entirely up to the subclass.
        The :func:`getDefaultConnectionData` method provides the initial data for a connection when it is opened.
        The :data:`_connections` instance variable then keeps a mapping from websocket connections to that data.
        """
        super(WSServerBase,self).__init__()
        self.log = logging.getLogger(self.loggingName)
        self._pendingOpenCompletion = []

        # re-entrant lock used for thread safety
        self._lock = threading.RLock()

        self.handler = self._makeHandlerClass(connectionIdPrefix=self.connectionIdPrefix)
        """\
        Handler class for new connections. Should be provided as a configuration argument to cherrypy.
        """

        self.maxConnectionsAllowed = maxConnectionsAllowed
        self._connections={} #: dict mapping WebSocket objects to connection data. Connection data is for use by subclasses to store data specific to each individual connection.
        self.enabled = enabled

    def getDefaultConnectionData(self):
        """\
        This function is called to create new server-specific connection data when a new client
        connects. This is stored against the websocket connection and can be retrieved using the
        :func:`getConnections` method.

        Override with your own function that returns data to be stored against new connections
        :returns: empty :class:`dict`, but can return anything you like.
        """
        return { }


    def onClientConnect(self, webSock):
        """\
        This method is called when a new client connects.

        |stub-method|

        :param webSock:(:class:`WebSocket <ws4py.websocket.WebSocket>`) The object representing the WebSocket connection of the newly connected client
        """
        raise NotImplementedError("onClientConnect not implemented")

    def onClientDisconnect(self, webSock, connectionData):
        """\
        This method is called after a client is disconnected.

        |stub-method|

        :param webSock: (:class:`WebSocket <ws4py.websocket.WebSocket>`) The object representing the WebSocket connection of the now-disconnected client
        :param connectionData: (:class:`dict`) of connection data relating to this connection.
        """
        raise NotImplementedError("onClientDisconnect not implemented")

    def onClientMessage(self, webSock, msg):
        """\
        This method is called when a message is received from a client.

        |stub-method|

        :param webSock: (:class:`WebSocket <ws4py.websocket.WebSocket>`) The object representing the WebSocket connection from which the message has been received.
        :param msg: (:class:`Message <ws4py.messaging.Message>`) WebSocket message that has been received. Will be either a :class:`Text <ws4py.messaging.TextMessage>` or a :class:`Binary <ws4py.messaging.BinaryMessage>` message.
        """
        raise NotImplementedError("onClientMessage not implemented")

    @property
    def enabled(self):
        """\
        (read/write :class:`bool`) Whether this server endpoint is enabled (True) or disabled (False).

        Set this property enable or disable the endpoint.

        When disabled, existing connections are closed with WebSocket closure reason code 1001
        and new attempts to connect will be refused with HTTP response status code 403 "Forbidden".
        """
        return self._enabled

    @enabled.setter
    def enabled(self, value):
        with self._lock:
            self._enabled=value
            if self._enabled:
                cherrypy.engine.subscribe("stop", self.cleanup)
            else:
                cherrypy.engine.unsubscribe("stop", self.cleanup)
                for webSock in self._connections.keys():
                    webSock.close(code=1001) # 1001 = code for closure because server is "going away"
                    del self._connections[webSock]

    def cleanup(self):
        self.enabled=False

    def getConnections(self):
        """\
        :returns dict: mapping a :class:`WebSocket <ws4py.websocket.WebSocket>` object to connection related data for all connections to this server. This is a snapshot of the connections at the moment the call is made. The dictionary is not updated later if new clients connect or existing ones disconnect."""
        return self._connections.copy()

    def _addConnection(self, webSock):
        """\
        Internal method. Called to notify this class of a newly connected websocket.

        :param webSock: (:class:`WebSocket <ws4py.websocket.WebSocket>`) The newly connected Websocket.
        """
        with self._lock:
            self.log.debug("Adding websocket connection "+webSock.id())
            if webSock not in self._connections:
                self._connections[webSock] = self.getDefaultConnectionData()
                try:
                    self.onClientConnect(webSock)

                except Exception, e:
                    self.log.error(str(e))
                    print str(e)

    def _removeConnection(self, webSock):
        """\
        Internal method. Called to notify this class of a websocket disconnection.

        :param webSock: (:class:`WebSocket <ws4py.websocket.WebSocket>`) The now disconnected Websocket.
        """
        with self._lock:
            self.log.debug("Removing websocket connection "+webSock.id())
            if webSock in self._connections:
                conn=self._connections[webSock]
                del self._connections[webSock]
                self.onClientDisconnect(webSock, conn)

    def _receivedMessage(self, webSock, message):
        """\
        Internal method. Called to notify this class of a websocket message arrival.

        :param webSock: (:class:`WebSocket <ws4py.websocket.WebSocket>`) The WebSocket connection on which the message arrived.
        :param msg: (:class:`Message <ws4py.messaging.Message>`) WebSocket message that has been received. Will be either a :class:`Text <ws4py.messaging.TextMessage>` or a :class:`Binary <ws4py.messaging.BinaryMessage>` message.
        """
        self.log.debug("Received message from connection "+webSock.id()+" : "+str(message))
        with self._lock:
            self.onClientMessage(webSock,message)


    def _makeHandlerClass(self,connectionIdPrefix):
        """\
        :param connectionIdPrefix: (str) Human-readable prefix to be put on connection-ids
        :return: :class:`.WebSocketHandler` class, which is a subclass of :class:`ws4py.websocket.WebSocket` that is unique to this server instance.

        """
        serverSelf=self
        # create unique class specific to this instance of a server
        # so that we can plug it into the server

        class WebSocketHandler(WebSocket):
            """Server instance specific subclass of a WebScoket connection"""

            def __init__(self, *args, **kwargs):
                super(WebSocketHandler,self).__init__(*args,**kwargs)
                self.connectionId = connectionIdPrefix+"-" + ConnectionIdGen.next()

            @classmethod
            def isEnabled(cls):
                """\
                :return: True if the server endpoint is enabled, otherwise False.
                """
                return serverSelf.enabled

            @classmethod
            def canAllocateConnection(cls):
                """\
                :return: True only if the connection limit of the parent server has not yet been reached. Otherwise False.
                """
                serverSelf.log.debug("Checking concurrent connection allocation")
                return serverSelf.maxConnectionsAllowed < 0 or serverSelf.maxConnectionsAllowed > len(serverSelf._connections)

            def opened(self):
                # cant process sensibly now because websocket upgrade is complete
                # but connection is not properly regstered in the cherrypy framework
                # ... sending via the websocket connection now would cause it to prematurely terminate!!
                pass

            def openComplete(self):
                """\
                Informs parent server that the connection has been opened.
                """
                serverSelf.log.info("opened()")
                serverSelf._addConnection(self)

            def disconnected(self):
                """\
                Informs parent server that the connection has been disconnected.
                """
                serverSelf._removeConnection(self)

            def closed(self, code, reason=None):
                """\
                Informs parent server that the connection has been closed.

                :param reason: Reason code for the closure, or None.
                """
                serverSelf._removeConnection(self)

            def received_message(self, message):
                """\
                Passes a received message to the parent server.
                """
                serverSelf._receivedMessage(self,message)

            def id(self):
                """:return: connection id"""
                return self.connectionId

        return WebSocketHandler



__all__ = [  ]
