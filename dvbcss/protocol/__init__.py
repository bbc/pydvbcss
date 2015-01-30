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

class _Entity(object):
    """\
    """
    def __init__(self, name, description = None, **kwargs):
        super(_Entity,self).__init__(**kwargs)
        if description == None:
            description = name
        self.__doc__ = description
        self.name=name
    def __str__(self):
        return self.name
    def __repr__(self):
        return self.name

OMIT=_Entity("OMIT", """\
When this object is assigned to an attribute of a protocol message object this
indicates that the corresponding property is not included in the JSON
representation of that message (it is omitted).

Here is an example. By default nearly all properties of a freshly created CII
message object are 'OMIT':

.. code-block:: python

    >>> from dvbcss.protocol.cii import CII
    >>> from dvbcss.protocol import OMIT

    >>> c=CII()
    >>> print repr(c.contentId)
    OMIT

    >>> c.wcUrl = "udp://192.168.1.1:6677"
    >>> print repr(c.wcUrl)
    'udp://192.168.1.1:6677'

    >>> c.wcUrl = OMIT
    >>> print repr(c.wcUrl)
    OMIT
""")





__all__ = [
    "OMIT",
]
