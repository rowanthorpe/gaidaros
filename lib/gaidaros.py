#!/usr/bin/env python
# encoding: utf-8
from __future__ import unicode_literals

"""
Async server micro-framework for control freaks
"""
__version__ = '0.3.8'

import sys, os, ConfigParser, inspect, importlib, socket, select, errno, csv

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
                 handler_class=None, handler_class_args=None, handler_module=None, \
                 handle_request=None, end_request=None, split_request=None, \
                 decode_request=None, encode_response=None):
        _proc = {
            'end_request': end_request,
            'split_request': split_request,
            'handle_request': handle_request,
            'decode_request': decode_request,
            'encode_response': encode_response,
        }
        for _prockey in list(_proc): # must not lazy-evaluate as we are changing the dict in the loop
            _proc[_prockey + '_name'] = None
        if conf:
            conf = unicode(conf)
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
            if handler_module is None:
                handler_module = self.cnf.get('handler', 'module')
            if handler_class is None:
                handler_class = self.cnf.get('handler', 'class')
            if handler_class_args is None:
                handler_class_args = tuple(
                  *csv.reader([self.cnf.get('handler', 'class_args').replace('\n','')], skipinitialspace = True, quoting = csv.QUOTE_NONE))
            for _prockey in _proc:
                if _prockey[-5:] != '_name' and _proc[_prockey] in (None, ''):
                    _proc[_prockey] = self.cnf.get('handler', _prockey)
        ## set the defaults not specified in the conf
        if verbose in (None, ''):
            verbose = False
        if host in (None, ''):
            host = '::'
        if port in (None, ''):
            port = 8080
        if ip_version in (None, ''):
            ip_version = 0
        if backlog in (None, ''):
            backlog = 50
        if poll_timeout in (None, ''):
            poll_timeout = 1
        if recv_size in (None, ''):
            recv_size = 1024
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
        elif isinstance(handler_class, basestring):
            handler_class_name = unicode(handler_class)
            if handler_module is not None and hasattr(handler_module, handler_class_name) and inspect.isclass(getattr(handler_module, handler_class_name)):
                handler_class = getattr(handler_module, handler_class_name)
            elif self._globals.has_key(handler_class_name) and inspect.isclass(eval(handler_class_name)):
                handler_class = eval(handler_class_name)
            else:
                raise ValueError('handler_class is not the name of a valid class. It is: {}'.format(handler_class_name))
        elif inspect.isclass(handler_class):
            if handler_class_name in (None, ''):
                handler_class_name = unicode(handler_class.__name__)
        else:
            raise TypeError('handler_class is not a valid class. It is: {} (type {})'.format(handler_class, type(handler_class)))
        for _prockey in _proc:
            if _prockey[-5:] != '_name' and _proc[_prockey] in (None, ''):
                _proc[_prockey] = _prockey
        ## set long-lived vars including handler instance
        self.verbose = verbose
        self.host = host
        self.port = port
        self.ip_version = ip_version
        self.backlog = backlog
        self.poll_timeout = poll_timeout
        self.recv_size = recv_size
        if handler_class is None:
            self.handler = None
        else:
            self.handler = handler_class(*handler_class_args)
        # the following looped code is perverse but saves a *lot* of duplicated code
        # (more than 100 lines of "pythonic" code)
        _routine_defaults = {
            'end_request': lambda request: '\n' in request,
            'split_request': lambda request: (
              [_splitpoint for _splitpoint in (request.find('\n') + 1,)],
              [_trailing for _trailing in (_splitpoint - 1 < len(request),)],
              ((request,''),(request[:_splitpoint],request[_splitpoint:]))[_trailing],
            )[-1],
            'handle_request': lambda request: (request, False),
            'decode_request': lambda request: request.decode('utf-8'),
            'encode_response': lambda response: (response[0].encode('utf-8'), response[1]),
        }
        for _routine in 'end_request', 'split_request', 'handle_request', 'decode_request', 'encode_response':
            if _proc.has_key(_routine):
                if isinstance(_proc[_routine], basestring):
                    _proc.update({_routine + '_name': unicode(_proc[_routine])})
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
                        _proc.update({_routine + '_name': unicode(_proc[_routine].__name__)})
                else:
                    raise TypeError('{} is not a valid function or method. It is: {}'.format(_routine, _proc[_routine]))
        for _prockey in _proc:
            setattr(self, _prockey, _proc[_prockey])

    def _setup(self):
        ## setup socket - ip version(s), host, port, backlog
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
        ## setup poller
        epoll = select.epoll()
        epoll.register(sock_fileno, select.EPOLLIN | select.EPOLLET)
        return sock, sock_fileno, epoll

    def ioloop(self, one_req=False):
        ## initial state
        finished_accepting = False
        shutdown_wanted = False
        response  = b''
        connections = {}
        requests = {}
        responses = {}
        keepalive_flags = {}
        ## setup socket and poller
        sock, sock_fileno, epoll = self._setup()
        try:
            ## main polling loop
            while not shutdown_wanted:
                events = epoll.poll(self.poll_timeout)
                for fileno, event in events:
                    if fileno == sock_fileno and not finished_accepting:
                        ## accept new connection (only once if requested)
                        try:
                            while not finished_accepting:
                                connection, address = sock.accept()
                                if one_req:
                                    finished_accepting = True
                        except socket.error, e:
                            if e.args[0] != errno.EWOULDBLOCK:
                                raise
                        connection.setblocking(0)
                        connection_fileno = connection.fileno()
                        epoll.register(connection_fileno, select.EPOLLIN | select.EPOLLET)
                        connections[connection_fileno] = connection
                        requests[connection_fileno] = b''
                        responses[connection_fileno] = response
                        keepalive_flags[connection_fileno] = False
                    elif event & select.EPOLLIN:
                        ## read data
                        try:
                            requests[fileno] += self.decode_request(connections[fileno].recv(self.recv_size))
                        except socket.error, e:
                            if e.args[0] != errno.EWOULDBLOCK:
                                raise
                        ##NB: use of threads, procs, pp, etc... usefulness starts here
                        if self.end_request(requests[fileno]):
                            processing_request, requests[fileno] = self.split_request(requests[fileno])
                            responses[fileno], keepalive_flags[fileno] = self.encode_response(self.handle_request(processing_request))
                            if self.verbose:
                                log('-' * 40, 'request: ' + processing_request, 'leftover-requests: ' + unicode(requests[fileno]))
                            epoll.modify(fileno, select.EPOLLOUT | select.EPOLLET)
                        ## ...end ends about here
                    elif event & select.EPOLLOUT:
                        ## write data
                        try:
                            while len(responses[fileno]) > 0:
                                byteswritten = connections[fileno].send(responses[fileno])
                                responses[fileno] = responses[fileno][byteswritten:]
                        except socket.error, e:
                            if e.args[0] != errno.EWOULDBLOCK:
                                raise
                        if len(responses[fileno]) == 0:
                            if keepalive_flags[fileno]:
                                epoll.modify(fileno, select.EPOLLIN | select.EPOLLET)
                            else:
                                epoll.modify(fileno, select.EPOLLET)
                                connections[fileno].shutdown(socket.SHUT_RDWR)
                                if one_req:
                                    ## if only once then force closing connection
                                    epoll.unregister(fileno)
                                    connections[fileno].close()
                                    del connections[fileno]
                                    shutdown_wanted = True
                    elif event & select.EPOLLHUP:
                        ## finish connection
                        epoll.unregister(fileno)
                        connections[fileno].close()
                        del connections[fileno]
                        if one_req:
                            shutdown_wanted = True
        finally:
            ## close server
            if locals().has_key('epoll'):
                epoll.unregister(sock_fileno)
                epoll.close()
            if locals().has_key('sock'):
                sock.close()

    def handle(self):
        self.ioloop(one_req=True)

    def serve(self):
        self.ioloop()

if __name__ == '__main__':
    # If executed directly this runs as a minimal one-line echo server (with
    # LF end-of-lines, listening on all interfaces, port 8080, IPv4 & IPv6,
    # with UTF-8 decoding and encoding, with no keepalive or logging to
    # console) in a loop until interrupted (by keyboard or signal).
    server = Gaidaros()
    server.serve()
