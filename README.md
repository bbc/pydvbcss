# Python DVB Companion Screen Synchronisation protocol library and tools

[![Build status](https://travis-ci.org/bbc/pydvbcss.svg?branch=0.5.2)](https://travis-ci.org/bbc/pydvbcss)
[![Docs Status
(0.5.2)](https://readthedocs.org/projects/pydvbcss/badge/?version=0.5.2)](http://pydvbcss.readthedocs.io/en/0.5.2/?badge=0.5.2)
[![Docs Status (latest)](https://readthedocs.org/projects/pydvbcss/badge/?version=latest)](http://pydvbcss.readthedocs.io/en/latest/?badge=latest)
[![Latest PyPI package](https://img.shields.io/pypi/v/pydvbcss.svg)](https://pypi.python.org/pypi/pydvbcss)

* **[How to install](#install-the-code)**
* **[Read the documentation](#read-the-documentation)**
* **[Run the examples](#run-the-examples)**

**pydvbcss** is a set of Python 2.7 libraries and command-line tools that implement some of the
protocols defined in the DVB CSS specification (published as [ETSI 103-286 part 2](http://www.etsi.org/standards-search?search=103+286&page=1&title=1&keywords=1&ed=1&sortby=1))
and are used for the "inter-device synchronisation" feature in **[HbbTV 2](http://hbbtv.org/resource-library/)**.
These protocols enable synchronisation of media presentation between a TV
and Companion devices (mobiles, tablets, etc).

This library includes simple to use high level abstractions that wrap up the
server or client behaviour for each protocol as well as low level code for
packing and unpacking messages sent across the protocols. There are also
objects that work with the rest of the library to represent clocks and timelines.

This code is intended as an informal reference and is suitable for building
prototypes and testing tools that implement TV (server) or Companion
(client) behaviour. It is not considered production ready or suitable for
integration into consumer products.

The code does not implement media playback functionality and this is not a planned
feature.

The DVB CSS specification was formerly published as [DVB Bluebook A167-2](https://www.dvb.org/search/results/keywords/A167). This is deprecated in favour of the [ETSI spec](http://www.etsi.org/standards-search?search=103+286&page=1&title=1&keywords=1&ed=1&sortby=1).

## Getting started

**pydvbcss** requires [ws4py](https://ws4py.readthedocs.io/en/latest/) for
use in clients and servers, and also [cherrypy](http://www.cherrypy.org)
for server implementations.  The steps below describe how to install these.

**pydvbcss** has been developed on Mac OS X 10.10 but has also been used
successfully on Microsoft Windows 7 and Ubuntu 14.04.



### Read the Documentation

The docs for the library can be read online on readthedocs.org:

   * [![Docs Status (0.5.2)](https://readthedocs.org/projects/pydvbcss/badge/?version=0.5.2)](http://pydvbcss.readthedocs.io/en/0.5.2/?badge=0.5.2) [Docs for 0.5.2 release](http://pydvbcss.readthedocs.io/en/0.5.2/?badge=0.5.2)
   
   * [![Docs Status (latest)](https://readthedocs.org/projects/pydvbcss/badge/?version=latest)](http://pydvbcss.readthedocs.io/en/latest/?badge=latest) [Docs for latest commits to master release](http://pydvbcss.readthedocs.io/en/latest/?badge=latest)

Links are also available from those pages through to documentation for earlier releases.



### Install the code ...

*On Mac OS X and Linux you may need to run one or more of the commands as root.*

#### Using PyPi _(core library only, no examples or tools)_

   * [![Latest PyPI package](https://img.shields.io/pypi/v/pydvbcss.svg)](https://pypi.python.org/pypi/pydvbcss) [See the pydvbcss PyPI package page](https://pypi.python.org/pypi/pydvbcss). 

If you ONLY want the library (not the [code examples and tools](#run-examples) ) and
if you don't require the very latest bugfixes, then you can install a recent
release package from the Python Package Index (PyPI) using
[pip](https://pip.pypa.io/en/latest/installing.html):

    $ pip install pydvbcss

Or if upgrading from a previous version:

    $ pip install --upgrade pydvbcss

You can use `pip search pydvbcss` to verify which version is installed.

> *See note in the next section about `CherryPy` and `ws4py` dependencies.*


#### From Github or a release tarball _(includes examples and tools)_

The [master branch](https://github.com/BBC/pydvbcss/tree/master) is the latest
state of the code, including any recent bugfixes. It is mostly stable but
might have occasional small API changes.
[Release snapshots](https://github.com/BBC/pydvbcss/releases) are also available
but won't contain the very latest bugfixes or new features.
Both of these options include the full code, including [examples](#run-examples).

First you need to install dependencies...

We recommend using [pip](https://pip.pypa.io/en/latest/installing.html) to install
dependencies from the Python Package Index [PyPI](https://pypi.python.org/pypi):

    $ pip install -r requirements.txt

> *NOTE: There have been recent incompatibilities between certain versions of
> `cherrypy`, `ws4py` and `cheroot`. Therefore, `requirements.txt` requires specific
> (older) versions of these pacakges. You are welcome to try newer versions installing
> them manually. See [#15](https://github.com/bbc/pydvbcss/issues/15) for background
> details.*

Then take (or update) your clone of the repository *master* branch, or
download and unzip a snapshot release and run the `setup.py` script to
install:

    $ python setup.py install
    
This will install all module packages under 'dvbcss'.

There is a limited test suite (it only tests certain classes at the moment).
Run it via setup.py:

    $ python setup.py test

This checks some timing sensitive implementation issues, so ensure you are not
running any CPU intensive tasks at the time.



## Running the examples and tools

There is a set of example and tools demonstrating simple servers and clients for the
protocols included with the library. See the 
[quick start guide](https://BBC.github.io/pydvbcss/docs/latest/examples.html) 
in the documentation to see how to run them.

The clients are useful tools to test a TV implementation is outputting the correect data.

The servers can be modified to simulate a TV that is playing content with an ID
and timeline(s) that a companion application expects.

### Example: checking protocols implemented by a TV

Start the content playing on the TV and ensure it is serving the protocols (for HbbTV 2
TVs this requires an HbbTV application to enable inter-device synchronisation).

Suppose the TV is serving the CII protocol at the URL `ws://192.168.0.57:7681/cii`...

To check the CII protocol:

    $ python examples/CIIClient.py ws://192.168.0.57:7681/cii

Suppose that the messages returned report the URL of the TS protocol endpoint as being `ws://192.168.0.57:7681/ts` and the wall clock protocol as being at `192.168.0.57` port `6677`...

To check the TV's Wall Clock protocol:`

    $ python examples/WallClockClient.py 192.168.0.57 6677

To check the TV reporting a PTS timeline (uses both Wall Clock and TS protocols):

    $ python examples/TSClient.py ws://192.168.0.57:7681/ts \
        udp://192.168.0.57:6677 \
        "" \
        "urn:dvb:css:timeline:pts" \
        9000


## Super-quick introduction to the protocols

DVB has defined 3 protocols for communicating between a companion and TV in
order to create synchronised second screen / dual screen / companion
experiences (choose whatever term you prefer!) that are implemented here:

* CSS-CII - A WebSockets+JSON protocol that conveys state from the TV, such
  as the ID of the content being shown at the time. It also carries the URLs
  to connect to the other two protocols.

* CSS-WC - A simple UDP protocol (like NTP but simplified) that establishes
  a common shared clock (a "wall clock") between the TV and companion,
  compensating for network delays.

* CSS-TS - Another WebSockets+JSON protocol that communicates timestamps
  from TV to Companion that describe the current timeline position.

The TV implements servers for all 3 protocols. The Companion implements
clients.

There are other protocols defined in the specification (CSS-TE and CSS-MRS) that
are not currently implemented by this library.


## Building the documentation for yourself

You can also build the documentation yourself. It is written using the
[sphinx](http://www.sphinx-doc.org) documentation build system.

Building the documentation requires [sphinx](http://www.sphinx-doc.org) and
the sphinx "read the docs" theme. The easiest way is using PyPI:

    $ pip install sphinx
    $ pip install sphinx_rtd_theme

The `docs` directory contains the configuration and main documentation
sources that descibe the structure. Most of the actual words are in the
inline docstrings in the source code. These structural pages pull these in.

To build docs in HTML format, either:

    $ python setup.py build_sphinx

or:

    $ cd docs
    $ make html
    


## Contact and discuss

Discuss and ask questions on the [pydvbcss google group](<https://groups.google.com/forum/#!forum/pydvbcss>).

The original author is Matt Hammond 'at' bbc.co.uk



## Licence

All code and documentation is licensed under the Apache License v2.0.



## Contributing

If you would like to contribute to this project, see
[CONTRIBUTING](CONTRIBUTING.md) for details.

