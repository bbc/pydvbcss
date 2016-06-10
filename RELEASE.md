# Release process for pydvbcss

## Explanation of the process sequence

Assumption that the current state of *master* will constitute the release...

#### 1. Pre-release checks

Make the following checks before performing a release:
   * Do all unit tests pass?
   * Do all examples work?
   * Does documentation build?


#### 2. Update VERSION and CHANGELOG and README

##### Increment the version number.
   
The version number is in the [`VERSION`](VERSION) file. This is picked up by the documentation build process.

It consists of two lines. The first carries the version number. The structure is: *major* **.** *minor* **.** *revision*.
The *revision* part is *not included* if it is zero '0' (just after a *major* or *minor* increment).
   * *major* = significant incompatible change (e.g. partial or whole rewrite).
   * *minor* = some new functionality or changes that are mostly/wholly backward compatible.
   * *revision* = very minor changes, e.g. bugfixes.

The 2nd line carries the state - whether this is the "latest" code in the master branch, or whether it is a "release".
Leave this as "latest" for the moment.


##### Update the change log
  
The is in the [`CHANGELOG.md`](CHANGELOG.md) file. Ensure it mentions any noteworthy changes since the previous release.


##### Update README

In ['README.md'](README.md) change references to the "master" branch to the name
of release branch that will be used in the next step (which will be the
release version number). The places this occurs includes:

   * the Travis CI build status image link at the beginning.


#### 3. Create release branch 

Create the branch, naming it after the release version number (just the number).

In the branch, now modify (and commit) the VERSION file, changing "latest" to "release".


#### 4. Create a new release on GitHub based on the new branch

Put a shorter summary of the new changelog items into the release notes. Make the tag name the version number
- the same as the branch name.


#### 5. Check documentation builds

_The old process of manually building and pushing to gh-pages is deprecated._

Docs are built automatically by readthedocs.org when the new release tag is generated. Check that the new release
has built correctly and is classified as the "stable" build, here: https://readthedocs.org/projects/pydvbcss/



#### 6. Upload new package to python package index

The process originally followed to register and setup first time was [this one](http://peterdowns.com/posts/first-time-with-pypi.html).

For subsequent releases, do an upload to first *PyPI Test* and only if that succeeds then do an upload to *PyPI Live*.

- - - - -

## Example of release process sequence

This example assumes your local repository is a clone and the working copy is currently at the head of the master branch, and that this is all 
synced with GitHub. The following steps will do a release "X.Y.Z"

    $ git status
    On branch master
    Your branch is up-to-date with 'origin/master'.
    nothing to commit, working directory clean
    
### 1. Run checks

Run unit tests:

    $ python tests/test_all.py
    
Also check the documentation builds:

    $ python setup.py build_sphinx

... and manually review areas where it will have changed

And run all examples and check they work!



### 2. Update VERSION and CHANGELOG

Update the version number in `master`, e.g. using `vi`:
  
    $ vi VERSION
        .. change version number line only ..
    $ vi CHANGELOG.md
        .. update change log  ..
    $ git add VERSION
    $ git add CHANGELOG.md
    $ git commit -m "Version number increment and Changelog update ready for release"

And push to GitHub:

    $ git push origin master

### 3. Create release branch

Create new branch (locally)

    $ git checkout -b 'X.Y.Z'

Update VERSION to mark as "release" within the branch

    $ vi VERSION
       .. change "latest" to "release"
    $ git add VERSION
    $ git commit -m "Version marked as release."
    
Push branch up to github (and set local repository to track the upstream branch on origin):

    $ git push -u origin 'X.Y.Z'
    

### 4. Create a new release on GitHub based on the new branch

Now use the [new release](https://github.com/bbc/pydvbcss/releases/new) function on GitHub's web interface to
mark the branch 'X.Y.Z' as a new release.

### 5. Update documentation builds on gh-pages (deprecated)

Documentation is now automatically rebuilt and hosted by readthedocs.org. It
will be picked up when the new release is tagged.

    
### 6. Upload to PyPI:

To upload, you must have [pandoc](http://pandoc.org/) installed as a command
line tool. This is needed to convert the README from [Markdown](https://daringfireball.net/projects/markdown/)
to [ReStructuredText](http://docutils.sourceforge.net/docs/ref/rst/introduction.html) because PyPI
requires it.

    $ sudo apt-get install pandoc       # Debian/ubuntu Linux
    $ sudo port install pandoc          # Mac Ports

... first uploading to the test service to check everything is okay:

    $ git checkout <<release-branch>>
    $ sudo python setup.py sdist register upload -r pypitest
    
... then going live:

    $ sudo python setup.py sdist register upload -r pypi

The conversion of the README alone can be checked by doing a 'register' without
an 'upload'.
