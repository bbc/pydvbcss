.. _examples:
	example code

.. py:module:: examples
	
================
Run the examples
================

The code in the `examples` directory demonstrates how to create and control
servers and clients for all three protocols: CSS-CII, CSS-TS and CSS-WC.

.. contents::
   :local:
   :depth: 1

There are instructions below on how to run the examples and see them interact with each other.

See the sources here: :repo:`on github </examples>`
   
**WallClockServer.py** and **WallClockClient.py**
=================================================

Get started
-----------

The *WallClockServer* and *WallClockClient* examples use the library to
implement a simple server and client for the :doc:`wc`.

First start the server, specifying the host and IP to listen on:

.. code-block:: shell

    $ python examples/WallClockServer.py 127.0.0.1 6677

Leave it running in the background and start a client, telling it where to connect to the server:

.. code-block:: shell

    $ python examples/WallClockClient.py 127.0.0.1 6677

.. note::

    The wall clock protocol is connectionless (it uses UDP) This means the client will not report an error if
    you enter the wrong IP address or port number.
    
    Watch the "dispersion" values which indicate how
    much margin for error there is in the client's wall clock estimate. If the value is very large, this
    means it is not receiving responses from the server.


How they work
-------------

WallClockServer.py :repo:`[source] </examples/WallClockServer.py>`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: examples.WallClockServer
   :noindex:
   
WallClockClient.py :repo:`[source] </examples/WallClockClient.py>`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: examples.WallClockClient
   :noindex:




**CIIServer.py** and **CIIClient.py**
=====================================

Get started
-----------

The `CIIServer` and `CIIClient` examples implement the *CSS-CII*
protocol, with the server sharing some pretend CII status information with
the client. 

First start the server:

    $ python examples/CIIServer.py

The server listens on 127.0.0.1 on port 7681 and accepts WebSocket connections to `ws://<ip>:<port>/cii`.

Leave it running in the background and connect using the client and see how
the CII data is pushed by the server whenever it changes:

    $ python examples/CIIClient.py ws:/127.0.0.1:7681/cii



How they work
-------------

CIIServer.py :repo:`[source] </examples/CIIServer.py>`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: examples.CIIServer
   :noindex:
   

CIIServer.py :repo:`[source] </examples/CIIClient.py>`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: examples.CIIClient
   :noindex:
   



**TSServer.py** and **TSClient.py**
===================================

Get started
-----------

The `TServer` and `TSClient` examples implement the *CSS-TS* protocol, with the
server pretending to have a few different timelines for a DVB broadcast service (where the content ID is a DVB URL).

First start the server:

.. code-block:: shell

    $ python examples/TSServer.py
    
The server listens on 127.0.0.1 on port 7681 and accepts WebSocket connections to `ws://<ip>:<port>/ts`.
It also includes a wall clock server, also on 127.0.0.1 on port 6677. 

Leave it running in the background and connect using the client and see
how the client is able to synchronise and periodically print an estimate of the timeline position (converted to units of seconds):

.. code-block:: shell

    $ python examples/TSClient.py ws://127.0.0.1:7681/ts udp://127.0.0.1:6677 "dvb://" "urn:dvb:css:timeline:pts" 90000

Here we have told it to request a timeline for whatever content the server thinks it is showing provided that the content ID begins with "dvb://".
Assuming that matches, then the timeline is to be a PTS timeline, which ticks at 90kHz (the standard rate of PTS in an MPEG transport stream).



How they work
-------------

TSServer.py :repo:`[source] </examples/TSServer.py>`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: examples.TSServer
   :noindex:
   

TSClient.py :repo:`[source] </examples/TSClient.py>`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: examples.TSClient
   :noindex:
   
   
   
**TVDevice.py**
===============

Get started
-----------

This is a very simple example of a server running all three protocols (CSS-WC, CSS-TS and CSS-CII).
It pretends to be showing a DVB broadcast service and able to provide a PTS or TEMI timeline for it.

First start the server:

.. code-block:: shell

    $ python examples/TVDevice.py
    
While we leave it running in the background, we can try to interact with it using the various example
clients described above.

By default it provides a wall clock server on 127.0.0.1 port 6677

.. code-block:: shell

    $ python examples/WallClockClient.py 127.0.0.1 6677

... and a CSS-CII server that can be reached at `ws://127.0.0.1:7681/cii`

.. code-block:: shell

    $ python examples/CIIClient.py ws:/127.0.0.1:7681/cii
    
... and a CSS-TS server that can be reached at `ws://127.0.0.1:7681/ts`
    
.. code-block:: shell

    $ python examples/TSClient.py ws://127.0.0.1:7681/ts udp://127.0.0.1:6677 "dvb://" "urn:dvb:css:timeline:temi:1:1" 1000



How it works
------------

TVDevice.py :repo:`[source] </examples/TVDevice.py>`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: examples.TVDevice
    :noindex:
