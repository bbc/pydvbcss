.. py:module:: dvbcss.protocol.wc

=======================
CSS-WC Message objects
=======================

Module: `dvbcss.protocol.wc`

.. contents::
    :local:
    :depth: 2

.. automodule:: dvbcss.protocol.wc
   :noindex:
   
Classes
~~~~~~~

WCMessage
---------

 .. autoclass:: WCMessage
   :members:
   :exclude-members: msgtype, precision, maxFreqError, originateNanos, receiveNanos, transmitNanos, originalOriginate
   :inherited-members:

   .. autoinstanceattribute:: msgtype
      :annotation:
      
   .. autoinstanceattribute:: precision
      :annotation:
      
   .. autoinstanceattribute:: maxFreqError
      :annotation:
      
   .. autoinstanceattribute:: originateNanos
      :annotation:
      
   .. autoinstanceattribute:: receiveNanos
      :annotation:
      
   .. autoinstanceattribute:: transmitNanos
      :annotation:
      
   .. autoinstanceattribute:: originalOriginate
      :annotation:
      


Candidate
---------

 .. autoclass:: Candidate
   :members:
   :exclude-members: t1, t2, t3, t4, offset, rtt, isNanos, precision, maxFreqError, msg
   :inherited-members:

   .. autoinstanceattribute:: t1
      :annotation: = msg.originateNanos
      
   .. autoinstanceattribute:: t2
      :annotation: = msg.receiveNanos
      
   .. autoinstanceattribute:: t3
      :annotation: = msg.transmitNanos
      
   .. autoinstanceattribute:: t4
      :annotation: = nanosRx
      
   .. autoinstanceattribute:: offset
      :annotation: = ((t3+t2)-(t4+t1))/2
      
   .. autoinstanceattribute:: rtt
      :annotation: = (t4-t1)-(t3-t2)
      
   .. autoinstanceattribute:: isNanos
      :annotation: = True
      
   .. autoinstanceattribute:: precision
      :annotation: = msg.getPrecision()
      
   .. autoinstanceattribute:: maxFreqError
      :annotation: = msg.getMaxFreqError()
      
   .. autoinstanceattribute:: msg
      :annotation: = WCMessage
 