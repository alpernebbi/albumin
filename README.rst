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
- git-annex-adapter_
- pyexiftool_
- pytz

.. _git-annex-adapter: https://github.com/alpernebbi/git-annex-adapter
.. _pyexiftool: https://github.com/smarnach/pyexiftool

Workflow
--------
The entire process of creating the photograph collection is like the following:

- ``--analyze`` a set of files to see which ones the script can't find any information.
- Manually inspect these files and find a algorithmic method to extract the timestamp.
- Implement the method in ``imdate.py``, add it to the ``ImageDate``'s list of methods
  and to the ``analyze_date()`` function.
- ``--analyze`` again to ensure the new method works.
- ``--import`` if all files' timestamps look correct.


Usage
-----
The first positional argument is the repository path and is required (except for using ``--help``).
Folders, git repositories and git-annex repositories will be created if they don't exist at the given path.
A simple explanation is::

    $ albumin /path/to/repo [action [option ...]]

Actions
^^^^^^^
To show a help message::

    $ albumin --help

To analyze the dates of the photographs from a folder::

    $ albumin /path/to/repo --analyze /path/to/photos

To import files from the folder::

    $ albumin /path/to/repo --import /path/to/photos

To execute multiple actions with one repo::

    $ albumin /path/to/repo --interactive
    alb >> --analyze /path/to/photos
    alb >> --import /path/to/photos
    alb >> exit

Options
^^^^^^^
``--timezone tz`` can be added to both actions to assume the photos belong to a specific timezone.
If not given, the timezone value from repository metadata is used if it exists, UTC if it doesn't.

``--tags tag1=value1 [tag2=value2 ...]`` can be added to ``--import`` to add aditional fields to all imported photos.

Example
-------
::

    $ albumin /path/to/repo --interactive
    alb >> --analyze /path/to/photos --timezone Europe/London
    No new information:
        /path/to/photos/IMG_0321.JPG
        /path/to/photos/IMG_0322.JPG
    New files:
        /path/to/photos/IMG_0323.JPG: 2012-09-04 15:43:17+01:00 (DateTimeOriginal)
        /path/to/photos/IMG_0324.JPG: 2012-09-04 15:43:21+01:00 (DateTimeOriginal)
    No information:
        /path/to/photos/thumbs.db

Trying to import at this moment will give a ``NotImplementedError``.
After manually removing the thumbs.db file::

    alb >> --import /path/to/photos --timezone Europe/London --tags album=London
