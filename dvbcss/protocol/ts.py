#!/usr/bin/env python
#
# Copyright 2015 British Broadcasting Corporation
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

r"""\
A :class:`~dvbcss.protocol.ts.SetupData` object represents a setup-data message sent by a client to a server
immediately after opening a CSS-TS protocol connection.

A :class:`ControlTimestamp` object represents a Control Timestamp message sent by the server
to the client.

A :class:`AptEptLpt` object represents an Actual, Earliest and Latest Presentation Timestamp
message that may be sent by a client to the server.

The :class:`Timestamp` objects are used in the above message objects to represent the
relationship between wall clock time and content (timeline) time.


Examples
--------

SetupData examples:

.. code-block:: python

    >>> from dvbcss.protocol.ts import SetupData
    >>> from dvbcss.protocol import OMIT
    
    >>> s = SetupData(timelineSelector="urn:dvb:css:timeline:pts", ciStem="dvb://1004")
    >>> s.pack()
    '{"timelineSelector": "urn:dvb:css:timeline:pts", "contentIdStem": "dvb://1004"}'
    
.. code-block:: python

    >>> jsonMessage = \"""\
    ... { "timelineSelector":"urn:dvb:css:timeline:temi:1:1",
    ...   "contentIdStem":""
    ... }
    ... \"""
    >>> SetupData.unpack(jsonMessage)
    SetupData(ciStem="", timelineSelector="urn:dvb:css:timeline:temi:1:1", private=OMIT)

ControlTimestamp examples:

.. code-block:: python

    >>> from dvbcss.protocol.ts import ControlTimestamp, Timestamp

    >>> t = Timestamp(contentTime=12345, wallClockTime=900028432)
    >>> ct = ControlTimestamp(timestamp=t, timelineSpeedMultiplier=1)
    >>> ct.pack()
    '{"timelineSpeedMultiplier": 1.0, "wallClockTime": "900028432", "contentTime": "12345"}'

.. code-block:: python

    >>> jsonMessage = \"""\
    ... { "contentTime" : "1003847",
    ...   "wallClockTime" : "348957623498576",
    ...   "timelineSpeedMultiplier" : 2.0
    ... }
    ... \"""
    >>> c = ControlTimestamp.unpack(jsonMessage)
    >>> c.timestamp.contentTime
    1003847
    >>> c.timestamp.wallClockTime
    348957623498576
    >>> c.timelineSpeedMultiplier
    2.0

Actual, Earliest and Latest Presentation Timestamp examples:

.. code-block:: python

    >>> from dvbcss.protocol.ts import AptEptLpt, Timestamp
    
    >>> te = Timestamp(contentTime=123465, wallClockTime=float("-inf"))
    >>> tl = Timestamp(contentTime=123465, wallClockTime=float("+inf"))
    >>> ael = AptEptLpt(earliest=te, latest=tl)
    >>> ael.pack()
    '{"earliest": {"wallClockTime": "minusinfinity", "contentTime": "123465"}, "latest": {"wallClockTime": "plusinfinity", "contentTime": "123465"}}'
    
.. code-block:: python

    >>> jsonMessage = \"""\
    ... { "earliest" : { "contentTime" : "1000", "wallClockTime": "10059237" },
    ...   "latest"   : { "contentTime" : "1000", "wallClockTime": "19284782" },
    ...   "actual"   : { "contentTime" : "1005", "wallClockTime": "10947820" }
    ... }
    ... \"""
    >>> ael=AptEptLpt.unpack(jsonMessage)
    >>> ael.actual.contentTime
    1005
    >>> ael.actual.wallClockTime
    10947820


.. _plus-minus-infinity:

+/- infinity
------------

For certain timestamp messages it is permissible to convey a time value that is either plus or minus infinity.
Use the python :class:`float` to express these values as follows:

.. code-block:: python

    >>> float("+inf")
    inf
    
    >>> float("-inf")
    -inf

"""

import json
import logging

from dvbcss.protocol.transformers import encodeOneOf, decodeOneOf
from dvbcss.protocol.transformers import Transformer
from dvbcss.protocol import OMIT

