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
The :class:`CIIServer` class implements a CII server that can be plugged into the cherrypy
web server engine.

To create a CII Server, first create and mount the server in a cherrypy web server. Then
you can start the cherrypy server and the CII server will start to accept connections from
clients.
While the server is running, update the CII state maintained by that server and instruct it when to push
updates to all connected clients.

An :doc:`example <examples>` server is provided in this package.

Using CII Server
----------------

1. Imports and initialisation
'''''''''''''''''''''''''''''

To run a CII server, you must import both ws4py's cherrypy server and the `dvbcss.protocol.server.cii` module.
When the `dvbcss.protocol.server.cii` module is imported, it will register as a "tool" with cherrypy, so it must
be imported after cherrypy is imported.

Next, subscribe the ws4py websocket plugin to cherrypy.

.. code-block:: python

    import cherrypy
    from ws4py.server.cherrypyserver import WebSocketPlugin
    from dvbcss.protocol.server.cii import CIIServer

    # initialise the ws4py websocket plugin
    WebSocketPlugin(cherrypy.engine).subscribe()


2. Create and mount the CII server
''''''''''''''''''''''''''''''''''
You can now create an instance of a CIIServer and mount it into the cherrypy server at a path of your choosing.

The configuration for that path must turn on the "dvb_cii" tool and pass a "handler_cls" argument whose value is the
handler class that the CIIServer instance provides via the :data:`CIIServer.handler` attribute.

For example, to create a CIIServer mounted at the URL path "/cii":

.. code-block:: python

    # create CII Server
    ciiServer = CIIServer(maxConnectionsAllowed=2)

    # bind it to the URL path /cii in the cherrypy server
    class Root(object):
        @cherrypy.expose
        def cii(self):
            pass
    
    # construct the configuration for this path, providing the handler and turning on the tool hook
    cfg = {"/cii": {'tools.dvb_cii.on': True,
                    'tools.dvb_cii.handler_cls': ciiServer.handler
                   }
          }
    
    cherrypy.tree.mount(Root(), "/", config=cfg)    

3. Start cherrypy running
'''''''''''''''''''''''''

Start cherrypy running and our CII server will start to accept connections from clients:

.. code-block:: python

    # configure cherrypy to serve on port 7681
    cherrypy.config.update({"server.socket_port":7681})
    
    # activate cherrypy web server (non blocking)
    cherrypy.engine.start()

The cherrypy engine runs in a background thread when the cherrypy engine is started.


4. Setting CII state and pushing it to connected clients
''''''''''''''''''''''''''''''''''''''''''''''''''''''''

The :data:`CIIServer.cii` is a CII message object representing the CII state. Your code can read and alter the attributes of this
message object to update the server side state.

When a client first connects, a CII message object will automatically be sent to that client to send it the current CII state.
Your code does not need to do this.

If you update the CII state then you need to ask the CII server to push a change to all connected clients.
To do this call the :func:`CIIServer.updateClients`
method. By default this will only push changes to CII state, and will not send a message at all if there is no change.
However this behaviour can be overridden.

.. code-block:: python

    ciiServer.cii.contentId = "dvb://233a.1004.1080"
    ciiServer.cii.contentIdStatus = "partial"
    ciiServer.updateClients()

    ...
    
    ciiServer.cii.contentId = "dvb://233a.1004.1080;21af~20131004T1015Z--PT01H00M"
    ciiServer.cii.contentIdStatus = "final"
    ciiServer.updateClients()



What does CIIServer do for you and what does it not?
----------------------------------------------------

:class:`CIIServer` handles the connection and disconnection of clients without requiring any further intervention.
It ensure the current state in its :data:`~CIIServer.cii` property is sent, in a CII message, to the client as soon as it connects.

The role of your code is to update the :data:`~CIIServer.cii` object as state changes, and to inform the CIIServer
when it is time to update any connected clients by informing them of the changes to state by calling the :func:`~CIIServer.updateClients` method.



