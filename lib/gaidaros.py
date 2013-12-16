#!/usr/bin/env python
# -*- coding: utf-8 -*-

#NB: "unicode" introduces more problems than it solves, if we want to also be able to
#    handle arbitrary binary data "strings" (which often don't have a unicode
#    representation). For that reason we now only use binstrings, and the handler has
#    to deal with it explicitly if you want it. Even if you override decode_request()
#    and encode_response() to decode to Python's "unicode" in the handler, don't be
#    tempted to pass back u'' instead of b'', it will throw a TypeError. Do the
#    b'' -> u'' inside handle_request() (and maybe end_request() and split_request())
#    if you really need it, but it *will* slow things down. My tests instantly started
#    serving five times faster when I removed the redundant UTF-8 -> unicode() logic...

"""
Async server micro-framework for control freaks
"""
__version__ = '0.3.13'

import sys, os, ConfigParser, inspect, importlib, socket, select, errno, ast
try:
    import ssl
    has_ssl = True
except ImportError:
    has_ssl = False

def _print_nl(data, ostream=sys.stdout):
    ostream.write(data + ('\n', '')[data[-1:] == '\n'])

def usage(ostream=sys.stderr):
    pass

def warn(warning, ostream=sys.stderr, with_usage=False):
    if with_usage:
        usage(ostream=ostream)
        ostream.write('\n')
    _print_nl(os.path.basename(__file__) + ': ' + warning, ostream=ostream)

def die(warning=None, stack=None, with_usage=False):
    if warning:
        warn(warning, with_usage=with_usage)
    if __name__ == '__main__':
        if stack:
            sys.stderr.write('\n' + stack)
        sys.exit(1)
    raise

def log(*args):
    for message in args:
        warn(message, ostream=sys.stderr)

