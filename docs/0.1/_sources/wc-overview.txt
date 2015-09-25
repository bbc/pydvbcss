CSS-WC Protocol Introduction
----------------------------

**Here is a quick introduction to the CSS-WC protocol. For full details, refer to the**
`DVB specification <https://www.dvb.org/search/results/keywords/A167>`_.

The CSS-WC protocol is for establishing *Wall clock synchronisation* - meaning
that there is a common synchronised sense of time (a "wall clock") between the
server (e.g. TV) and client (e.g. companion). This common wall clock is used
in the CSS-TS protocol to make it immune to network delays.

The client uses the information carried in the protocol to estimate the server
wall clock and attempt to compensate for network latency.  This is a
connectionless UDP protocol similar to NTP's client-server mode of
operation, but much simplified and not intended to set the system real-time
clock.

.. contents::
    :local:
    :depth: 1

Sequence of interaction
~~~~~~~~~~~~~~~~~~~~~~~

The client is assumed to already know the host and port number of the CSS-WC
server (usually from the information received via the
:doc:`CSS-CII protocol <cii>`).

1. The client sends a Wall Clock protocol "request" message to the server.
   
2. The server sends back a Wall Clock protocol "response" message to the client.

3. If the server is able to more accurately measure when it sent a message
*after* it has done so, then it can optionally send a "follow-up response" with
this information.

The client repeats this process as often as it needs to.

Synchronising the wall clock
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The client notes the time at which the request is sent and the response received,
and by the server including the times at which it received the request and
sent its response. Using this information the client can estimate the difference
between the time of its clock and that of the server. It can also calculate
an error bound on this (known as dispersion):

    .. image:: wc-request-response.png
       :width: 128pt
       :align: center
    
Estimated offset = (( *t3* + *t2* ) - ( *t4* + *t1* )) / 2
 
The `DVB specification <https://www.dvb.org/search/results/keywords/A167>`_
contains an annex that goes into more detail on the
theory of how to calculate dispersion and how a client can use this
as part of a simple algorithm to align its wall clock.
 

Message format
~~~~~~~~~~~~~~

Requests and responses both have the same fixed 32 byte binary message format.
A :class:`~dvbcss.protocol.wc.WCMessage` carries the following fields:

* Protocol **version** identifier
* Message **type** (request / response / response-before-follow-up / follow-up)
* The **precision** of the server's wall clock
* The **maximum frequency error** of the server's wall clock
* Timevalues (in NTP 64-bit time format, comprising a 32bit word carrying the
  number of nanoseconds and another 32bit word containing the number of seconds)

  * **Originate timevalue:** when the client sent the request.
  * **Receive timevalue:** when the server received the request.
  * **Transmit timevalue:** when the server sent the response.
  
The *precision*, *max freq error*, *receive timevalue* and *transmit timevalue* fields only
have meaning in a response from a server. Their values do not matter in requests.