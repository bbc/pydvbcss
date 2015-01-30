================
CSS-WC protocol
================

.. toctree::
    :maxdepth: 2
    
    wc-messages.rst
    wc-client.rst
    wc-server.rst

This package provides objects for representing messages exchanged via the DVB CSS-WC protocol and for implementing clients and servers.

The WC protocol is a simple UDP request response-protocol that enables simple
`clock synchronisation <http://en.wikipedia.org/wiki/Network_Time_Protocol#Clock_synchronization_algorithm>`_ algorithms to
be used to establish a common *wall clock* between a server and client.

There is a :class:`~dvbcss.protocol.server.wc.WallClockServer` class providing a self contained Wall Clock server.
The :class:`~dvbcss.protocol.client.wc.WallClockClient` is designed to allow different algorithms to be plugged in for acting on
the results of the request-response interaction to adjust a local :mod:`~dvbcss.clock` object to match the Wall Clock of the
server.

Modules for using the CSS-WC protocol:

* :mod:`dvbcss.protocol.wc` : objects for representing and packing/unpacking the protocol messages.

* :mod:`dvbcss.protocol.client.wc` : implementation of a client for a CSS-WC connection.

* :mod:`dvbcss.protocol.client.wc.algorithm` : algorithms to be used with a CSS-WC client.

* :mod:`dvbcss.protocol.server.wc` : implementation of a server for a CSS-WC connection.