class Gaidaros(object):

    _globals = globals()
    
    def __init__(self, verbose=None, conf=None, host=None, port=None, ip_version=None, \
                 backlog=None, poll_timeout=None, recv_size=None, \
                 use_ssl=None, ssl_certfile=None, ssl_keyfile=None, \
                 ssl_cert_reqs=None, ssl_ca_certs=None, ssl_version=None, die_on_error=None, \
                 handler_class=None, handler_class_args=None, handler_class_kwargs=None, handler_module=None, \
                 handle_request=None, end_request=None, split_request=None, \
                 decode_request=None, encode_response=None):
        _proc = {
            'end_request': end_request,
            'split_request': split_request,
            'handle_request': handle_request,
            'decode_request': decode_request,
            'encode_response': encode_response,
        }
        for _prockey in _proc.keys(): # eager-evaluate as we are changing the dict in the loop
            _proc[_prockey + '_name'] = None
        if conf:
            conf = str(conf)
            ## source conf for default settings
            self.cnf = ConfigParser.ConfigParser()
            self.cnf.MAX_INTERPOLATION_DEPTH = 3
            cnf_fp = open(os.path.expanduser(conf))
            self.cnf.readfp(cnf_fp)
            cnf_fp.close()
            sys_path = self.cnf.get('dir', 'lib')
            sys_run = self.cnf.get('dir', 'run')
            if sys_path and sys_path not in sys.path:
                sys.path.insert(0, os.path.expanduser(sys_path))
            if verbose is None:
                verbose = self.cnf.getboolean('parameter', 'verbose')
            if host is None:
                host = self.cnf.get('parameter', 'host')
            if port is None:
                port = self.cnf.getint('parameter', 'port')
            if ip_version is None:
                ip_version = self.cnf.getint('parameter', 'ip_version')
            if backlog is None:
                backlog = self.cnf.getint('parameter', 'backlog')
            if poll_timeout is None:
                poll_timeout = self.cnf.getint('parameter', 'poll_timeout')
            if recv_size is None:
                recv_size = self.cnf.getint('parameter', 'recv_size')
            if use_ssl is None:
                use_ssl = self.cnf.getboolean('parameter', 'use_ssl')
            if ssl_certfile is None:
                ssl_certfile = self.cnf.get('parameter', 'ssl_certfile')
            if ssl_keyfile is None:
                ssl_keyfile = self.cnf.get('parameter', 'ssl_keyfile')
            if ssl_cert_reqs is None:
                ssl_cert_reqs = self.cnf.getint('parameter', 'ssl_cert_reqs')
            if ssl_ca_certs is None:
                ssl_ca_certs = self.cnf.get('parameter', 'ssl_ca_certs')
            if ssl_version is None:
                ssl_version = self.cnf.getint('parameter', 'ssl_version')
            if die_on_error is None:
                die_on_error = self.cnf.getboolean('parameter', 'die_on_error')
            if handler_module is None:
                handler_module = self.cnf.get('handler', 'module')
            if handler_class is None:
                handler_class = self.cnf.get('handler', 'class')
            if handler_class_args is None:
                _tmpvar = self.cnf.get('handler', 'class_args')
                if _tmpvar not in (None, ''):
                    handler_class_args = tuple(ast.literal_eval(_tmpvar))
            if handler_class_kwargs is None:
                _tmpvar = self.cnf.get('handler', 'class_kwargs')
                if _tmpvar not in (None, ''):
                    handler_class_kwargs = dict(ast.literal_eval(_tmpvar))
            for _prockey in _proc:
                if _prockey[-5:] != '_name' and _proc[_prockey] in (None, ''):
                    _proc[_prockey] = self.cnf.get('handler', _prockey)
        ## set the defaults not specified in the conf
        if verbose in (None, ''):
            verbose = False
        if port in (None, ''):
            port = 8080
        if ip_version in (None, ''):
            ip_version = 0
        if host in (None, ''):
            if ip_version in (0, 6):
                host = '::'
            else:
                host = '0.0.0.0'
        if backlog in (None, ''):
            backlog = 50
        if poll_timeout in (None, ''):
            poll_timeout = 1
        if recv_size in (None, ''):
            recv_size = 1024
        if use_ssl in (None, ''):
            use_ssl = False
        if ssl_cert_reqs in (None, ''):
            ssl_cert_reqs = ssl.CERT_NONE
        if ssl_ca_certs in (None, ''):
            ssl_ca_certs = '/etc/ca-certificates.conf' # Debian default location
        if ssl_version in (None, ''):
            ssl_version = ssl.PROTOCOL_TLSv1
        if die_on_error in (None, ''):
            die_on_error = True
        if handler_module in (None, ''):
            handler_module_name = ''
            handler_module = None
        elif isinstance(handler_module, basestring):
            handler_module_name = handler_module
            handler_module = importlib.import_module(handler_module_name)
        elif inspect.ismodule(handler_module):
            if handler_module_name in (None, ''):
                handler_module_name = handler_module.__name__
        else:
            raise TypeError('handler_module is not a valid module or name of one. It is: {} (type {})'.format(handler_module, type(handler_module)))
        if handler_class in (None, ''):
            handler_class_name = ''
            handler_class = None
            handler_class_args = ()
            handler_class_kwargs = {}
        elif isinstance(handler_class, basestring):
            handler_class_name = str(handler_class)
            if handler_module is not None and hasattr(handler_module, handler_class_name) and inspect.isclass(getattr(handler_module, handler_class_name)):
                handler_class = getattr(handler_module, handler_class_name)
            elif self._globals.has_key(handler_class_name) and inspect.isclass(eval(handler_class_name)):
                handler_class = eval(handler_class_name)
            else:
                raise ValueError('handler_class is not the name of a valid class. It is: {}'.format(handler_class_name))
        elif inspect.isclass(handler_class):
            if handler_class_name in (None, ''):
                handler_class_name = str(handler_class.__name__)
        else:
            raise TypeError('handler_class is not a valid class. It is: {} (type {})'.format(handler_class, type(handler_class)))
        for _prockey in _proc:
            if _prockey[-5:] != '_name' and _proc[_prockey] in (None, ''):
                _proc[_prockey] = _prockey
        if use_ssl and not has_ssl:
            raise NotImplementedError('use_ssl specified but ssl module not available or usable')
        ## set long-lived vars including handler instance
        for x in 'verbose', 'host', 'port', 'ip_version', 'backlog', 'poll_timeout', \
                 'recv_size', 'use_ssl', 'ssl_certfile', 'ssl_keyfile', 'ssl_cert_reqs', \
                 'ssl_ca_certs', 'ssl_version', 'die_on_error':
            setattr(self, x, locals()[x])
        # POSIX.1-2001 allows either error, and doesn't require them to have same value,
        # so check for both (merging identical integers if any, too).
        if use_ssl:
            self.ssl_wouldblock_errors = tuple(frozenset((ssl.SSL_ERROR_WANT_READ, ssl.SSL_ERROR_WANT_WRITE)))
        self.socket_wouldblock_errors = tuple(frozenset((errno.EWOULDBLOCK, errno.EAGAIN)))
        if handler_class is None:
            self.handler = None
        else:
            self.handler = handler_class(*handler_class_args, **handler_class_kwargs)
        # The following looped code is perverse but saves more than 100 lines of "pythonic"
        # (and less DRY) code
        _routine_defaults = {
            'end_request': lambda _request: '\n' in _request,
            'split_request': lambda _request: (
              [_splitpoint for _splitpoint in (_request.find('\n') + 1,)],
              [_trailing for _trailing in (_splitpoint - 1 < len(_request),)],
              ((_request,''),(_request[:_splitpoint],_request[_splitpoint:]))[_trailing],
            )[-1],
            'handle_request': lambda _request: (_request, False),
            # See note at top of script. Now not doing "decoding" from utf8 for that reason.
            'decode_request': lambda _request: _request,
            'encode_response': lambda _response: _response, # Remember _response is: tuple(data, keepalive_flag)
        }
        for _routine in 'end_request', 'split_request', 'handle_request', 'decode_request', 'encode_response':
            if _proc.has_key(_routine):
                if isinstance(_proc[_routine], basestring):
                    _proc.update({_routine + '_name': str(_proc[_routine])})
                    if self.handler and hasattr(self.handler, _proc[_routine + '_name']) and inspect.method(getattr(self.handler, _proc[_routine + '_name'])):
                        _proc.update({_routine: getattr(self.handler, _proc[_routine + '_name'])})
                    elif self._globals.has_key(_proc[_routine + '_name']) and inspect.isroutine(self._globals[_proc[_routine + '_name']]):
                        _proc.update({_routine: self._globals[_proc[_routine + '_name']]})
                    elif _routine == _proc[_routine + '_name']:
                        _proc.update({_routine: _routine_defaults[_routine]})
                    else:
                        try:
                            if len(_proc[_routine]) > 7 and _proc[_routine][:7] == 'lambda ':
                                _proc.update({_routine: eval(_proc[_routine + '_name'])})
                            else:
                                raise SyntaxError
                        except SyntaxError:
                            raise ValueError('{} is not the name of a valid method or function, and doesn\'t look like a valid lambda. It is: {}'.format(_routine, _proc[_routine + '_name']))
                elif inspect.isroutine(_proc[_routine]):
                    if _proc[_routine + '_name'] in (None, ''):
                        _proc.update({_routine + '_name': str(_proc[_routine].__name__)})
                else:
                    raise TypeError('{} is not a valid function or method. It is: {}'.format(_routine, _proc[_routine]))
        for _prockey in _proc:
            setattr(self, _prockey, _proc[_prockey])

    def _setup(self):
        ## setup socket - ip version(s), host, port, backlog, ssl_opts
        if self.ip_version == 4:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        else:
            sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
            if self.ip_version == 6:
                sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 1)
            else:
                sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((self.host, self.port))
        sock.listen(self.backlog)
        sock.setblocking(0)
        sock_fileno = sock.fileno()
        if self.use_ssl:
            self.ssl_opts = {'server_side': True, 'certfile': os.path.realpath(self.ssl_certfile), 'cert_reqs': self.ssl_cert_reqs, 'ca_certs': os.path.realpath(self.ssl_ca_certs), 'ssl_version': self.ssl_version}
            if self.ssl_keyfile is not None:
                self.ssl_opts.update({'keyfile': os.path.realpath(self.ssl_keyfile)})
        ## setup poller
        epoll = select.epoll()
        epoll.register(sock_fileno, select.EPOLLIN | select.EPOLLET)
        return sock, sock_fileno, epoll

    def ioloop(self, one_req=False):
        ## initial state
        finished_accepting = False
        shutdown_wanted = False
        response  = ''
        connections = {}
        requests = {}
        dec_requests = {}
        responses = {}
        keepalive_flags = {}
        sock, sock_fileno, epoll = self._setup()
        ## link directly to remaining self-vars from locals to avoid lookups and speedup the loop
        use_ssl = self.use_ssl
        poll_timeout = self.poll_timeout
        recv_size = self.recv_size
        verbose = self.verbose
        end_request = self.end_request
        handle_request = self.handle_request
        split_request = self.split_request
        decode_request = self.decode_request
        encode_response = self.encode_response
        e_register = epoll.register
        e_unregister = epoll.unregister
        e_modify = epoll.modify
        e_poll = epoll.poll
        e_close = epoll.close
        s_accept = sock.accept
        s_close = sock.close
        sel_EPOLLIN = select.EPOLLIN
        sel_EPOLLOUT = select.EPOLLOUT
        sel_EPOLLET = select.EPOLLET
        sel_EPOLLHUP = select.EPOLLHUP
        s_error = socket.error
        s_wouldblock_errors = self.socket_wouldblock_errors
        if use_ssl:
            ssl_opts = self.ssl_opts
            ssl_wrap_socket = ssl.wrap_socket
            ssl_error = ssl.SSLError
            _wouldblock_errors = self.ssl_wouldblock_errors
        else:
            _wouldblock_errors = s_wouldblock_errors
        die_on_error = self.die_on_error
        if die_on_error:
            if use_ssl:
                _sock_error = ssl_error
            else:
                _sock_error = s_error
        else:
            _sock_error = Exception
        ## this whole loop is not very DRY because I have "unrolled" it a bit, on purpose, for speed
        try:
            ## main polling loop
            while not shutdown_wanted:
                events = e_poll(poll_timeout)
                while events:
                    # Iterate through events list until it's empty, iterate backwards so removing items doesn't cause skips
                    for indexno in xrange(len(events) - 1, -1, -1):
                        fileno, event = events[indexno]
                        if fileno == sock_fileno:
                            ## accept new connection
                            if not finished_accepting:
                                try:
                                    connection, address = s_accept()
                                    if use_ssl:
                                        connection = ssl_wrap_socket(connection, **ssl_opts)
                                    connection.setblocking(0)
                                    connection_fileno = connection.fileno()
                                    e_register(connection_fileno, sel_EPOLLIN | sel_EPOLLET)
                                except (socket.error, ssl.SSLError) as e: # catch both types here
                                    if die_on_error:
                                        raise
                                    if one_req:
                                        shutdown_wanted = True
                                else:
                                    if one_req:
                                        finished_accepting = True
                                    connections[connection_fileno] = connection
                                    requests[connection_fileno] = ''
                                    dec_requests[connection_fileno] = ''
                                    responses[connection_fileno] = response
                                    keepalive_flags[connection_fileno] = False
                                    if verbose:
                                        log('=' * 40, 'setup socket ' + str(connection_fileno))
                        else:
                            try:
                                if event & sel_EPOLLIN:
                                    try:
                                        ## read data
                                        requests[fileno] += connections[fileno].recv(recv_size) # don't decode yet (see explanation below)
                                    except _sock_error as e:
                                        if e.args[0] in _wouldblock_errors:
                                            pass
                                    ## process request
                                    try:
                                        dec_requests[fileno] += decode_request(requests[fileno])
                                        requests[fileno] = ''
                                    except ValueError:
                                        # Capture decoding exceptions in case decoding a partial chunk would bork (e.g. on a multibyte
                                        # character split across a read boundary) but a valid request is contained in the beginning of
                                        # the data. Hope that eventually there will be a non-erroring chunk of data to decode...
                                        pass
                                    else:
                                        if end_request(dec_requests[fileno]):
                                            processing_request, dec_requests[fileno] = split_request(dec_requests[fileno])
                                            responses[fileno], keepalive_flags[fileno] = encode_response(handle_request(processing_request))
                                            e_modify(fileno, sel_EPOLLOUT | sel_EPOLLET)
                                            if verbose:
                                                log('-' * 40,
                                                    'processed response for socket ' + str(fileno),
                                                    ' decoded request: ' + repr(processing_request),
                                                    ' encoded response: ' + repr(responses[fileno]),
                                                    ' decoded leftovers: ' + repr(dec_requests[fileno]),
                                                    ' other leftovers: ' + repr(requests[fileno]))
                                elif event & sel_EPOLLOUT:
                                    ## write data
                                    try:
                                        while len(responses[fileno]) != 0:
                                            byteswritten = connections[fileno].send(responses[fileno])
                                            responses[fileno] = responses[fileno][byteswritten:]
                                    except _sock_error as e:
                                        if e.args[0] in _wouldblock_errors:
                                            pass
                                    else:
                                        if keepalive_flags[fileno]:
                                            e_modify(fileno, sel_EPOLLIN | sel_EPOLLET)
                                        else:
                                            e_unregister(fileno)
                                            connections[fileno].shutdown(socket.SHUT_RDWR)
                                            del connections[fileno], requests[fileno], dec_requests[fileno], responses[fileno], keepalive_flags[fileno]
                                            if one_req:
                                                shutdown_wanted = True
                                        if verbose:
                                            log('-' * 40, 'response output to socket ' + str(fileno))
                                elif event & sel_EPOLLHUP:
                                    ## hangup
                                    if verbose:
                                        log('-' * 40, 'hanging up socket ' + str(fileno))
                                    e_unregister(fileno)
                                    connections[fileno].shutdown(socket.SHUT_RDWR)
                                    connections[fileno].close()
                                    del connections[fileno], requests[fileno], dec_requests[fileno], responses[fileno], keepalive_flags[fileno]
                                    if one_req:
                                        shutdown_wanted = True
                            except Exception as e:
                                if die_on_error:
                                    raise
                                e_unregister(fileno)
                                connections[fileno].shutdown(socket.SHUT_RDWR)
                                connections[fileno].close()
                                del connections[fileno], requests[fileno], dec_requests[fileno], responses[fileno], keepalive_flags[fileno]
                                if one_req:
                                    shutdown_wanted = True
                        del events[indexno]
        finally:
            ## cleanup leftover connections
            for fileno in connections.keys(): # eager evaluate
                e_unregister(fileno)
                connections[fileno].shutdown(socket.SHUT_RDWR)
                connections[fileno].close()
            ## unregister and close server
            e_unregister(sock_fileno)
            e_close()
            s_close()
    
    def handle(self):
        self.ioloop(one_req=True)

    def serve(self):
        self.ioloop()

if __name__ == '__main__':
    # If executed directly this runs as a minimal one-line echo server (with
    # only LF end-of-lines, listening on all interfaces, port 8080, IPv4 & IPv6,
    # with no decoding or encoding, with no keepalive or logging to console) in
    # a loop until interrupted (by keyboard or signal).
    server = Gaidaros()
    server.serve()
