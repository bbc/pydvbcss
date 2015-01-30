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

"""\
Helper routines for protocol message format packing and unpacking code.

Transformer objects provided here convert betwen python data types convenient for use within code and
python types that will map directly to JSON types. Each transformer has an encode() and a decode()
method allowing conversion to be done either way.

encodeOneOf and decodeOneOf allow several Transformers to be composed to allow a value to be encoded
or decoded that matches any one of the transformers.

E.g.

Transformer.intAsString will convert integers to and from string representations - allowing large
integers (greater than 53 bits precision) to be represented in JSON as strings without loss of precision.

Transformer.plusInf and Transformer.minusInf will convert between plus or minus infinity (represented by
a python float value) and the strings "plusinfinity" and "minusinfinity"
"""

import re
from dvbcss.protocol import OMIT

_re_intAsString = re.compile('^(0|(-?[1-9])[0-9]*)$')

def encodeOneOf(value, errMsg, *transformers):
    """Attempt to encode value using one of the transformers supplied. They are tried in the order provided.
    If all fail, the raise a ValueError with the error message provided."""
    for t in transformers:
        try:
            return t.encode(value)
        except Exception, e:
            pass
    raise ValueError(errMsg+" Value: "+str(value)+"\nCause: "+str(e))


def decodeOneOf(value, errMsg, *transformers):
    """Attempt to decode value using one of the transformers supplied. They are tried in the order provided.
    If all fail, the raise a ValueError with the error message provided."""
    for t in transformers:
        try:
            return t.decode(value)
        except Exception:
            pass
    raise ValueError(errMsg+" Value: "+str(value))



class Transformer(object):
    """\
    Contains set of standard transformer objects that implement a decode(value) and encode(value) methods.
    
    The purpose of these transformers to to transform to and from a representation suitable for conversion
    to json:
    
                       --encode-->                   --json.dumps-->
        Python objects             Python primitives                 JSON        
                       <--decode--                   <--json.loads--
    """

    class intAsString(object):
        """\
        Transformer object with methods:
        
        encode(value) : 12345 -> "12345"
        decode(value) : "12345" -> 12345
        
        Raises ValueError if input value is not expected form.
        """
        @classmethod
        def decode(cls,value):
            match = _re_intAsString.match(value)
            if match:
                return int(match.group(1))
            else:
                raise ValueError("Format of time value not recognised: "+str(value))
        @classmethod
        def encode(cls,value):
            return str(int(value))
    
    class minusInf(object):
        """\
        Transformer object with methods:
        
        encode(value) : float("-inf") -> "minusinfinity"
        decode(value) : "minusinfinity" -> float("-inf")
        
        Raises ValueError if input value is not expected form.
        """
        @classmethod
        def decode(cls,value):
            if value == "minusinfinity":
                return float("-inf")
            else:
                raise ValueError("Value is not encoded as minus infinity")
        @classmethod
        def encode(cls,value):
            if value == float("-inf"):
                return "minusinfinity"
            else:
                raise ValueError("Isn't minus infinity")
        
    class plusInf(object):
        """\
        Transformer object with methods:
        
        encode(value) : float("+inf") -> "plusinfinity"
        decode(value) : "plusinfinity" -> float("+inf")
        
        Raises ValueError if input value is not expected form.
        """
        @classmethod
        def decode(cls,value):
            if value == "plusinfinity":
                return float("+inf")
            else:
                raise ValueError("Value is not encoded as plus infinity")
        @classmethod
        def encode(cls,value):
            if value == float("+inf"):
                return "plusinfinity"
            else:
                raise ValueError("Isn't plus infinity")
    
    class float(object):
        """\
        Transformer object with methods:
        
        encode(value) : 1234.5 -> 1234.5
        decode(value) : 1234.5 -> 1234.5
        
        Raises ValueError if input value is not expected form.
        """

        @classmethod
        def decode(cls,value):
            return float(value)
        @classmethod
        def encode(cls,value):
            return float(value)
    
    class null(object):
        """\
        Transformer object with methods:
        
        encode(value) : None -> None
        decode(value) : None -> None
        
        Raises ValueError if input value is not expected form.
        """
        @classmethod
        def decode(cls,value):
            if value is None:
                return value
            else:
                raise ValueError("Value is not null")
        @classmethod
        def encode(cls,value):
            if value is None:
                return value
            else:
                raise ValueError("Value is not None")

    class uriString(object):
        """\
        Transformer object with methods:
        
        encode(value) : uri-string -> uri-string
        decode(value) : uri-string -> uri-string
        
        Raises ValueError if input value is not expected form.
        """

        # Regular expression from RFC3986 appendix B
        _uriRegex = re.compile("^(([^:/?#]+):)?(//([^/?#]*))?([^?#]*)(\?([^#]*))?(#(.*))?")

        @classmethod
        def decode(cls,value):
            if cls._uriRegex.match(value):
                return value
            else:
                raise ValueError("Value is not a valid URI: "+str(value))
        
        encode=decode
        
    class omit(object):
        """\
        Transformer object with methods:
        
        encode(value) : OMIT -> OMIT
        decode(value) : OMIT -> OMIT
        
        Raises ValueError if input value is not expected form.
        """
        @classmethod
        def decode(cls,value):
            if value == OMIT:
                return value
            else:
                raise ValueError("Value is not OMIT")
        @classmethod
        def encode(cls,value):
            if value == OMIT:
                return value
            else:
                raise ValueError("Value is not OMIT")

    @classmethod
    def listOf(cls, transformer):
        class listOf(object):
            @classmethod
            def decode(cls,value):
                try:
                    return [transformer.decode(x) for x in value]
                except:
                    raise ValueError("Value is not a list of the correct type of items.")
            @classmethod
            def encode(cls,value):
                try:
                    return [transformer.encode(x) for x in value]
                except:
                    raise ValueError("Value is not a list of the correct type of items.")
        return listOf

    @classmethod
    def matchOneOf(cls,*items):
        class matchOneOf(object):
            @classmethod
            def decode(cls,value):
                if value in items:
                    return value
                else:
                    raise ValueError("Value is not one from the list "+repr(items))
            @classmethod
            def encode(cls,value):
                if value in items:
                    return value
                else:
                    raise ValueError("Value is not one from the list "+repr(items))
        return matchOneOf

    class private(object):
        """Transformer object with methods:
        
        encode(value) : [ private, private, ...] -> [ private, private, ...]
        decode(value) : [ private, private, ...] -> [ private, private, ...]
        
        where private = { "type" : uriString, <any-other-properties> }
        """
        @classmethod
        def decode(cls, value):
            try:
                for item in value:
                    Transformer.uriString.decode(item["type"])
                return value
            except (ValueError, KeyError), e:
                raise ValueError("Not a valid private structure:"+str(e))
        
        encode=decode
        