class SetupData(object):
    def __init__(self, contentIdStem, timelineSelector, private=OMIT):
        """\
        Object representing a CSS-TS Setup-Data message.
        
        This carries a content identifier stem and a timeline selector string, and is used, in effect,
        to request the timeline to be synchronised to via the CSS-TS protocol.
        
        **Initialisation takes the following parameters:**
        
        :param str contentIdStem: The content identifier stem.
        :param str timelineSelector: The timeline selector
        :param private: Optional private data.
        :type private: :obj:`~dvbcss.protocol.OMIT` or :ref:`private-data`
        
        The attributes of the object have the same name as the SetupData message properties:
        
        * :data:`contentIdStem`
        * :data:`timelineSelector`
        * :data:`private`
            
        Converting to and from JSON representation is performed using the :func:`pack` method and :func:`unpack` class method.
        Properties set to equal :data:`~dvbcss.protocol.OMIT` will be omitted when the message
        is packed to a JSON representation.
        """
        super(SetupData,self).__init__()
        
        self.contentIdStem = contentIdStem       #: (read/write :class:`str`) The stem (subset starting from the LHS) of a content identifier
        self.timelineSelector = timelineSelector #: (read/write :class:`str`) The timeline selector
        self.private = private                   #: (read/write :obj:`~dvbcss.protocol.OMIT` or :ref:`private-data`) Optional private data.
        
        
        self.log = logging.getLogger("dvbcss.protocol.ts.SetupData")
        
    def pack(self):
        """\
        :returns: string containing JSON representation of this message.
        :throws ValueError: if there are values for properties that are not permitted.
        """
        struct = {}
        struct["contentIdStem"] = str(self.contentIdStem)
        struct["timelineSelector"] = str(self.timelineSelector)
        if self.private is not OMIT:
            struct["private"] = encodeOneOf(self.private,"Not a valid private property.", Transformer.private)
        return json.dumps(struct)

    @classmethod
    def unpack(cls, msg):
        """\
        Convert JSON string representation of this message encoded as a :class:`SetupData` object.
        
        :throws ValueError: if not possible.
        """
        struct = json.loads(msg)
        opt={}
        if "private" in struct:
            opt["private"] = decodeOneOf(struct["private"],"Not a valid private property.", Transformer.private)
        try:
            return SetupData(contentIdStem = struct["contentIdStem"], timelineSelector = struct["timelineSelector"], **opt)
        except KeyError:
            raise ValueError("Not all fields in SetupData message present as expected")
        
    def __str__(self):
        return self.__repr__()
    
    def __repr__(self):
        return 'SetupData(contentIdStem="%s", timelineSelector="%s", private=%s)' % (self.contentIdStem, self.timelineSelector, repr(self.private))

    def copy(self):
        """:returns: a copy of this SetupData object. Note that this does NOT deep copy any private data."""
        return SetupData(self.contentIdStem, self.timelineSelector, self.private)


class Timestamp(object):

    def __init__(self, contentTime, wallClockTime):
        """\
        Object representing a Timestamp part(s) of a :class:`ControlTimestamp` or :class:`AptEptLpt` object.

        **Initialisation takes the following parameters:**
        
        :param contentTime: The content time (time on timeline) part of a timestamp
        :type contentTime: :obj:`None` or :class:`int`
        :param wallClockTime: The wall clock time part of a timestamp
        :type wallClockTime: :class:`int` or :ref:`plus-minus-infinity` :class:`float` ("+inf") or :class:`float` ("-inf")

        The values for contentTime and wallClockTime are allowed to be arbitrarily large precision integers because they are carried as a string
        in the JSON representation.

        The attributes of the object have the same name as the corresponding message properties:
        
        * :data:`contentTime`
        * :data:`wallClockTime`
            
        Converting to and from JSON representation is performed using the :func:`pack` method and :func:`unpack` class method.
        """
        super(Timestamp,self).__init__()
        self.contentTime=contentTime    #: (read/write :obj:`None` or large :class:`int`) The content time part of a timestamp
        self.wallClockTime=wallClockTime #: (read/write large :class:`int` or :class:`float("+inf")` or :class:`float("-inf")` ) The wall clock time part of a timestamp 
        self.log = logging.getLogger("dvbcss.protocol.ts.Timestamp")

    def __str__(self):
        return self.__repr__()
    
    def __repr__(self):
        return 'Timestamp(contentTime=%s, wallClockTime=%s)' % (repr(self.contentTime), repr(self.wallClockTime))

    def copy(self):
        return Timestamp(self.contentTime, self.wallClockTime)


