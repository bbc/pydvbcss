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

    def processDoc(docString):
        objPathName = parentClass.__module__ + "." + parentClass.__name__
        inheritInfo = "\n\n(Documentation inherited from :%s:`~%s`)\n" % (objType, objPathName)
        docString = docString.replace("|stub-method|","")
        docString = docString + inheritInfo
        return docString


    def decorator(childClass):
    
        for attrName in dir(parentClass):
            parentProp = getattr(parentClass, attrName)
            childProp  = getattr(childClass,  attrName)

            # depending on the kind of attribute, the __doc__ string comes from different places        
            if type(parentProp) == types.MethodType and childProp.__doc__ is None:
                try:
                    childProp.im_func.__doc__ = processDoc(parentProp.im_func.__doc__)
                except:
                    pass
        
            elif type(parentProp) == property and childProp.__doc__ is None:
                docStr = processDoc(parentProp.__doc__)
                newProperty = property(fget=childProp.fget, fset=childProp.fset, fdel=childProp.fdel, doc=docStr)
                setattr(childClass, attrName, newProperty)
        
            else:
                pass

        return childClass              

    return decorator
