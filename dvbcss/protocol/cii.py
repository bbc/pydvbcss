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
A :class:`CII` object represents a CII message sent from server to client via the CSS-CII protocol.

A :class:`TimelineOption` object describes a timeline selector
and the tick rate of the timeline if that selector is used to request a
timeline from the CSS-TS server. It is carried in a list in the
:data:`~CII.timelines` property of a :class:`CII` message.

Examples
--------

:class:`CII` messages:

.. code-block:: python

    >>> from dvbcss.protocol.cii import CII
    >>> from dvbcss.protocol import OMIT
    
    >>> jsonCiiMessage = \"""\
    ...     { "protocolVersion":"1.1",
    ...       "contentId":"dvb://1234.5678.01ab",
    ...       "contentIdStatus":"partial"
    ...     }
    ... \"""
    
    >>> cii = CII.unpack(jsonCiiMessage)
    >>> cii.contentId
    'dvb://1234.5678.01ab'
   
    >>> print cii.mrsUrl
    OMIT

    >>> cii.protocolVersion = OMIT
    >>> cii.pack()
    '{contentId":"dvb://1234.5678.01ab","contentIdStatus":"partial"}'


:class:`TimelineOption` within CII messages:

.. code-block:: python

    >>> from dvbcss.protocol.cii import CII, TimelineOption
    
    >>> t1 = TimelineOption(timelineSelector="urn:dvb:css:timeline:pts", unitsPerTick=1, unitsPerSecond=90000)
    >>> t2 = TimelineOption(timelineSelector="urn:dvb:css:timeline:temi:1:1", unitsPerTick=1, unitsPerSecond=1000)

    >>> print t1.timelineSelector, t1.unitsPerTick, t1.unitsPerSecond, t1.accuracy
    urn:dvb:css:timeline:pts 1 90000 OMIT

.. code-block:: python

    >>> cii = CII(presentationStatus="final", timelines=[t1, t2])
    >>> cii.pack()
    '{ "presentationStatus": "final",
       "timelines": [ { "timelineProperties": {"unitsPerSecond": 90000, "unitsPerTick": 1},
                        "timelineSelector": "urn:dvb:css:timeline:pts"
                      },
                      { "timelineProperties": {"unitsPerSecond": 1000, "unitsPerTick": 1},
                        "timelineSelector": "urn:dvb:css:timeline:temi:1:1"
                      }
                    ]
     }'
"""

import json
import re
import copy
import logging    

from dvbcss.protocol.transformers import encodeOneOf, decodeOneOf
from dvbcss.protocol.transformers import Transformer
from dvbcss.protocol import OMIT

class CIITransformer(object):
    class presentationStatus(object):
        """\
        Transformer object for CII message presentationStatus with methods:
        
        encode(value) : [ "primaryAspect", "secondary1", "secondary2" ... ] -> "primaryAspect secondary1 secondary2 ..."
        decode(value) : "primaryAspect secondary1 secondary2 ..." -> "primaryAspect secondary1 secondary2"
        
        Raises ValueError if input value is not expected form.
        """
        @classmethod
        def decode(cls,value):
            if re.match("^(okay|transitioning|fault|[^ ]+)( [^ ]+)*$", value):
                return list(value.split(" "))
            else:
                raise ValueError("Format of presentationStatus not recognised: "+str(value))
        @classmethod
        def encode(cls,value):
            if isinstance(value,str):
                raise ValueError("presentationStatus should have been a list of strings, not a single string.")
            try:
                return " ".join(value)
            except:
                raise ValueError("presentationStatus should have been a list of strings")

    contentIdStatus = Transformer.matchOneOf("partial","final")