class ControlTimestamp(object):
    def __init__(self, timestamp, timelineSpeedMultiplier):
        """\
        Object representing a CSS-TS Control Timestamp message.
        
        **Initialisation takes the following parameters:**
        
        :param Timestamp timestamp: carries the `contentTime` and `wallClockTime` properties of the Control Timestamp
        :param timelineSpeedMultiplier: the timeline speed multiplier
        :type timelineSpeedMultiplier: :class:`float` or :obj:`None`
        
        The attributes of the object have the following relationship to the message properties:
        
        * :data:`timestamp`
        * :data:`timelineSpeedMultiplier`
            
        Converting to and from JSON representation is performed using the :func:`pack` method and :func:`unpack` class method.
        """
        super(ControlTimestamp,self).__init__()
        self.timestamp = timestamp #: (read/write :class:`Timestamp`) :class:`Timestamp` object representing the contentTime and wallClockTime parts of the timestamp)
        self.timelineSpeedMultiplier = timelineSpeedMultiplier #: (read/write :class:`float` or :obj:`None`) Timeline speed. For example: 1 = normal, 0 = pause, -0.5 = half speed reverse. Use `None` only when the Control Timestamp is supposed to indicate that the timeline is unavailable.
        self.log = logging.getLogger("dvbcss.protocol.ts.ControlTimestamp")
        
    def pack(self):
        """\
        :returns: string containing JSON representation of this message.
        :throws ValueError: if there are values for properties that are not permitted.
        """
        struct = {}
        
        struct["contentTime"]             = encodeOneOf(self.timestamp.contentTime,   "Not a valid Control Timestamp contentTime.",             Transformer.null, Transformer.intAsString)
        struct["wallClockTime"]           = encodeOneOf(self.timestamp.wallClockTime, "Not a valid Control Timestamp wallClockTime.",           Transformer.intAsString)
        struct["timelineSpeedMultiplier"] = encodeOneOf(self.timelineSpeedMultiplier, "Not a valid Control Timestamp timelineSpeedMultiplier.", Transformer.null, Transformer.float)
        return json.dumps(struct)
    
    @classmethod
    def unpack(cls, msg):
        """\
        Convert JSON string representation of this message encoded as a :class:`ControlTimestamp` object.
        
        :throws ValueError: if not possible.
        """
        struct = json.loads(msg)
        contentTime             = decodeOneOf(struct["contentTime"],             "Not a valid Control Timestamp contentTime.",             Transformer.null, Transformer.intAsString)
        wallClockTime           = decodeOneOf(struct["wallClockTime"],           "Not a valid Control Timestamp wallClockTime.",           Transformer.intAsString)
        timelineSpeedMultiplier = decodeOneOf(struct["timelineSpeedMultiplier"], "Not a valid Control Timestamp timelineSpeedMultiplier.", Transformer.null, Transformer.float)
        
        if (contentTime is None) != (timelineSpeedMultiplier is None):
            raise ValueError("Both contentTime and timelineSpeedMutliplier must be null, or neither must be null. Cannot be only one of them.")
        
        return ControlTimestamp(Timestamp(contentTime, wallClockTime), timelineSpeedMultiplier)

    def __str__(self):
        return self.__repr__()
    
    def __repr__(self):
        return 'ControlTimestamp(timestamp=%s, timelineSpeedMultiplier=%s)' % (repr(self.timestamp), repr(self.timelineSpeedMultiplier))

    def copy(self):
        """:returns: a deep copy of this Control Timestamp object"""
        return ControlTimestamp(self.timestamp.copy(), self.timelineSpeedMultiplier)


