# Change Log

## Latest

* Bugfix to constructor for CIIServer to ensure default value for `initialCII` is not corrupted if a 2nd CII server is instantiated, plus added copy() methods to all objects representing JSON messages.

## 0.3.1 : Packaging version fix (01 Sep 2015)

* Completed support for uploading packages to pypi to enable installation using `pip`
* Bugfix: setup.py was not tracking same version number as in `VERSION` file.

## 0.3 : Bugfixes and CSS-TS Server API enhancements (01 Sep 2015)

* API change: Modified API for TimelineSource for TS Servers to allow for situations where it takes time to begin extracting a timeline at the server.
* Docs: Switched to referring to spec as ETSI 103 286 now it is published by ETSI
* Docs: Updated to reflect API changes
* Docs: General minor fixes
* Bugfix: CIIServer disconnect callback failed due to wrong number of arguments
* Bugfix: Incorrect use of `"presentationStatus"` CII property in examples. Should have been a list, not a string. Also added a check to trap this.
* Bugfix: Some command line arguments being ignored in `examples/TVDevice.py`
* Bugfix: Wallclock time printed in wrong units in `examples/WallClockClient.py`

## 0.2 : Client dispersion reporting release (17 Mar 2015)

* API change: Added ways to extract dispersion and worst-dispersion information more usefully from wall clock clients.
* Tests: Minor unit test improvements

## 0.1.1 : Bugfix release (18 Feb 2015)

* Bugfix: Fixed problem in `setup.py` that meant when pydvbcss is installed it could not be imported into another python program
* Bugfix: Fixed incorrect content ID URLs used in CII Server example
* Docs: Various documentation improvements
* Tests: New unit tests

## 0.1 : initial release
