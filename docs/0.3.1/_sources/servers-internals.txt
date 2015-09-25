.. _servers-internals:
.. py:module:: dvbcss.protocol.server

======================================
Protocol server implementation details
======================================

.. contents::
   :local:
   :depth: 2
   
CSS-WC
------

Overview
^^^^^^^^

The CSS-WC server is based on a simple generic framework for building UDP servers

Classes
^^^^^^^

.. autoclass:: dvbcss.protocol.server.wc.UdpRequestServer
   :members:
   :inherited-members:
  
.. autoclass:: dvbcss.protocol.server.wc.WallClockServerHandler
   :members:
   :inherited-members:

   
CSS-CII and CSS-TS
------------------

Module: `dvbcss.protocol.server`

Overview
^^^^^^^^

The CSS-CII and CSS-TS servers subclass the WebSocket server functionality for cherrypy implemented
by ws4py in the :mod:`~ws4py.server.cherrypyserver` module.

:class:`~cii.CIIServer` and :class:`~ts.TSServer` both inherit from a common base implementation
:class:`WSServerTool` provided in the `dvbcss.protocol.server` module.

The Tool provides the hook into cherrypy for handling the connection request and upgrading it to a
WebSocket connection, spawning an object representing the WebSocket connection and which implements
the WebSocket protocols.

The base server object class is intended to manage all WebSocket connections for a particular server
endpoint. It therefore provides its own customised WebScoket class that is bound to that particular
server object instance.

The tool is enabled via an "on" configuration when setting up the mount point in cherrypy.
The tool also expects to a "handler_cls" property set in the configuration at the mount point.
This property points to a WebSocket class which can be instantiated to handle the connection.

Example usage: creating a server at "ws://<host>:80/endpoint" just using the base classes provided here:

.. code-block:: python

    import cherrypy
    from ws4py.server.cherrypyserver import WebSocketPlugin
    from dvbcss.protocol.server import WSServerBase, WSServerTool

    # plug the tool into cherrypy as "my_server"
    cherrypy.tools.my_server = WSServerTool()

    WebSocketPlugin(cherrypy.engine).subscribe()
    
    # create my server
    myServer = WSServerBase()

    # bind it to the URL path /endpoint in the cherrypy server
    class Root(object):
        @cherrypy.expose
        def endpoint(self):
            pass
    
    cfg = {"/endpoint": {'tools.my_server.on': True,
                    'tools.my_server.handler_cls': myServer.handler
                   }
          }
    
    cherrypy.tree.mount(Root(), "/", config=cfg)    

    # activate cherrypy web server on port 80
    cherrypy.config.update({"server.socket_port":80})
    cherrypy.engine.start()


See documentation for :class:`WSServerBase` for information on creating subclasses to implement specific endpoints.


Classes
^^^^^^^

.. autoclass:: dvbcss.protocol.server.ConnectionIdGen
   :members:
   :inherited-members:

.. autoclass:: dvbcss.protocol.server.WSServerTool
   :members:
   :inherited-members:

.. autoclass:: dvbcss.protocol.server.WSServerBase
   :members:
   :exclude-members: handler
   :inherited-members:
   :private-members:
   
   .. autodata:: loggingName, getDefaultConnectionData, connectionIdPrefix

   .. autoinstanceattribute:: handler
      :annotation:

   .. autoinstanceattribute:: _connections
      :annotation:

   .. :method: _makeHandlerClass
   
.. class:: .WebSocketHandler(WebSocket)
    
    This class is created and returned by the :func:`WSServerBase._makeHandlerClass` method
    and each class returned is bound to the instance of :class:`WSServerBase` that created it.
    
    It is intended to be provided to cherrypy as the "handler_cls" configuration parameter for the WebSocket tool.
    It is instantiated for every connection made.
    
    These are subclasses of the ws4py :class:`~ws4py.websocket.WebSocket` class and represent an individual WebSocket connection.
    
    Instances of this class call through to :func:`WSServerBase._addConnection` and :func:`WSServerBase._removeConnection`
    and :func:`WSServerBase._receivedMessage` to inform the parent server of the WebSocket opening, closing and receiving messages.
    
    .. classmethod:: isEnabled(cls)
                
       :return: True if the server endpoint is enabled, otherwise False.

    .. classmethod:: canAllocateConnection(cls)
       
       :return: True only if the connection limit of the parent server has not yet been reached. Otherwise False.

    .. method:: id(self)
    
       :return: A human readable connection ID
