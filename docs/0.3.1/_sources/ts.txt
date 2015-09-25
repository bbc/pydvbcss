===============
CSS-TS protocol
===============

.. toctree::
    :maxdepth: 2
    
    ts-overview.rst
    ts-messages.rst
    ts-client.rst
    ts-server.rst

This package provides objects for representing messages exchanged via the DVB CSS-TS protocol and for implementing clients and servers.

The TS protocol is a mechanism for a server to share timeline position and playback speed with a client. In effect it enables a client to synchronise its
understanding of the progress of media presentation with that of a server, in terms of a particular timeline.

The client initially sends a :class:`~dvbcss.protocol.ts.SetupData` message to specify what timeline it wants to synchronise in terms of.
The server then periodically sends :class:`~dvbcss.protocol.ts.ControlTimestamp` messages to inform the client of the state of presentation timing.
The client can also send :class:`AptEptLpt <dvbcss.protcool.ts.AptEptLpt>` (Actual, Earliest and Latest Presentation Timestamp) messages to the server
to inform it of its playback timing and range of playback timings it can achieve.

The client implementation in this library can control a :class:`~dvbcss.clock.CorrelatedClock`, synchronising it to the timeline.
The server implementation in this library uses :class:`~dvbcss.clock.CorrelatedClock` objects as its source of timelines that it
is to share with clients.


Modules for using the CSS-TS protocol:

* :mod:`dvbcss.protocol.ts` : objects for representing and packing/unpacking the CSS-TS protocol messages.

* :mod:`dvbcss.protocol.client.ts` : implementation of a client for a CSS-TS connection.

* :mod:`dvbcss.protocol.server.ts` : implementation of a server for a CSS-TS connection.

