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
There are two classes provided for implementing CSS-CII clients:

* :class:`CIIClient` connects to a CII server and provides a CII message
  object representing the complete state of the server and notifies you of changes of state.

* :class:`CIIClientConnection` provides a lower level connection
  to a CII server and only provides the messages received from the server.
  It does not maintain a model of the server state and does not work out when
  a received message constitutes a change.

An :doc:`example <examples>` client is provided in this package that uses the :class:`CIIClient` class.

Using CIIClient
---------------

This is the simplest class to use. Create it, passing the URL of the server to connect to,
then call :func:`~CIIClient.connect` and :func:`~CIIClient.disconnect` to connect and disconnect from the server.

CIIClient maintains a local copy of the state of CII data the :data:`CIIClient.cii` property and the most
recently received CII message in :data:`CIIClient.latestCII`.

You can use the class either by subclassing and overriding the various stub methods
or by creating an instance and replacing the stub methods with your own function handlers
dynamically.

Pass the WebSocket URL of the CII server when creating the `CIIClient` then call the :func:`~CIIClient.connect()`
and :func:`~CIIClient.disconnect()` methods to connect and disconnect from the server. The `onXXX()` methods
can be overriden to find out when connection or disconnection takes place, if there is a protocol error (e.g.
a message was received that could not be parsed as CII) or when properties of the CII data change.

The CII state is kept in the :data:`~CIIClient.cii` property of the object. This is updated with properties
in CII messages that are received. Properties not included in a CII message are left unchanged.

Properties of the CII state whose value is :data:`dvbcss.protocol.OMIT` have not been defined by the CII server.

.. code-block:: python

    from dvbcss.protocol.client.cii import CIIClient

    class MyCIIClient(CIIClient):
    
        def onConnected(self):
            print "Connected!"
            
        def onDisconnected(self, code, reason):
            print "Disconnected :-("
            
        def onChange(self, propertyNames):
            print "The following CII properties have changed:
            for name in propertyNames:
                value = getattr(conn.cii, name)
                print "    "+name+" is now: "+str(value)
            
        # one example of a handler for changes to a particular property 'contentId' in CII    
        def onContentIdChange(self, newValue):
            print "The contentId property has changed to now be: "+str(newValue)


            
    client = MyCIIClient("ws://127.0.0.1/cii")
    client.connect()
    
    time.sleep(60)
    
    print "The current contentId is "+client.cii.contentId
    
    time.sleep(60)    # wait only 60 more seconds then disconnect
    
    client.disconnect()


The client runs in a separate thread managed by the websocket client library, so the `onXXX` methods are called while the main thread sleeps.



Using CIIClientConnection
-------------------------

This is a lower level class, that only implements parsing of the incoming CII messages from the server.
It does not detect if a message actually constitutes a change of state or not.

You can use the class either by subclassing and overriding the various stub methods
or by creating an instance and replacing the stub methods with your own function handlers
dynamically.

Pass the WebSocket URL of the CII server when creating the `CIIClientConnection` object then call the :func:`~CIIClientConnection.connect`
and :func:`~CIIClientConnection.disconnect` methods to connect and disconnect from the server. The `onXXX()` methods
can be overridden to find out when connection or disconnection takes place, if there is a protocol error (e.g.
a message was received that could not be parsed as CII) or when a new CII message is received.

.. code-block:: python

    from dvbcss.protocol.client.cii import CIIClientConnection

    class MyCIIClientConnection(CIIClientConnection):
    
        def onConnected(self):
            print "Connected!"
            
        def onDisconnected(self, code, reason):
            print "Disconnected :-("
            
        def onCii(self, cii):
            print "Received a CII message: "+str(cii)



    client = MyCIIClientConnection("ws://127.0.0.1/cii")
    client.connect()
    
    time.sleep(60)      # run only for 60 seconds then disconnect
    
    client.disconnect()

