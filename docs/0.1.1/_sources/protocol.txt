.. py:module:: dvbcss.protocol

========================
DVB CSS Protocol modules
========================

Module: `dvbcss.protocol`

The :mod:`dvbcss.protocol` module contains classes to implement the CSS-CII, CSS-TS and CSS-WC protocols.
For each protocol there are objects to represent the messages that flow across the protocols and classes
that implement clients and servers for the protocols.

.. toctree::
   :maxdepth: 2
   
   cii.rst
   ts.rst
   wc.rst
   
See :doc:`servers-internals` for information on how the servers are implemented.

Common types and objects
------------------------

.. _private-data:

Signalling that a property is to be omitted from a message
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autodata:: OMIT
    :annotation: object

Private data
~~~~~~~~~~~~

Some protocol messages contain optional properties to carry private data.

Private data is encoded in message objects here as a :class:`list` of :class:`dict` objects
where each has a key "type" whose value is a URI.

Each dict can contain any other
keys and values you wish so long as they can be parsed by the python :mod:`json <json>` module's encoder.
For example:

.. code-block:: python

    example_private_data = [
        { "type" : "urn:bbc.co.uk:pid", "pid":"b00291843",
          "entity":"episode"
        },
        { "type" : "tag:bbc.co.uk/programmes/clips/link-url",
          "http://www.bbc.co.uk/programmes/b1290532/"
        }
    ]
    

Exceptions
~~~~~~~~~~

.. autoclass:: dvbcss.protocol.client.ConnectionError
