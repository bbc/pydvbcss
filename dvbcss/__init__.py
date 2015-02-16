#!/usr/bin env python

# --------------------------------------------------------------------------
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
# --------------------------------------------------------------------------

import types

def _inheritDocs(parentClass, objType="class"):
    """\
    Decorator that copies documentation strings from attributes of a parent class to a child
    class where the methods have been defined but no doc string written.
    
    Works for methods that have been defined (instance method objects) and
    for getter/setter properties.
    
    Also suffix inheritance information.
    """

    def decorator(childClass):
    
        objPathName = parentClass.__module__ + "." + parentClass.__name__
        inheritInfo = "\n\n(documentation inherited from :%s:`~%s`)\n" % (objType, objPathName)
    
        for attrName in dir(parentClass):
            parent = getattr(parentClass, attrName)
            child  = getattr(childClass,  attrName)

            # depending on the kind of attribute, the __doc__ string comes from different places        
            if type(parent) == types.MethodType:
                copyDocsFromTo = [ (parent.im_func, child.im_func) ]
        
            elif type(parent) == property:
                copyDocsFromTo = [ (parent.fget, child.fget), (parent.fset, child.fset) ]
        
            else:
                copyDocsFromTo = []

            for parentWithDoc, childWithDoc in copyDocsFromTo:                    
                if parentWithDoc.__doc__ is not None and childWithDoc.__doc__ is None:
                    try:
                        childWithDoc.__doc__ = parentWithDoc.__doc__ + inheritInfo
                    except AttributeError:
                    
                        pass # raised if it is a method of the class itself, e.g. __repr__

        return childClass              

    return decorator