"""

import logging
import socket

from dvbcss.protocol.cii import CII
from dvbcss.protocol.client import WrappedWebSocket
from dvbcss.protocol.client import ConnectionError


class CIIClientConnection(object):
    """\
    Simple object for connecting to a CSS-CII server and handling the connection.
    
    Use by subclassing and overriding the following methods:
    
    * :func:`onConnected`
    * :func:`onDisconnected`
    * :func:`onCII`
    * :func:`onProtocolError`
    
    If you do not wish to subclass, you can instead create an instance of this
    class and replace the methods listed above with your own functions dynamically.
    """
    
    def __init__(self, url):
        """\
        **Initialisation takes the following parameters:**
        
        :param: url (:class:`str`) The WebSocket URL of the CII Server to connect to. E.g. "ws://127.0.0.1/mysystem/cii"
        """
        super(CIIClientConnection,self).__init__()
        self.log = logging.getLogger("dvbcss.protocol.client.cii.CIIClientConnection")
        self._ws = WrappedWebSocket(url, self)
        
        self._isOpen = False
        
    def onDisconnected(self, code, reason=None):
        """\
        This method is called when the connection is closed.
        
        |stub-method|

        :param code:   (:class:`int`) The connection closure code to be sent in the WebSocket disconnect frame
        :param reason: (:class:`str` or :class:`None`) The human readable reason for the closure
        """
        pass

    def onConnected(self):
        """\
        This method is called when the connection is opened.
        
        |stub-method|
        """
        pass

    def onCII(self, cii):
        """\
        This method is called when a CII message is received from the server.
        
        |stub-method|
        
        :param cii: A :class:`~dvbcss.protocol.cii.CII` object representing the received message.
        """
        pass
    
    def onProtocolError(self, msg):
        """\
        This method is called when there has been an error in the use of the CII protocol - e.g. receiving the wrong kind of message.
           
        |stub-method|
        
        :param msg: A :class:`str` description of the problem.
        """
        pass
    
    @property
    def connected(self):
        """True if the connection is connect, otherwise False"""
        return self._isOpen
        
    def connect(self):
        """\
        Open the connection.
        
        :throws :class:`ConnectionError` if there was a problem and the connection could not be opened.
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
      
    def _ws_on_open(self):
        self._isOpen=True
        self.log.debug("Connection opened.")
        self.onConnected()
        
    def _ws_on_close(self, code, reason=None):
        self._isOpen=False
        self.log.debug("Connection closed.")
        self.onDisconnected(code,reason)
        
    def _ws_on_disconnected(self):
        self._isOpen=False

    def _ws_on_error(self, msg):
        self.log.error("CII Protocol error: "+msg+"\n")
        self.onProtocolError(msg)
    
    def _ws_on_message(self, msg):
        self.log.debug("Message received.")
        if not msg.is_text:
            self._ws_on_error("Protocol error - message received was not a text frame")
            return
        try:
            cii = CII.unpack(msg.data)
        except Exception,e:
            self._ws_on_error("Protocol error - message received could not be parsed as a CII message: "+str(msg)+". Continuing anyway. Cause was: "+str(e)+"\n")
            return
        self.onCII(cii)


