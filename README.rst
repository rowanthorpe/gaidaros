===================================================
Gaidaros: async server framework for control-freaks
===================================================

Gaidaros is an async socket server framework which has been
designed for network developers, with an emphasis on easy
low-level configurability and speed, with sane standard
defaults. This means it can be quickly reused and adapted
to each new project's requirements, while keeping features
out of the way unless requested.

Its first iteration is presently in alpha phase (e.g.
edge-triggered epoll only), but has a clear list of
development milestones ahead. See the TODO.txt file for
details.

Gaidaros (Γάιδαρος) is Greek for donkey. I like donkeys.
This framework doesn't try to implement every trendy feature
under the sun, it just tries to do all the basics accurately
and reliably - like a donkey. So, that's the naming rationale
issue out of the way...

Features
--------

* Minimalism (priority on leanness, speed, configurability
  and base completeness rather than added features)

* Thin wrapper to underlying async socket mechanisms

* Everything configurable by config-files and passed
  arguments

* Pass in handlers by name, (module, class) or as
  pre-created functions, methods or code objects

* *TODO*: Multiple server processors can be run on the polling
  socket using multiprocessing (or a pool thereof)

* *TODO*: Handlers can be run in threads, greenthreads,
  multiprocesses, and pools of any of those three

* *TODO*: Handlers can be run on a cluster using parallel
  processing ("pp"/"pyparallel"). Cluster nodes can in turn
  use threads, greenthreads, multiprocesses, or pools
  thereof too

* IPv4 and/or IPv6, *TODO*: SSL, etc

* TCP, *TODO*: UDP, unixsocket, etc

* *TODO*: Can be used with various frontends (e.g. Tornado)


Installation
------------

From pypi
~~~~~~~~~

::

    $ pip install gaidaros

To install Gaidaros using pip you must make sure you have a
recent version of distribute installed

::

    $ curl -O http://python-distribute.org/distribute_setup.py
    $ sudo python distribute_setup.py
    $ easy_install pip

From source
~~~~~~~~~~~

::

    $ git clone https://github.com/rowanthorpe/gaidaros.git
    $ cd gaidaros && pip install -r requirements.txt

From latest released tarball
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

    $ wget --no-check-certificate https://api.github.com/repos/rowanthorpe/gaidaros/tarball/0.1.1


Build Status
------------

When properly integrated with Travis the project's status
should appear below this:

.. image:: https://secure.travis-ci.org/rowanthorpe/gaidaros.png?branch=master
   :alt: Build Status
   :target: https://secure.travis-ci.org/rowanthorpe/gaidaros


Author
------
Rowan Thorpe <rowan@rowanthorpe.com>


License
-------

Gaidaros uses the MIT license, check LICENSE file.


Contributors
------------

 * Just Rowan, so far...


Thanks also to
--------------

 * Scott Doyle for the `well-written blog-post about epoll <http://scotdoyle.com/python-epoll-howto.html>`_ which inspired me to start this project.


.. figure:: http://farm1.staticflickr.com/10/11189916_202acb3d5a_z.jpg
   :width: 50%
   :alt: "donkey kiss" image by wgdavis (CC BY-NC-SA 2.0)
   :target: http://www.flickr.com/photos/garth/11189916/

   "Donkey kiss" image from `flickr <http://www.flickr.com/photos/garth/11189916/>`_ (CC BY-NC-SA 2.0)
