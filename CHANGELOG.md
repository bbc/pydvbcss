# Change Log

## Latest

* Bugfix: fixed semantics on `calcWhen()`, `toParenTicks()` and `toRootTicks()`
  when clock speed is 0.` ([32256b6](https://github.com/bbc/pydvbcss/commit/32256b6f94ce01466ab4645097672e58a00456cc))
* ...

## 0.4.0 : Bugfixes and overhaul of clock object model (new-clock-model)

This release contains a significant internal upgrade to the `dvbcss.clock`
module with minor knock-on effects on other packages - particularly wall clock
client and server code and algorithms. The changes have been implemented to
be mostly backwardly compatible, so existing code should continue to work. The
only exception will be any custom wall clock client algorithms.

Clock objects can now calculate **dispersion** (error bounds). Clocks can also
track clock **availability** (mirroring the concept of timeline availability).

Wall clock client algorithms have been switched from measuring and adjusting
the same clock (representing the wall clock) to instead measuring its parent
and setting the correlation. Any custom wall clock client algorithms will
not work and will need to be updated.

#### How to 'upgrade' existing code

* Use a `CorrelatedClock` instead of a `TunableClock` to model a wall clock.
  and set the "maximum frequency error" when initialising the `SysClock`
  instead of passing it to a `WallClockClient` or `WallClockServer`.
  
* Use a `Correlation` object instead of a tuple (parentT,childT) to represent
  correlations for a `CorrelatedClock`
  
* Control and check timeline availability of clock objects instead of setting
  or querying the availability of the TS protocol server or client.
  
* Update any custom algorithms you might have created for wall clock clients.

  * `Candidate` objects now represent the relationship between the **parent**
    of the local wall clock (instead of the local wall clock itself)
    and the server's wall clock.`
  
  * Algorithms and Filters now receive a single `Candidate` object in units of
    nanoseconds. They no longer receive a `Candidate` converted to units of
    clock ticks.
  
  * Predictors should return a `Correlation` instead of an adjustment value.
  
* `DispersionCalculator` is being deprecated. It still exists, but you should
  stop using it and instead use `Candidate.calcCorrelationFor` function to 
  create a correlation which you then put into a `CorrelatedClock` and call
  the `dispersionAtTime` function.
  
Examples of old way (0.3.x and earlier):
  
    s = SysClock()
    wallClock = TunableClock(s, tickRate=1000000000)

    algorithm = LowestDispersionCandidate(wallClock,repeatSecs=1,timeoutSecs=0.5, localMaxFreqErrorPpm=500)
    wc_client=WallClockClient(bind, dest, wallClock, algorithm)
    wc_client.start()

    timeline = CorrelatedClock(wallClock, tickRate=1000, (10,20))

    timeline.correlation = ( timeline.correlation[0], timeline.correlation[1] + 50)

    ts = TSClientClockController(tsUrl, contentIdStem, timelineSelector, timeline)
    print ts.available

Equivalent new way (0.4 and later):
  
    s=SysClock(maxFreqErrorPpm=500)
    wallClock=CorrelatedClock(s,tickRate=1000000000)

    algorithm = LowestDispersionCandidate(wallClock,repeatSecs=1,timeoutSecs=0.5)
    wc_client=WallClockClient(bind, dest, wallClock, algorithm)
    wc_client.start()

    timeline = CorrelatedClock(wallClock, tickRate=1000, Correlation(10,20))

    timeline.correlation = timeline.correlation.butWith(childTicks=timeline.childTicks + 50)

    ts = TSClientClockController(tsUrl, contentIdStem, timelineSelector, timeline)
    print timeline.isAvailable()

#### Summary of changes:

Main changes in new clock model ([da846a9](https://github.com/bbc/pydvbcss/commit/da846a96ec8dd3e23b4a3e363fd98d1c495cc8c5)):
* API addition: can setParent() on `CorrelatedClock`, `RangeCorrelatedClock` and `TunableClock`.
* API change: All clock objects modified to be able to track error values and calculate dispersions and clock `availability`
* API change: `CorrelatedClock` class modified to use a `Correlation` object instead of a tuple.
* API change: `TunableClock` reimplemented as subclass of `CorrelatedClock`
* API change: `WallClockClient`, `WallClockServer` initialisation arguments - precision and maxfreqerror now optional. Now, by default, taken from the clock.
* API change: Wall clock client algorithms (dispersion, filtering, prediction) changed to update a CorrelatedClock and to measure the parent of the clock representing the wall clock. Review the documentation to understand how to update any algorithms you might have implemented.
* API change: `DispersionCalculator` class deprecated (but still available). Use `Candidate.calcCorrelationFor` and `CorrelatedClock.dispersionAtTime` instead.
* Tests: Updated to reflect changes.
* Docs: Updated to reflect changes.

Other improvements/bugfixes:
* Bugfix: Tracking of number of connections to CSS-CII and CSS-TS had a leak ([4c76042](https://github.com/bbc/pydvbcss/commit/4c76042d2e6c69f2c38682468738ba8cca02b5d1))
* API addition: `setParent()` on `CorrelatedClock` ([d4576d7](https://github.com/bbc/pydvbcss/commit/d4576d7440e8e9f5ced4e73fa182edc05442b1b8))
* Bugfix: NotImplemented exception used incorrectly ([d4576d7](https://github.com/bbc/pydvbcss/commit/d4576d7440e8e9f5ced4e73fa182edc05442b1b8))
* Bugfix: Workaround for OSX 10.11 SIP for monotonic clock module ([P-R #6](https://github.com/bbc/pydvbcss/pull/6) and [P-R #7](https://github.com/bbc/pydvbcss/pull/7))
* Improvement: Support for monotonic clock on Android.
  ([P-R #5](https://github.com/bbc/pydvbcss/pull/5) by [Jack Jansen](https://github.com/jackjansen))
* Bugfix: `clock.getEffectiveSpeed()` stuck in infinite loop. ([ceb3f33](https://github.com/bbc/pydvbcss/commit/ceb3f33edb7b94359ecb2cac74046b92b2cc5094))
* Docs: Now correctly links to github source for correct branch/version.
* Docs: Improvements to setup/release process to format PyPI description correctly (by converting to ReStructuredText)

## 0.3.3 : Bugfixes and thread safety improvements (20 Apr 2016)

* Build: Migrated to hosting documentation on readthedocs.org and doing build checks with travis-ci.org
* Bugfix: improvements to thread safety
* Bugfix: incorrect arguments on disconnect handler in CIIClient

## 0.3.2 : Bugfixes and minor API enhancements (17 Dec 2015)

* Bugfix: Initialiser for `CIIServer` class to avoid corruption of default value for `initialCII` if a 2nd CII server is instantiated
* API addition: Added `copy()` methods to all classes representing JSON messages.
* Bugfix: `TSClient` class did not correctly handle when contentId is null
* Bugfix: `examples/TSClient.py` now exits when the connection is closed.

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