class TimelineOption(object):
    def __init__(self, timelineSelector, unitsPerTick, unitsPerSecond, accuracy=OMIT, private=OMIT):
        """\
        Object representing a CSS-CII Timeline Option used in the "timelines" property of a CII message.
        
        **Initialisation takes the following parameters:**
        
        :param str timelineSelector: The timeline selector
        :param int unitsPerTick: Denominator of tick rate (in ticks per second) for the corresponding timeline
        :param int unitsPerSecond: Numerator of tick rate (in ticks per second) for the corresponding timeline
        :param accuracy: Optional indication of timeline accuracy
        :type accuracy: :obj:`~dvbcss.protocol.OMIT` or :class:`float`
        :param private: Optional private data.
        :type private: :obj:`~dvbcss.protocol.OMIT` or :ref:`private-data`
        
        It represents a timeline selector and the tick rate of the timeline
        if that selector is used to request a timeline from the CSS-TS server.
        It is carried in a :class:`list` in the :data:`~CII.timelines` property of a :class:`CII` message.

        The tick rate of the timeline is expressed by the `unitsPerTick` and `unitsPerSecond` values.
        The tick rate in ticks per second is equal to `unitsPerTick` / `unitsPerSecond`.
          
        Accuracy and private data are optional, but the other fields are mandatory.

        The attributes of the object have the same name as the relevant CII message properties:
        
        * :data:`timelineSelector`
        * :data:`unitsPerTick`
        * :data:`unitsPerSecond`
        * :data:`accuracy`
        * :data:`private`
            
        Converting to and from JSON representation is performed using the :func:`pack` method and :func:`unpack` class method.
        Properties set to equal :data:`~dvbcss.protocol.OMIT` will be omitted when the message
        is packed to a JSON representation.

        """
        super(TimelineOption,self).__init__()
        
        self.timelineSelector = timelineSelector #: (:class:`str`) The timeline selector
        self.unitsPerTick     = unitsPerTick     #: (:class:`int`) The units per tick of the timeline
        self.unitsPerSecond   = unitsPerSecond   #: (:class:`int`) The units per second of the timeline
        self.accuracy         = accuracy         #: (:data:`~dvbcss.protocol.OMIT` or :class:`float`) The accuracy of the timeline with respect to the content in seconds.
        self.private          = private          #: (read/write :obj:`~dvbcss.protocol.OMIT` or :ref:`private-data`) Optional private data.
        
        """\
        (:data:`~dvbcss.protocol.OMIT` or :class:`list` of :class:`dict` )
        Private data as a :class:`list` of :class:`dict` objects that can be converted to JSON by :func:`json.dumps`.
        Each dict must contain at least a key called "type" with a URI string as its value.
        """
        
        self.log = logging.getLogger("dvbcss.protocol.cii.TimelineOption")
        
    @classmethod
    def encode(cls,item):
        """Internal class method used by a :class:`CII` message object when packing to JSON format."""
        return item._encode()
    
    def _encode(self):
        """Internal  method used by a :class:`CII` message object when packing to JSON format."""
        struct = {}
        struct["timelineSelector"] = self.timelineSelector
        substruct={}
        substruct["unitsPerTick"]= int(self.unitsPerTick)
        substruct["unitsPerSecond"]= int(self.unitsPerSecond)
        if self.accuracy != OMIT:
            substruct["accuracy"]= float(self.accuracy)
        if self.private != OMIT:
            struct["private"] = encodeOneOf(self.private,"Not a valid private property.", Transformer.private)
        struct["timelineProperties"]  = substruct
        return struct
            
    def pack(self):
        """:returns: string containing JSON presentation of this message."""
        return json.dumps(self.encode())

    @classmethod
    def unpack(cls, msg):
        """\
        Convert JSON string representation of this message encoded as a :class:`TimelineOption` object.
        
        :throws ValueError: if not possible.
        """
        struct = json.loads(msg)
        return cls.decode(struct)
    
    @classmethod
    def decode(cls, struct):
        """Internal method used by a :class:`CII` message object when unpacking to JSON format."""
        opt={}
        if "private" in struct:
            opt["private"] = decodeOneOf(struct["private"],"Not a valid private property.", Transformer.private)
        substruct = struct["timelineProperties"]
        if "accuracy" in substruct:
            opt["accuracy"] = decodeOneOf(substruct["accuracy"], "Not a valid accuracy property.", Transformer.float)
        try:
            return TimelineOption(
                  timelineSelector = struct["timelineSelector"],
                  unitsPerTick=substruct["unitsPerTick"],
                  unitsPerSecond=substruct["unitsPerSecond"],
                  **opt)
        except KeyError:
            raise ValueError("Not all fields in TimelineOption present as expected")
        
    def __str__(self):
        return self.__repr__()
    
    def __repr__(self):
        return 'TimelineOption(timelineSelector="%s", unitsPertick=%d, unitsPerSecond=%d, accuracy=%s private=%s)' %\
            (self.timelineSelector, self.unitsPerTick, self.unitsPerSecond, self.accuracy, repr(self.private))

    def __eq__(self, other):
        """Equality test, returns true if all properties are equal"""
        return self.timelineSelector == other.timelineSelector and \
               self.unitsPerTick == other.unitsPerTick and \
               self.unitsPerSecond == other.unitsPerSecond and \
               self.accuracy == other.accuracy and \
               self.private == other.private

    def __deepcopy__(self,memo):
        properties={}
        for name in ["timelineSelector", "unitsPerTick","unitsPerSecond","accuracy","private"]:
            original = getattr(self,name) 
            if original != OMIT:
                properties[name] = copy.deepcopy(original,memo)
        return TimelineOption(**properties)
                

