Caltech Digital Borrowing System
================================

[![License](https://img.shields.io/badge/License-BSD%203--Clause-blue.svg?style=flat-square)](https://choosealicense.com/licenses/bsd-3-clause)


Table of contents
-----------------

* [Introduction](#introduction)
* [Installation](#installation)
* [Running the server on localhost](#running-the-server-on-localhost)
* [General information](#general-information)
* [License](#license)
* [Acknowledgments](#authors-and-acknowledgments)


Introduction
------------

Caltech DIBS ("_**Di**gital **B**orrowing **S**ystem_") is the Caltech Library's basic [controlled digital lending](https://en.wikipedia.org/wiki/Controlled_digital_lending) system.


Installation
------------

To install this locally, you will need to clone not just the main repo contents but the branch and submodules as well.  There are multiple ways of doing this; I use a script I wrote called [`git-clone-complete`](https://github.com/mhucka/small-scripts/blob/main/git-scripts/git-clone-complete) for doing deep clones of github repositories:

```sh
git-clone-complete https://github.com/caltechlibrary/dibs
```


Running the server on localhost
-------------------------------

First, install the Python dependencies on your system or your virtual environment:

```sh
pip3 install -r requirements.txt
```

Prior to running the server for the first time, for testing purposes, you may want to add some sample data. This can be done by running the script [`load-mock-data.py`](load-mock-data.py) in the current directory:

```sh
python3 load-mock-data.py
```

To demo the viewer with actual content, a manifest needs to be added to the subdirectory named [`manifests`](manifests).  The manifest must be named using the pattern `NNNN-manifest.json`, where `NNNN` is the barcode.

The script [`run-server`](run-server) starts the server running; it assumes you are in the current directory, and it takes a few arguments for controlling its behavior:

```sh
./run-server -h
```

By default it starts the server on `localhost` port 8080.

To run with debug tracing, use the `-@` option with an argument telling it where to send the output.  Using `-` will send it to stdout and using a file name will redirect it to a file.  For example,

```sh
./run-server -@ /tmp/debug.log
```

It's useful to have 2 shell windows open in that case: one where you start the server, and with `tail -f /tmp/debug.log` to see the trace.


Logging in
----------

The current demo server only implements a simple login scheme for code develop purposes only.  Here is a summary of how it works:

* Login status is determined by a session cookie
* The page at `/` doesn't nothing but show a welcome message
* The page at `/login` lets you log in. The login verification only checks for the password; it lets you use any email address. The password is set in `settings.ini`. 
* Once logged in, that's when `/list` and other pages become accessible.
* To log out, visit `/logout` and that's all (responds to HTTP GET).


General information
-------------------

Settings are stored in the file [`settings.ini`](settings.ini).  This file is read at run time by the server and database components.

### _About Peewee_

The definition of the database is in [`dibs/database.py`](dibs/database.py).  The interface is defined in terms of high-level objects that are backed by an SQLite database back-end.  The ORM used is [Peewee](http://docs.peewee-orm.com/en/latest/).

Worth knowing: Peewee queries are lazy-executed: they return iterators that must be accessed before the query is actually executed.  Thus, when selecting items, the following returns a Peewee `ModelSelector`, and not a single result or a list of results:

```python
Item.select().where(Item.barcode == barcode)
```

and you can't call something like Python's `next(...)` on this because it's an iterator and not a generator.  You have to either use a `for` loop, or create a list from the above before you can do much with it.  Creating lists in these cases would be inefficient, but we have so few items to deal with that it's not a concern currently.


### _About Bottle_

The definition of the service endpoints and the behaviors is in [`dibs/server.py`](dibs/server.py).  The endpoints are implemented using [Bottle](https://bottlepy.org).

The web server used at the moment is the development server provided by Bottle.  It has live reload built-in, meaning that changes to the `.py` files are picked up automatically and the server updates its behavior on the fly.

See http://bottlepy.org/docs/dev/tutorial.html#auto-reloading for an important note about Bottle: when it's running in auto-reload mode, _"the main process will not start a server, but spawn a new child process using the same command line arguments used to start the main process. All module-level code is executed at least twice"_.  This means some care is needed in how the top-level code is written.  Useful to know is that code can distinguish whether it's in the parent or child process by looking for the presence of the environment variable `'BOTTLE_CHILD'` set by Bottle in the child process.


License
-------

Software produced by the Caltech Library is Copyright (C) 2021, Caltech.  This software is freely distributed under a BSD/MIT type license.  Please see the [LICENSE](LICENSE) file for more information.

This repository includes other software as submodules.  They have their own software licenses.


Acknowledgments
---------------

This work was funded by the California Institute of Technology Library.

<div align="center">
  <br>
  <a href="https://www.caltech.edu">
    <img width="100" height="100" src="https://raw.githubusercontent.com/caltechlibrary/dibs/main/.graphics/caltech-round.png">
  </a>
</div>
