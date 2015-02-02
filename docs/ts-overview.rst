CSS-TS Protocol introduction
----------------------------

**Here is a quick introduction to the CSS-TS protocol. For full details, refer to the** `DVB specification <https://www.dvb.org/search/results/keywords/A167>`_.

The CSS-TS protocol is for *Timeline Synchronisation*. Via this protocol,
the server (e.g. TV) pushes timestamps to the client (e.g. companion) to keep
it up-to-date on the progress of a particular timeline (chosen by the client).

A client can also report its own timing and what range of timings it can
cope with. This allows the client to negotiate a mutually achievable
timing with the server.

It is a WebSockets based protocol and messages are in JSON format.

.. contents::
    :local:
    :depth: 1

Sequence of interaction
~~~~~~~~~~~~~~~~~~~~~~~

The client is assumed to already know the WebSocket URL for the CSS-TS server
(usually from the information received via the :doc:`CSS-CII protocol <cii>`).

1. The client connects to the CSS-TS server. Either this is refused via an HTTP status code response,
or it is accepted.

2. The client then immediately sends an initial :class:`~dvbcss.protocol.ts.SetupData` message to request the
timeline to synchronise with.

3. The server then starts sending back :class:`~dvbcss.protocol.ts.ControlTimestamp` messages that update the
client as to the state of that timeline. This state says either that the timeline is currently
unavailable, or that it is available, and here is how to calculate the timeline position from
the wall clock position.The server sends as frequently or infrequently as it likes, but will at least send
them if there is a meaningful change in the timeline.

4. The client can, optionally, send its own :class:`~dvbcss.protocol.ts.AptEptLpt` messages to inform the server
of what it is doing, and the range of different timings it can achieve for its media (e.g.
what is the earliest and latest timings it can achieve). However this is purely informative. 
A server is not obliged to do anything with this information.


Determining timeline selection and availability
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The :class:`~dvbcss.protocol.ts.SetupData` message conveys to the CSS-TS server details of what timeline the client
wants to synchronise to.

The CSS-TS server determines, at any given moment, if a timeline is available by checking if:

1. the stem matches the current content identifier for what is being presented at the server
   (meaning that the stem matches the left hand most subset of the content id);

2. and the timeline selector identifies a timeline that exists for the content being presented at the server.

While the above is true, the timeline is "available". While it is not true, it is "unavailable".
The CSS-TS connection is kept open irrespective of timeline availability. The server indicates
changes in availability via the :class:`~dvbcss.protocol.ts.ControlTimestamp` messages it sends.

Example :class:`~dvbcss.protocol.ts.SetupData` message; requesting a PTS timeline for
a particular DVB broadcast channel, but not being specific about which event (programme in the EPG):

.. code-block:: json

	{
		"contentIdStem"    : "dvb://233a.1004.1044",
		"timelineSelector" : "urn:dvb:css:timeline:pts"
	}


What does a timestamp convey?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

It represents a relationship between Wall Clock time and the timeline of the content being presented by the TV Device.
It is sometimes referred to as a *(point of) correlation* between the wall clock and the timeline.

This relationship can be visualised as a line that maps from wall clock time (on one axis) to timeline time (on the other axis).
The (content-time, wall-clock-time) correlation is a point on the line. The timelineSpeedMultiplier represents the slope.
The tick rates of each timeline are the units (the scale of each axis).

The CSS-TS server sends :class:`~dvbcss.protocol.ts.ControlTimestamp` messages to clients, and clients can, optionally, send back :class:`AptEptLpt`
messages.

A ControlTimestamp can also tell a client if a timeline is unavailable by having null values for the contentTime
and timelineSpeedMultiplier properties. Non-null values mean the timeline is available.

:class:`~dvbcss.protocol.ts.AptEptLpt` messages enables a client to inform a server of what time it is presenting at (the "actual" part of the timestamp)
and also to indicate the earliest and latest times it could present. It is, in effect, three correlations bundled into one message,
to represent each of these three aspects.
Earliest and Latest correlations are allowed to have -infinity and +infinity for the wall clock time to indicate that the client
has no limits on how early, or late, it can present.

An example :class:`~dvbcss.protocol.ts.ControlTimestamp` indicating the timeline is unavailable:

.. code-block:: json

	{
		"contentTime"             : null,
		"wallClockTime"           : "116012000000",
		"timelineSpeedMultiplier" : null
	}

An example :class:`~dvbcss.protocol.ts.ControlTimestamp` providing a correlation
for an available timeline:

.. code-block:: json


	{
		"contentTime"             : "834188",
		"wallClockTime"           : "116012000000",
		"timelineSpeedMultiplier" : 1.0
	}

An example of an :class:`~dvbcss.protocol.ts.AptEptLpt` message, indicating
the current presentation timing being used by the client; a limit on how early
it can present; but no limit on how long it can delay (buffer):

.. code-block:: json

	{
		"actual" : {
			"contentTime"   : "834190",
			"wallClockTime" : "115992000000"
		},
		"earliest" : {
			"contentTime"   : "834190",
			"wallClockTime" : "115984000000"
		},
		"latest" : {
			"contentTime"   : "834190",
			"wallClockTime" : "plusinfinity"
		}
	}


