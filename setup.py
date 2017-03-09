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

from setuptools import setup
import os
import sys
import re


def find_packages(path, base="" ):
    """ Find all packages in path """
    packages = {}
    if "__init__.py" in os.listdir(path):
        packages[base] = path
        
    for item in os.listdir(path):
        itempath = os.path.join(path,item)
        if os.path.isdir(itempath):
            newbase = "%s.%s" % (base, item)
            packages.update(find_packages(itempath, newbase))

    return packages

packages = find_packages("dvbcss","dvbcss")
package_names = packages.keys()

otherArgs = {}

# if registering or uploading to PyPI: convert markdown readme to ReStructuredText
# using pandoc

lcase_args = [arg.lower() for arg in sys.argv]
if "register" in lcase_args or "upload" in lcase_args:
    retval = os.system("pandoc --from=markdown --to=rst --output=tmp.README.rst README.md")
    if retval==0:
        otherArgs["long_description"] = open("tmp.README.rst").read()
    else:
        raise RuntimeError("Unable to convert documentation from Markdown to ReStructuredText. Is 'pandoc' command line tool installed?")
    
try:
    VERSION, _ = re.match("^([.0-9a-zA-Z]+)-(.+)$", open("VERSION").read().replace("\n","").replace("\r","")).groups()

    setup(
        name = "pydvbcss",
        version = VERSION,
        author = "Matt Hammond (British Broadcasting Corporation)",
        author_email = "matt.hammond@bbc.co.uk",
        description = ("pydvbcss is a library implementing DVB \"CSS\" protocols for Companion Screen Synchronisation."),
        license = "Apache 2.0",
        keywords = "dvb companion synchronisation synchronization second-screen protocol",
        url = "http://github.com/BBC/pydvbcss",
        
        packages = package_names,
        package_dir = packages,
        install_requires = [ 'cherrypy<9.0.0', 'ws4py<=0.3.5' ],

        test_suite = "test.test_all.testSuite",
        
        classifiers=[
            "Intended Audience :: Developers",
            "Intended Audience :: Telecommunications Industry",
            "License :: OSI Approved :: Apache Software License",
            "Natural Language :: English",
            "Operating System :: MacOS :: MacOS X",
            "Operating System :: Microsoft :: Windows",
            "Operating System :: POSIX :: Linux",
            "Programming Language :: Python :: 2.7",
            "Topic :: Internet",
            "Topic :: Software Development :: Libraries :: Python Modules",
            "Topic :: System :: Networking :: Time Synchronization",
        ],
        
        **otherArgs
    )

finally:
    if "long_description" in otherArgs:
        os.remove("tmp.README.rst")