class CIIClient(object):
    """\
    Manages a CSS-CII protocol connection to a CSS-CII Server and notifies of changes to CII state.

    Use by subclassing and overriding the following methods:

    * :func:`onConnected`
    * :func:`onDisconnected`
    * :func:`onChange`
    * individual `onXXXXChange()` methods named after each CII property
    * :func:`onCiiReceived` (do not use, by preference)

    If you do not wish to subclass, you can instead create an instance of this
    class and replace the methods listed above with your own functions dynamically.

    The :func:`connect` and :func:`disconnect` methods connect and disconnect the connection to the server
    and :func:`getStatusSummary` provides a human readable summary of CII state.

    This object also provides properties you can query:

    * :data:`cii` represents the current state of CII at the server
    * :data:`latestCII` is the most recently CII message received from the server
    * :data:`connected` indicates whether the connection is currently connect

    """
    def __init__(self, ciiUrl):
        """\
        **Initialisation takes the following parameters:**
        
        :param ciiUrl: (:class:`str`) The WebSocket URL of the CSS-CII Server (e.g. "ws://127.0.0.1/myservice/cii")
        """
        super(CIIClient,self).__init__()
        self.log = logging.getLogger("dvbcss.protocol.client.cii.CIIClient")
        self._conn = CIIClientConnection(ciiUrl)
        self._conn.onCII = self._onCII
        self._conn.onConnected = self._onConnectionOpen
        self._conn.onDisconnected = self._onConnectionClose
        self._conn.onProtocolError = self._onProtocolError
        
        self.connected = False #: True if currently connected to the server, otherwise False.

        self.cii = CII()       #: (:class:`~dvbcss.protocol.cii.CII`) CII object representing the CII state at the server    
        self.latestCII = None  #: (:class:`~dvbcss.protocol.cii.CII` or :class:`None`) The most recent CII message received from the server or None if nothing has yet been received. 
                
        self._callBackFuncNames = {}
        for name in CII.allProperties():
            funcname = "on" + name[0].upper() + name[1:] + "Change"
            self._callBackFuncNames[name] = funcname
    
    def onConnected(self):
        """\
        This method is called when the connection is opened.
        
        |stub-method|
        """
        pass
    
    def onDisconnected(self, code, reason=None):
        """\
        This method is called when the connection is closed.
        
        |stub-method|
        
        :param code:   (:class:`int`) The connection closure code to be sent in the WebSocket disconnect frame
        :param reason: (:class:`str` or :class:`None`) The human readable reason for the closure
        """
        pass
    
    def onChange(self, changedPropertyNames):
        """\
        This method is called when a CII message is received from the server that causes one or more of the CII properties to change to a different value.
        
        :param changedPropertyNames: A :class:`list` of :class:`str` names of the properties that have changed. Query the :data:`cii` attribute to find out the new values.
        """
        pass
    
    def onProtocolError(self, msg):
        """\
        This method is called when there has been an error in the use of the CII protocol - e.g. receiving the wrong kind of message.
           
        |stub-method|
        
        :param msg: A :class:`str` description of the problem.
        """
        pass
    
    def onCiiReceived(self, newCii):
        """\
        This method is called when a CII message is received, but before any 'onXXXXChange()' handlers (if any) are called.
        It is called even if the message does not result in a change to CII state held locally.
        
        By preference is recommended to use the 'onXXXXChange()' handlers instead since these will only be called if there
        is an actual change to the value of a property in CII state.
        
        |stub-method|
        
        :param cii: A :class:`~dvbcss.protocol.cii.CII` object representing the received message.
        """
        pass
    
    def connect(self):
        """\
        Start the client by trying to open the connection.
        
        :throws ConnectionError: There was a problem that meant it was not possible to connect.
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
        
    def _onConnectionClose(self, code, reason):
        self.connected=False
        self.onDisconnected()
            
    def _onProtocolError(self, msg):
        self.log.error("There was a protocol error: "+msg+". Continuing anyway.")
        self.onProtocolError(msg)
        
    def _onCII(self, newCII):
        self.latestCII = newCII
        self.onCiiReceived(newCII)
        
        # take a diff since we cannot assume the received message is a diff
        diff=CII.diff(self.cii, newCII)
        changes=diff.definedProperties()
        
        if len(changes) > 0:      
            self.log.debug("Changed properties: "+ " ".join(changes))
            self.cii.update(diff)
            
            # now we examine changes and fire change specific callbacks as well as a general callback 
            for name in changes:
                if name in changes:
                    funcname = self._callBackFuncNames[name]
                    callback = getattr(self, funcname)
                    if callback is not None:
                        newValue=getattr(diff, name)
                        callback(newValue)
            
            
            # fire general catch-all callback
            self.onChange(changes)
        else:
            self.log.debug("No properties have changed")
                        
    def getStatusSummary(self):
        if self.latestCII is None:
            return "Nothing received from TV yet."
        
        return str(self.cii)

# programmatically create the onXXXChange methods for every property in a CII message
for propertyName in CII.allProperties():
    def f(self, newValue):
        pass
    f.__doc__="Called when the "+propertyName+" property of the CII message has been changed by a state update from the CII Server.\n\n" + \
              "|stub-method|\n\n" + \
              ":param newValue: The new value for this property."
    setattr(CIIClient, "on"+propertyName[0].upper() + propertyName[1:]+"Change", f)


__all__ = [
    "CIIClientConnection",
    "CIIClient",
]
