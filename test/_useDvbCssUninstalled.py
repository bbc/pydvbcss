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


# allow tests to run from the package directory, if dvbcss isn't yet installed
try:
    import dvbcss
except ImportError:
    import sys, os
    parentDir= os.path.dirname(os.path.abspath(__file__))+os.sep+".."
    sys.path.append(parentDir)

if __name__ == "__main__":
    import sys
    
    print >> sys.stderr, """
This is a support file and is designed to be imported, not run on its own.

This module amends the import path to include the parent directory,
thereby allowing the example code to run without installing dvbcss
modules first.

"""
