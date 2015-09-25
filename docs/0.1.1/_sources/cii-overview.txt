CSS-CII Protocol introduction
-----------------------------

**Here is a quick introduction to the CSS-CII protocol. For full details, refer to the**
`DVB specification <https://www.dvb.org/search/results/keywords/A167>`_.

The CSS-CII protocol is for sharing the server's (e.g. TV's) current
"Content Identifier and other Information" (yes really!) with the client (e.g.
companion). It also includes the URL of the :doc:`CSS-TS <ts>` and
:doc:`CSS-WC <wc>` servers so the client knows where to find them.

CII comprises a set of defined properties.  The server pushes state update
messages containing some or all properties (at minimum those that have changed).
How often these messages are pushed and which properties are included are
up to the server.

It is a WebSockets based protocol and messages are in JSON format.

.. contents::
    :local:
    :depth: 1


Sequence of interaction
~~~~~~~~~~~~~~~~~~~~~~~

The client is assumed to already know the WebSocket URL for the CSS-CII server
(for example: because the TV chooses to advertise it via a network service
discovery mechanism).

1. The client connects to the CSS-TS server. Either this is refused via an HTTP status code response,
or it is accepted.

2. The server immediately responds with a first CII state update message. This
contains (at minimum) all properties whose values are not null.

3. The server can re-send the CII state update message as often as it wishes.
At minimum it will do so when one or more of the properties have changed value.
The server will, at minimum, include the properties that have changed, but could
also include others in the message.

This protocol is a state update mechanism. The client is locally
mirroring the state of the TV by remembering the most recent values received
for each of the properties. When a message is received it updates that local
state and can react to any changes if it needs to.

Any messages sent by the client are ignored by the server.


CII message properties
~~~~~~~~~~~~~~~~~~~~~~

Every message sent by the server is a CII message and consists of a single JSON
object with zero, one, more or all of the following properties:

* ``protocolVersion`` - currently "1.1" and must be included in the first message sent by the server after the client connects.
* ``contentId`` - a URI representing the ID of the content being presented by the server.
  This will be a variant on a DVB URL ("dvb://") for DVB broadcast services, or the URL of  the MPD for MPEG DASH streams.
* ``contentIdStatus`` - whether the content Id is in its "final" form or whether it is a "partial" version until full information is available.
  For example: a DVB broadcast content ID might not include some elements until the TV detects certain metadata in the broadcast stream which can take a few seconds.
* ``presentationStatus`` - Primarily, whether presentation of the content is "okay", "transitioning" from one piece of content to the next, or in a "fault" condition.
  This can be extended by suffixing space separated additional terms after the primary term.
* ``mrsUrl`` - The URL of an MRS server.
* ``tsUrl`` - The WebSockets URL of the CSS-TS server that a client should use if it wants to do Timeline Synchronisation.
* ``wcUrl`` - The UDP URL ("udp://<host>:<port") of the CSS-WC server.
* ``teUrl`` - The WebSockets URL of the CSS-TE server that a client should use if it wants to receive Trigger Events.
* ``timelines`` - a list of zero, one or more timelines that the TV believes to be available for synchronising to.
* ``private`` - Extension mechanism to carry additional private data.

An example :class:`~dvbcss.protocol.cii.CII` message:

.. code-block:: json

	{
		"protocolVersion"    : "1.1",
		"mrsUrl"             : "http://css.bbc.co.uk/dvb/233A/mrs",
		"contentId"          : "dvb://233a.1004.1044;363a~20130218T0915Z--PT00H45M",
		"contentIdStatus"    : "partial",
		"presentationStatus" : "okay",
		"wcUrl"              : "udp://192.168.1.5:5800",
		"tsUrl"              : "ws://192.168.1.8:5815",
		"timelines" : [
			{
				"timelineSelector"   : "urn:dvb:css:timeline:temi:1:1",
				"timelineProperties" : {
					"unitsPerTick"   : 5,
					"unitsPerSecond" : 10
				}
			}
		]
	}

Another example where the contentId has changed, due to a channel change. The
server has chosen to omit properties that have not changed since the previous
message:

.. code-block:: json

	{
		"contentId"          : "dvb://233a.1004.1044;364f~20130218T1000Z--PT01H15M",
		"contentIdStatus"    : "partial",
	}