class CII(object):
    
    # map of property names to the list of transformer objects used to encode or decode
    # the various forms each argument can take.
    _propertyTransform = {
        "protocolVersion"    : [Transformer.null, Transformer.matchOneOf("1.1")],
        "mrsUrl"             : [Transformer.null, Transformer.uriString],
        "contentId"          : [Transformer.null, Transformer.uriString],
        "contentIdStatus"    : [Transformer.null, CIITransformer.contentIdStatus],
        "presentationStatus" : [Transformer.null, CIITransformer.presentationStatus],
        "wcUrl"              : [Transformer.null, Transformer.uriString],
        "tsUrl"              : [Transformer.null, Transformer.uriString],
        "teUrl"              : [Transformer.null, Transformer.uriString],
        "timelines"          : [Transformer.null, Transformer.listOf(TimelineOption)],
         "private"           : [Transformer.null, Transformer.private],
    }
    
    def __init__(self,**kwargs):
        """\
        Object representing a CII message used in the CSS-CII protocol.
        
        **Initialisation takes the following parameters, all of which are optional
        keyword arguments that default to** :obj:`~dvbcss.protocol.OMIT` :
        
        :param protocolVersion: The protocol version being used by the server.
        :param mrsUrl: The URL of an MRS server known to the server.
        :param contentId: Content identifier URI.
        :param contentIdStatus: Content identifier status.
        :param presentationStatus: Presentation status as a :class:`list` of one or more strings, e.g. ``[ "okay" ]``
        :param wcUrl: CSS-WC server endpoint URL in the form "udp://<host>:<port>"
        :param tsUrl: CSS-TS server endpoint WebSocket URL
        :param teUrl: CSS-TE server endpoint WebSocket URL
        :param timelines: List of timeline options.
        :param private: Private data.
        
        :type protocolVersion: :data:`~dvbcss.protocol.OMIT` or "1.1"
        :type mrsUrl: :data:`~dvbcss.protocol.OMIT` or :class:`str`
        :type contentId: :data:`~dvbcss.protocol.OMIT` or :class:`str`
        :type contentIdStatus: :data:`~dvbcss.protocol.OMIT` or "partial" or "final"
        :type presentationStatus: :data:`~dvbcss.protocol.OMIT` or :class:`list` of :class:`str`
        :type wcUrl: :data:`~dvbcss.protocol.OMIT` or :class:`str`
        :type tsUrl: :data:`~dvbcss.protocol.OMIT` or :class:`str`
        :type teUrl: :data:`~dvbcss.protocol.OMIT` or :class:`str`
        :type timelines: :data:`~dvbcss.protocol.OMIT` or :class:`list` of :class:`TimelineOption`
        :type private: :data:`~dvbcss.protocol.OMIT` or :ref:`private-data`
        
        The attributes of the object have the same name as the CII message properties:
        
        * :data:`protocolVersion`
        * :data:`mrsUrl`
        * :data:`contentId`
        * :data:`contentIdStatus`
        * :data:`presentationStatus`
        * :data:`wcUrl`
        * :data:`tsUrl`
        * :data:`teUrl`
        * :data:`timelines`
        * :data:`private`
            
        Properties are accessed as attributes of this object using the same name as their JSON property name.
        
        Converting to and from JSON representation is performed using the :func:`pack` method and :func:`unpack` class method.
        Properties set to equal :data:`~dvbcss.protocol.OMIT` will be omitted when the message
        is packed to a JSON representation.

        """
        super(CII,self).__init__()
        self.log = logging.getLogger("dvbcss.protocol.cii.CII")
        
        self.protocolVersion    = OMIT #: (read/write :data:`~dvbcss.protocol.OMIT` or "1.1") The protocol version being used by the server.
        self.mrsUrl             = OMIT #: (read/write :data:`~dvbcss.protocol.OMIT` or :class:`str`) The URL of an MRS server known to the server
        self.contentId          = OMIT #: (read/write :data:`~dvbcss.protocol.OMIT` or :class:`str`) Content identifier (URL)
        self.contentIdStatus    = OMIT #: (read/write :data:`~dvbcss.protocol.OMIT` or "partial" or "final") Content identifier status
        self.presentationStatus = OMIT #: (read/write :data:`~dvbcss.protocol.OMIT` or :class:`list` of :class:`str`) Presentation status, e.g. ``[ "okay" ]``
        self.wcUrl              = OMIT #: (read/write :data:`~dvbcss.protocol.OMIT` or :class:`str`) CSS-WC server endpoint URL in form "udp://<host>:<port>"
        self.tsUrl              = OMIT #: (read/write :data:`~dvbcss.protocol.OMIT` or :class:`str`) CSS-TS server endpoint WebSocket URL
        self.teUrl              = OMIT #: (read/write :data:`~dvbcss.protocol.OMIT` or :class:`str`) CSS-TE server endpoint WebSocket URL
        self.timelines          = OMIT #: (read/write :data:`~dvbcss.protocol.OMIT` or :class:`list`(:class:`TimelineOption`)) Timeline options
        self.private            = OMIT #: (read/write :obj:`~dvbcss.protocol.OMIT` or :ref:`private-data`) Optional private data.
        """\
        (:data:`~dvbcss.protocol.OMIT` or :class:`list` of :class:`dict` )
        Private data as a :class:`list` of :class:`dict` objects that can be converted
        to JSON by :func:`json.dumps`.
        Each dict must contain at least a key called "type" with a URI string as its value.
        """
        
        for key in kwargs:
            if key in self._propertyTransform:
                setattr(self, key, kwargs[key])
            else:
                raise ValueError("Unrecognised property name provided as parameter: "+key)
    

        
    def pack(self):
        """\
        :returns: string containing JSON representation of this message.
        :throws ValueError: if there are values for properties that are not permitted.
        """
        struct = {}
        for name in self._propertyTransform:
            value=getattr(self, name)
            if value != OMIT:
                transformers=self._propertyTransform[name]
                struct[name]= encodeOneOf(value, "Value of "+name+" property not valid.", *transformers)
        return json.dumps(struct)
    
    @classmethod
    def unpack(cls, msg):
        """\
        Convert JSON string representation of this message encoded as a :class:`CII` object.
        
        :throws ValueError: if not possible.
        """
        struct = json.loads(msg)
        kwargs={}
        for name in cls._propertyTransform:
            if name in struct:
                value=struct[name]
                transformers=cls._propertyTransform[name]
                kwargs[name] = decodeOneOf(value, "Value of "+name+" property not valid.", *transformers)
        return CII(**kwargs)
        
    def __str__(self):
        return self.__repr__()
    
    def __repr__(self):
        return "CII(" + ", ".join(
              [ key+"="+repr(getattr(self, key))
                for key in
                    filter(lambda k:getattr(self,k) != OMIT,
                           self._propertyTransform.keys()
                          )
               ]
            )+")"
    
    def copy(self):
        """:returns: a copy of this CII object. The copy is a deep copy."""
        properties={}
        for name in self.definedProperties():
            original=getattr(self,name)
            if original != OMIT:
                properties[name] = copy.deepcopy(original)
        return CII(**properties)
    
    @classmethod
    def diff(cls, old, new):
        """\
        :param old: (:class:`~dvbcss.protocol.cii.CII`) A CII object
        :param new: (:class:`~dvbcss.protocol.cii.CII`) A CII object
        :Returns: CII object representing changes from old to new CII objects.
        
        If in the new CII object a property is OMITted, it property won't appear in the returned CII object that represents the changes.
        
        If in the old CII object a property is OMITted, but it has a non-omitted value in the new object, then it is assumed
        to be a change.
        """
        changes=CII()
        for name in cls._propertyTransform:
            if getattr(old,name) != getattr(new,name) and getattr(new,name) != OMIT:
                setattr(changes, name, getattr(new, name))
        return changes
    
    def definedProperties(self):
        """Returns a list of the names of properties whose value is not OMIT"""
        return [name for name in self._propertyTransform if getattr(self,name) != OMIT]

    @classmethod
    def allProperties(cls):
        """Returns a list of all property names, whether OMITted or not"""
        return [name for name in cls._propertyTransform]

    def update(self, diff):
        """\
        Updates this CII object with the values of any properties (that are not omitted) in the CII object provided as the `diff` argument.
        
        Note that this changes this object.

        :param diff: (:class:`~dvbcss.protocol.cii.CII`) A CII object whose properties (that are not omitted) will be used to update this CII object.
        """
        for name in self._propertyTransform:
            value = getattr(diff,name)
            if value != OMIT:
                setattr(self,name,value)
        
    def combine(self, diff):
        """\
        Copies this CII object, and updates that copy with any properties (that are not omitted) in the CII object supplied as the `diff` argument.
        The updated copy is then returned.
        
        :param diff: (:class:`~dvbcss.protocol.cii.CII`) A CII object whose properties (that are not omitted) will be used to update the copy before it is returned.
        
        new = old.combine(diff) is equivalent to the following operations:

        .. code-block:: python
        
            new = old.copy()
            new.update(diff)
        """
        new=self.copy()
        new.update(diff)
        return new





__all__ = [
    "CII",
    "TimelineOption",
]
