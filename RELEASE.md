# Release process for pydvbcss

## Explanation of the process sequence

Assumption that the current state of *master* will constitute the release...

#### 1. Pre-release checks

Make the following checks before performing a release:
   * Do all unit tests pass?
   * Do all examples work?
   * Does documentation build?


#### 2. Update VERSION and CHANGELOG

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


#### 3. Create release branch 

Create the branch, naming it after the release version number (just the number).

In the branch, now modify (and commit) the VERSION file, changing "latest" to "release".


#### 4. Create a new release on GitHub based on the new branch

Put a shorter summary of the new changelog items into the release notes. Make the tag name the version number
- the same as the branch name.


#### 5. Update documentation builds on gh-pages

Run the documentation build process to build documentation for:

* This new "release" branch ("new")
* *master* branch ("latest")

Note that these are slightly different (because of the 2nd line in the `VERSION` file)

Checkout the [gh-pages](https://github.com/bbc/pydvbcss/tree/gh-pages) branch and make the following commits:

* replace the contents of [`docs/latest`](https://github.com/bbc/pydvbcss/tree/gh-pages/docs/latest)
  with the documentation build for the "latest" state of master.

* put into `docs/XXXX` the documentation build for the "new" release branch, where XXXX is the version number

Then push the commits up to GitHub.

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

### 5. Update documentation builds on gh-pages
    
First, build and copy the documentation for the release and stash it somewhere temporarily.

    $ git status
    On branch X.Y.Z
    Your branch is up-to-date with 'origin/master'.
    nothing to commit, working directory clean
    
    $ python setup.py build_sphinx
    $ cp -R build/sphinx/html /tmp/X.Y.Z
    
Now switch back to master and do the same for the latest state of master:

    $ git checkout master
    $ python setup.py build_sphinx
    $ cp -R build/sphinx/html tmp/latest
    
Now switch to gh-pages and ensure it is synced with GitHub:

    $ git checkout gh-pages
    $ git pull origin gh-pages
    
And put the new documentation builds in place:

    $ cp -R /tmp/X.Y.Z docs/
    $ git add docs/X.Y.Z

    $ git rm docs/latest
    $ cp -R /tmp/latest docs/
    $ git add docs/latest
    
    $ git commit -m "Updated docs for new release and latest changes in master"
    
At this point the `docs` dir should contain:

* a subdir `X.Y.Z` (named after the release version) containing the HTML documentation for
  that version. `index.html` should should describe the release version as being *"X.Y.Z-release"*
  
* a subdir `latest` containing the HTML documentation built from *master*. `index.html` should describe the
  release version as being *"X.Y.Z-latest"*
  
Push to GitHub:

    $ git push origin gh-pages
    
Upload to PyPI:

... first uploading to the test service to check everything is okay:

    $ git checkout <<release-branch>>
    $ sudo python setup.py sdist upload -r pypitest
    
... then going live:

    $ sudo python setup.py sdist upload -r pypi
