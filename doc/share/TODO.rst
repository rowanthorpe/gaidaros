====
TODO
====

*See sample code at http://code.activestate.com/recipes/574454-thread-pool-mixin-class-for-use-with-socketservert for threadpools*

*Bracketed version numbers are intended milestones for each goal*

* bin/gaidaros & lib/gaidaros.py - IMPORTS:

 - [v0.4] signal (propagate interrupts), daemon, argparse (instead of getopt)

 - [v0.5] mp, threading, gevent.?, doctest, from timeit import Timer

 - [v2.0] pp/pyparallel (cluster handlers), zlib (compressed streams)

 - [v2.5] pyuv (platform portability), cython (speed)

 - [v2.7] uzmq (to facilitate using various protocols) [not sure about this yet]

 - [v3.0] tornado_pyuv, etc (frontends), gettext, locale

* bin/gaidaros - OPTIONS:

 - [v0.4]

   -d
       Daemon (bool)
         * default = False

   -k
       TCP Cork (bool)
         * default = False [Cork = off]

   -K
       TCP Nodelay (bool)
         * default = False [use buffering]

   -A
       disable Nagle's Algorithm (bool)
         * default = False [Nagle = on]

 - [v0.5]

   -S arg
       Server type (str)
         * "" = blocking
         * "proc" = spawn multiprocessors
         * "procpool" = multiprocessor pool
         * default = ""

   -X arg
       Handler type (str)
         * "" = blocking
         * "proc" = spawn multiprocessors
         * "procpool" = multiprocessor pool
         * "thread" = spawn threads
         * "threadpool" = thread pool
         * "gthread" = spawn green threads
         * "gthreadpool" = green thread pool
         * default = ""

   -N arg
      Server pool size (int)
         * "0" = number of cpu cores present
         * default = "0"

   -n arg
      Handler pool size (int)
         * default = "30"

   -Y
      Run profiling

   -Q
      Run tests from docstrings

 - [v2.0]

   -q arg
      Compress streams with (str)
         * "none"
         * "zlib"
         * "gzip"
         * "lzo"
         * default = "none"

   -C arg
      Cluster nodes, handlers (array)
         * "*" = broadcast
         * default = ""

   -s arg
      cluster node Secret password/s (str/array)
         * "" = no security
         * default = ""

*...make the following polymorphic. Single values map to all cluster nodes, otherwise array lengths must match number of nodes. Can't use arrays when "-C ['*']" is used.*

   -S arg
      Server type/s (str/array)
         * [string-values and meanings are the same as in version 3]

   -H arg
      Handler type/s (str/array)
         * [string-values and meanings are the same as in version 3]

   -N arg
      Server pool size/s (int/array)
         * "0" = number of cpu cores present
         * default = "0"

   -n arg
      Handler pool size/s (int/array)
         * default = "30"

 - [v2.5]

   -T arg
      Polling type (str) [...is this useful/worth it?]
         * "edge" = edge-triggered
         * "level" = level-triggered
         * "completion" = MS-style...
         * default = "edge"

 - [v2.7]

   -P arg
      Protocol (str)
         * "TCP"
         * "UDP"
         * "unixsocket"
         * etc...
         * default = "TCP"

 - [v3.0]

   -f arg
      Frontend (str)
         * "" = no-frontend
         * e.g. "tornado", ...
         * default = ""

* etc/gaidaros/gaidaros.conf - CONF:

 - [v0.4]::

     [global]
     daemon = False
     disable_nagle = False

 - [v0.5]::

     [server]
     pool_types = 
     pool_sizes = 0
     [handler]
     pool_types = 
     pool_sizes = 30
     [config]
     file = ~/.gaidaros.conf

 - [v2.0]::

     [cluster]
     nodes = 
     secrets = 

 - [v2.5]::

     [global]
     polling_type = edge

 - [v2.7]::

     [global]
     protocol = TCP

 - [v3.0]::

     [global]
     frontend = 
     locale =
     language =


* OTHER:

 - [v0.3.14]::

     * use ConfigParser correctly (and then remove all the redundant "defaults" code)
     * perhaps create reusable internal socket pool rather than tearing down and rebuilding each (will
       especially speed up SSL)
     * handle more wrap_socket options like do_handshake_on_connect=, suppress_ragged_eofs=, ciphers=, etc
     * perhaps (do all init in __new__?) and set all values in __slots__ rather than __dict__, for speedup?
     * check if sets or lists(?!) are possible and faster than dicts for storing requests, etc
     * use setting ONESHOT for epoll rather than tracking a one_req var (oneclient -> ONESHOT on the listener,
       onequery -> ONESHOT on each spawned connection)
     * (carefully) remove/gitignore-hide files which are generated from .in files (e.g. lib/gaidaros.py...)
     * catch up CHANGES.txt file
     * create pidfile in sys_run when ioloop starts, remove when it stops
     * set configurable alarm-triggered reaper for zombie connections (GC) while ioloop runs

 - [v0.4]::

     * work out proper minimum requirements (python version, etc) for packaging

 - [v0.5]::

     * allow config to chain-source configs (limited functionality and locations though, so user can't hijack
       the system).

 - [v2.5]::

     * run proper benchmark tests to compare to leading async servers, then profile loops, etc. Based on that
       use cython syntax to speed things up.

 - [v3.0]::

     * config directory with other example handlers (e.g. HTTP, SMTP, etc)
