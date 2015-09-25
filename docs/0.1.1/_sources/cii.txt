================
CSS-CII protocol
================

.. toctree::
    :maxdepth: 2
    
    cii-overview.rst
    cii-messages.rst
    cii-client.rst
    cii-server.rst

This package provides objects for representing messages exchanged via the DVB CSS-CII protocol and for implementing clients and servers.

The CII protocol is a mechanism for sending state updates from server to client. The state of the server can be represented by a 
:class:`~dvbcss.protocol.cii.CII` message where every property is populated with a value.
The server can send complete CII messages or partial ones containing only the properties that have
changed value since the last message. The client must track these changes to maintain its own local up-to-date copy of the complete state.


Modules for using the CSS-CII protocol:

* :mod:`dvbcss.protocol.cii` : objects for representing and packing/unpacking the CSS-CII protocol messages.

* :mod:`dvbcss.protocol.client.cii` : implementations of a client for a CSS-CII connection.

* :mod:`dvbcss.protocol.server.cii` : implementations of a server for a CSS-CII connection.

