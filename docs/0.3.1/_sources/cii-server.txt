.. py:module:: dvbcss.protocol.server.cii

===============
CSS-CII Servers
===============

Module: `dvbcss.protocol.server.cii`

.. contents::
    :local:
    :depth: 2

.. automodule:: dvbcss.protocol.server.cii
   :noindex:

Classes
-------

**CIIServer** - CII Server handler for cherrypy
'''''''''''''''''''''''''''''''''''''''''''''''

.. autoclass:: CIIServer
   :members:
   :exclude-members: cii
   :inherited-members:

   .. autoinstanceattribute:: cii
      :annotation:

   .. autoinstanceattribute:: handler
      :annotation:
      
      Handler class for new connections.
      
      When mounting the CII server with cherrypy, include in the config dict a key 'tools.dvb_cii.handler_cls' with this handler class as the value.