class AptEptLpt(object):
    
    def __init__(self, actual=OMIT, earliest=Timestamp(0,float("-inf")), latest=Timestamp(0,float("+inf"))):
        """\
        Object representing a CSS-TS Actual, Earliest and Latest Presentation Timestamp message.
        
        **Initialisation takes the following parameters:**
        
        :param actual: Optional timestamp representing the actual presentation timing
        :type actual: :obj:`~dvbcss.protocol.OMIT` or :class:`Timestamp`
        :param earliest: Timestamp representing the earliest possible presentation timing
        :type earliest: :obj:`~dvbcss.protocol.OMIT` or :class:`Timestamp`
        :param latest: Timestamp representing the latest possible presentation timing
        :type latest: :obj:`~dvbcss.protocol.OMIT` or :class:`Timestamp`
        
        For the *actual presentation timestamp*, the contentTime and wallClockTime must both be non-null integer values.
                
        For the *earliest presentation timestamp*, the contentTime must be a non-null integer. wallClockTime can be a
        non-null integer or :ref:`plus infinity <plus-minus-infinity>`
        
        For the *latest presentation timestamp*, the contentTime must be a non-null integer. wallClockTime can be a
        non-null integer or :ref:`minus infinity <plus-minus-infinity>`
        
        The attributes of the object have the same names as the Actual, Earliest and Latest presentation timestamp message properties:
        
        * :data:`actual`
        * :data:`earliest`
        * :data:`latest`
            
        Converting to and from JSON representation is performed using the :func:`pack` method and :func:`unpack` class method.
        If values of properties do not meet the requirements described above, then :func:`pack` will raise :class:`ValueError` exceptions.
        """
        super(AptEptLpt,self).__init__()
        self.actual=actual     #: (read/write :data:`OMIT` or :class:`Timestamp`) Actual presentation timestamp
        self.earliest=earliest #: (read/write :class:`Timestamp`) Earliest presentation timestamp. The wallClockTime property must be an :class:`int` or :class:`float("+inf")`. It must not be :class:`float("-inf")`.
        self.latest=latest     #: (read/write :class:`Timestamp`) Latest presentation timestamp. The wallClockTime property must be an :class:`int` or :class:`float("-inf")`. It must not be :class:`float("+inf")`.
        self.log = logging.getLogger("dvbcss.protocol.ts.AptEptLpt")
        
    def pack(self):
        """\
        :returns: string containing JSON representation of this message.
        :throws ValueError: if there are values for properties that are not permitted.
        """
        struct={}
        if self.actual != OMIT:
            struct["actual"] = {
                "contentTime"   : encodeOneOf(self.actual.contentTime,   "Not a valid APT contentTime.",   Transformer.intAsString),
                "wallClockTime" : encodeOneOf(self.actual.wallClockTime, "Not a valid APT wallClockTime.", Transformer.intAsString)
            }
        struct["earliest"] = {
            "contentTime"   : encodeOneOf(self.earliest.contentTime,   "Not a valid EPT contentTime.",   Transformer.intAsString),
            "wallClockTime" : encodeOneOf(self.earliest.wallClockTime, "Not a valid EPT wallClockTime.", Transformer.intAsString, Transformer.minusInf)
        }
        struct["latest"] = {
            "contentTime"   : encodeOneOf(self.latest.contentTime,   "Not a valid LPT contentTime.",   Transformer.intAsString),
            "wallClockTime" : encodeOneOf(self.latest.wallClockTime, "Not a valid LPT wallClockTime.", Transformer.intAsString, Transformer.plusInf)
        }
        return json.dumps(struct)

    @classmethod
    def unpack(cls,msg):
        """\
        Convert JSON string representation of this message encoded as a :class:`AptEptLpt` object.
        
        :throws ValueError: if not possible.
        """
        struct=json.loads(msg)
        opt={}
        try:
            if "actual" in struct:
                opt["actual"] = Timestamp(
                    contentTime   = decodeOneOf(struct["actual"]["contentTime"],   "Not a valid APT contentTime.",   Transformer.intAsString),
                    wallClockTime = decodeOneOf(struct["actual"]["wallClockTime"], "Not a valid APT wallClockTime.", Transformer.intAsString)
                )
            earliest = Timestamp(
                contentTime   = decodeOneOf(struct["earliest"]["contentTime"],   "Not a valid EPT contentTime.",   Transformer.intAsString),
                wallClockTime = decodeOneOf(struct["earliest"]["wallClockTime"], "Not a valid EPT wallClockTime.", Transformer.intAsString, Transformer.minusInf)
            )
            latest = Timestamp(
                contentTime   = decodeOneOf(struct["latest"]["contentTime"],   "Not a valid LPT contentTime.",   Transformer.intAsString),
                wallClockTime = decodeOneOf(struct["latest"]["wallClockTime"], "Not a valid LPT wallClockTime.", Transformer.intAsString, Transformer.plusInf)
            )
            return AptEptLpt(earliest=earliest, latest=latest, **opt)
        except KeyError:
            raise ValueError("Not all fields in SetupData message present as expected")
    
    def __str__(self):
        return self.__repr__()
    
    def __repr__(self):
        return 'AptEptLpt(actual=%s, earliest=%s, latest=%s' % (repr(self.actual), repr(self.earliest), repr(self.latest))

    def copy(self):
        """:returns: a deep copy of this AptEptLpt object"""
        actual = self.actual
        earliest = self.earliest
        latest = self.latest
        if actual != OMIT:
            actual = actual.copy()
        if earliest != OMIT:
            earliest = earliest.copy()
        if latest != OMIT:
            latest = latest.copy()
        return AptEptLpt(actual, earliest, latest)


__all__ = [
    "SetupData",
    "Timestamp",
    "ControlTimestamp",
    "AptEptLpt",
]
