=======
Albumin
=======
A script to semi-automatically manage a photograph collection using a git-annex_ repository.
It analyzes the files for their dates and times, compares them and their identification method to existing data in
the repository, and decides which information to keep.

.. _git-annex: https://git-annex.branchable.com/

Rationale
---------
Usually, the image timestamp resides in the Exif_ tags (e.g. ``DateTimeOriginal``).
This standard is widely adopted, so there is no trouble in finding the timestamp from recent, original pictures.
However, some image processing utilities, some social media websites and applications remove this information entirely.
Furthermore, some older pictures might not even have this metadata recorded in these locations, but somewhere else in
a different format. Instead of manually analyzing every file which has a non-Exif timestamp, I've decided to write this
script to partially automate it.

.. _Exif: https://en.wikipedia.org/wiki/Exif

Requirements
------------
- Python 3
- git-annex-adapter_ (v0.1.0)
- pyexiftool_
- pytz
- pygit2
- docopt

.. _git-annex-adapter: https://github.com/alpernebbi/git-annex-adapter
.. _pyexiftool: https://github.com/smarnach/pyexiftool

Workflow
--------
The entire process of creating the photograph collection is like the following:

- ``analyze`` a set of files to see which ones the script can't find any information.
- Manually inspect these files and find a algorithmic method to extract the timestamp.
- Implement the method in ``imdate.py``, add it to the ``ImageDate``'s list of methods
  and to the ``analyze_date()`` function.
- ``analyze`` again to ensure the new method works.
- ``import`` if all files' timestamps look correct.

For further automation, albumin can also set itself as (several) git hooks.

- ``albumin init`` in a repository to create the hooks.
- ``git-annex add`` some pictures.
- ``git commit``. If albumin can't get information for some files, it'll abort the commit and show a report.

Usage
-----
To initialize the repo and set up git hooks::

    $ albumin init [--repo=<repo>]

To analyze the files in the repo's staging area, or the files in a specific path::

    $ albumin analyze [<path>] [--repo=<repo>] [--timezone=<tz>]

To import the files from a specific path::

    $ albumin import <path> [--repo=<repo>] [--timezone=<tz>] [--tag=<tag>:<value>]...

Options
^^^^^^^
By default, albumin tries to use the current folder as the repository and usually fails if you're not in a repository.
To operate on a different repository, add ``--repo=<repo>``.

Analyzing and importing photographs need a timezone, which you can provide with ``--timezone=<tz>``.
You can also set a global default for the repository with ``git config albumin.timezone <tz>``,
or set it during a commit operation like ``git -c albumin.timezone=<tz> commit``.

``--tag=<tag>:<value>`` can be added multiple times to ``import`` to add aditional metadata to all imported photos.

Example
-------
Using albumin as git hooks::

    $ cd /path/to/repo
    $ albumin init
    Initializing git repo at .
    Initializing git-annex at .

    $ cp -r /path/to/photos .
    $ git annex add photos
    add photos/IMG_1386.JPG ok
    (recording state in git...)

    $ git -c albumin.timezone=Europe/Istanbul commit
    Some files in report have no information:
    No Information:
      SHA256E-s0--e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855.txt
      :: /path/to/repo/photos/unknown.txt

    New Keys:
      SHA256E-s3038886--b57a0d20740b09b60b443a01ada04eeb1a69948526c564513a4068d54280efa7.JPG
      :: /path/to/repo/photos/IMG_1386.JPG
      :: 2015-05-16 13:22:16 @ (Europe/Istanbul) (DateTimeOriginal)
    Aborting commit.

    $ git rm photos/unknown.txt --cached
    $ git -c albumin.timezone=Europe/Istanbul commit
    [master a928e3e] Demonstration of git hook functionality
    1 file changed, 1 insertion(+)
    create mode 120000 20161222T071811Z/20150516T102216Z00.JPG

    $ git show
    commit a928e3e256543129a1cca4a033452dd0448b65e1
    Author: John Doe <jdoe@example.com>
    Date:   Thu Dec 22 10:18:11 2016 +0300

        Demonstration of git hook functionality

        [tags]
        batch: 20161222T071811Z
        album: hook

        [report]
        [K+] SHA256E-s3038886--b57a0d20740b09b60b443a01ada04eeb1a69948526c564513a4068d54280efa7.JPG
        [ F] :: photos/IMG_1386.JPG
        [ T] :: 2015-05-16 13:22:16 @ (Europe/Istanbul) (DateTimeOriginal)

    ...

Analyzing and importing manually::

    $ cd /path/to/repo
    $ albumin analyze /path/to/photos --timezone=Europe/Istanbul
    No Information:
      SHA256E-s0--e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855.db
      :: /path/to/photos/thumbs.db

    Updated Keys:
      SHA256E-s2958920--00c73bbf52716a7c6c815e926d8508ca6b1cc7961d5112634be006485e620cef.JPG
      :: /path/to/photos/IMG_1387.JPG
      :: 2015-05-16 13:22:27 @ (Europe/Istanbul) (DateTimeOriginal)
      :: 2015-05-16 13:30:00 @ (Europe/Istanbul) (ManualUntrusted)

    New Keys:
      SHA256E-s2479385--9a064911a6c38eb0fdb255f337c2a5a7d00edc75f107f33a487eb0c32c3404dc.JPG
      :: /path/to/photos/IMG_1388.JPG
      :: 2015-05-16 13:22:43 @ (Europe/Istanbul) (DateTimeOriginal)

    Redundant Keys:
      SHA256E-s3038886--b57a0d20740b09b60b443a01ada04eeb1a69948526c564513a4068d54280efa7.JPG
      :: /path/to/photos/IMG_1386.JPG

Trying to import at this moment will give a ``NotImplementedError``.
After manually removing the thumbs.db file::

    $ albumin import /path/to/photos --timezone Europe/Istanbul --tags album=example
    Batch: 20161222T070940Z

    [tags]
    batch: 20161222T070940Z

    [report]
    [K!] SHA256E-s2958920--00c73bbf52716a7c6c815e926d8508ca6b1cc7961d5112634be006485e620cef.JPG
    [ F] :: /tmp/gitest/imp/IMG_1387.JPG
    [ T] :: 2015-05-16 13:22:27 @ (Europe/Istanbul) (DateTimeOriginal)
    [ t] :: 2015-05-16 13:30:00 @ (Europe/Istanbul) (ManualUntrusted)
    [K+] SHA256E-s2479385--9a064911a6c38eb0fdb255f337c2a5a7d00edc75f107f33a487eb0c32c3404dc.JPG
    [ F] :: /tmp/gitest/imp/IMG_1388.JPG
    [ T] :: 2015-05-16 13:22:43 @ (Europe/Istanbul) (DateTimeOriginal)
    [K=] SHA256E-s3038886--b57a0d20740b09b60b443a01ada04eeb1a69948526c564513a4068d54280efa7.JPG
    [ F] :: /tmp/gitest/imp/IMG_1386.JPG