"""

import cherrypy

from dvbcss.protocol.server import WSServerTool
from dvbcss.protocol.server import WSServerBase
from dvbcss.protocol.cii import CII
from dvbcss.protocol import OMIT

cherrypy.tools.dvb_cii = WSServerTool()

            
class CIIServer(WSServerBase):
    """\
    The CIIServer class implements a server for the CSS-CII protocol. It transparently manages
    the connection and disconnection of clients and provides an interface for simply setting the
    CII state and requesting that it be pushed to any connected clients.
    
    Must be used in conjunction with a cherrypy web server:
    
    1. Ensure the ws4py :class:`~ws4py.server.cherrypyserver.WebSocketPlugin` is subscribed, to the cherrypy server. E.g.
    
       .. code-block:: python
    
         WebSocketPlugin(cherrypy.engine).subscribe()
         
    2. Mount the instance onto a particular URL path on a cherrypy web server. Set the config
       properties for the URL it is to be mounted at as follows:
    
       .. code-block:: python
    
         { 'tools.dvb_cii.on'         : True,
           'tools.dvb_cii.handler_cls': myCiiServerInstance.handler }
        
    Update the :data:`cii` property with the CII state information and call the :func:`updateClients` method to propagate state changes to
    any connected clients.

    When the server is "disabled" it will refuse attempts to connect by sending the HTTP status response 403 "Forbidden".

    When the server has reached its connection limit, it will refuse attempts to connect by sending the HTTP status response 503 "Service unavailable".
    
    This object provides properties:

    * :data:`enabled` (read/write) controls whether this server is enabled or not
    * :data:`cii` (read/write) the CII state that is being shared to connected clients
    """
    
    connectionIdPrefix = "cii"
    loggingName = "dvb-css.protocol.server.cii.CIIServer"
    
    getDefaultConnectionData = lambda self: {  "prevCII" : CII() }  # default state for a new connection - no CII info transferred to client yet
    
    def __init__(self, maxConnectionsAllowed=-1, enabled=True, initialCII = CII(protocolVersion="1.1")):
        """\
        **Initialisation takes the following parameters:**
        
        :param maxConnectionsAllowed: (int, default=-1) Maximum number of concurrent connections to be allowed, or -1 to allow as many connections as resources allow.
        :param enabled: (bool, default=True) Whether the endpoint is initially enabled (True) or disabled (False)
        :param initialCII: (:class:`dvbcss.protocol.cii.CII`, default=CII(protocolVersion="1.1")) Initial value of CII state.
        """
        super(CIIServer,self).__init__(maxConnectionsAllowed=maxConnectionsAllowed, enabled=enabled)
        
        self.cii = initialCII.copy()
        """\
        A :class:`dvbcss.protocol.cii.CII` message object representing current CII state.
        Set the attributes of this object to update that state.
        
        When :func:`updateClients` is called, it is this state that will be sent to connected clients.
        """
    
    
    def updateClients(self, sendOnlyDiff=True,sendIfEmpty=False):
        """\
        Send update of current CII state from the :data:`CIIServer.cii` object to all connected clients.
        
        :param sendOnlyDiff: (bool, default=True) Send only the properties in the CII state that have changed since last time a message was sent. Set to False to send the entire message.
        :param sendIfEmpty: (bool, default=False) Set to True to force that a CII message be sent, even if it will be empty (e.g. no change since last time)
        
        By default this method will only send a CII message to clients informing them of the differencesin state since last time a message was sent to them.
        If no properties have changed at all, then no message will be sent.
        
        The two optional arguments allow you to change this behaviour. For example, to force the messages sent to include all properties, even if they have not changed:
        
        .. code-block:: python
        
            myCiiServer.updateClients(sendOnlyDiff=False)
            
        To additionally force it to send even if the CII state held at this server has no values for any of the properties:

        .. code-block:: python
        
            myCiiServer.updateClients(sendOnlyDiff=False, sendIfEmpty=True)
            
        """
        connections = self.getConnections()
        for webSock in connections:
            self.log.debug("Sending CII to connection "+webSock.id())
            connectionData = connections[webSock]
            prevCII = connectionData["prevCII"]
            
            # work out whether we are sending the full CII or a diff
            if sendOnlyDiff:
                diff = CII.diff(prevCII, self.cii)
                toSend = diff
                # enforce requirement that contentId must be accompanied by contentIdStatus
                if diff.contentId != OMIT:
                    toSend.contentIdStatus = self.cii.contentIdStatus
            else:
                toSend = self.cii
            
            # only send if forced to, or if the mesage to send is not empty (all OMITs)
            if sendIfEmpty or toSend.definedProperties():
                webSock.send(toSend.pack())
                
            connectionData["prevCII"] = self.cii.copy()

    def onClientConnect(self, webSock):
        """If you override this method you must call the base class implementation."""
        self.log.info("Sending initial CII message for connection "+webSock.id())
        webSock.send(self.cii.pack())
        self.getConnections()[webSock]["prevCII"] = self.cii.copy()
    
    def onClientDisconnect(self, webSock, connectionData):
        """If you override this method you must call the base class implementation."""
        pass
    
    def onClientMessage(self, webSock, message):
        """If you override this method you must call the base class implementation."""
        self.log.info("Received unexpected message on connection"+webSock.id()+" : "+str(message))
