.. py:module:: dvbcss.protocol.server.ts

==============
CSS-TS Servers
==============

Module: `dvbcss.protocol.server.ts`

.. contents::
    :local:
    :depth: 2

.. automodule:: dvbcss.protocol.server.ts
   :noindex:
   
Classes
-------

TSServer
''''''''

.. autoclass:: TSServer
   :members:
   :exclude-members: contentId
   :inherited-members:

   .. autoinstanceattribute:: contentId
      :annotation:

   .. autoinstanceattribute:: handler
      :annotation:
      
      Handler class for new connections.
      
      When mounting the CII server with cherrypy, include in the config dict a key 'tools.dvb_cii.handler_cls' with this handler class as the value.
      
      
TimelineSource
''''''''''''''

.. autoclass:: TimelineSource
   :members:
   :inherited-members:


SimpleTimelineSource
''''''''''''''''''''

.. autoclass:: SimpleTimelineSource
   :members:
   :inherited-members:
   
   

SimpleClockTimelineSource
'''''''''''''''''''''''''

.. autoclass:: SimpleClockTimelineSource
   :members:
   :inherited-members:

 
 
Functions
---------

ciMatchesStem
'''''''''''''

.. autofunction:: ciMatchesStem

isControlTimestampChanged
'''''''''''''''''''''''''

.. autofunction:: isControlTimestampChanged



