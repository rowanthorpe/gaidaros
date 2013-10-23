#/usr/bin/env python
# encoding: utf-8
from __future__ import unicode_literals
import sys, os, re, ConfigParser, inspect, importlib, socket, select, errno

"""
Async server micro-framework for control freaks
"""
__version__ = '0.3.0'
__all__ = ('Gaidaros', 'usage', 'warn', 'die', 'log')

def __print_nl(data, ostream=sys.stdout):
    ostream.write(data + ('\n', '')[data[-1:] == '\n'])

def usage(ostream=sys.stderr):
    pass

def warn(warning, ostream=sys.stderr, with_usage=False, usage_func=None):
    if with_usage:
        if hasattr(usage_func, '__call__'):
            usage_func(ostream=ostream)
        else:
            usage(ostream=ostream)
        ostream.write('\n')
    __print_nl(os.path.basename(main.__file__) + ': ' + warning, ostream=ostream)

def die(warning=None, stack=None, with_usage=False, usage_func=None):
    if warning:
        warn(warning, with_usage=with_usage, usage_func=usage_func)
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
                 handle_request=None, end_request=None, split_request=None):
        if conf:
            ## source conf for the remaining settings
            self.cnf = ConfigParser.ConfigParser()
            self.cnf.MAX_INTERPOLATION_DEPTH = 3
            cnf_fp = open(os.path.expanduser(conf))
            self.cnf.readfp(cnf_fp)
            cnf_fp.close()
            if verbose is None:
                verbose = self.cnf.getbool('global', 'verbose')
            if host is None:
                host = self.cnf.get('global', 'host')
            if port is None:
                port = self.cnf.getint('global', 'port')
            if ip_version is None:
                ip_version = self.cnf.getint('global', 'ip_version')
            if backlog is None:
                backlog = self.cnf.getint('global', 'backlog')
            if poll_timeout is None:
                poll_timeout = self.cnf.getint('global', 'poll_timeout')
            if recv_size is None:
                recv_size = self.cnf.getint('global', 'recv_size')
            if handler_class is None:
                handler_class = self.cnf.get('handler', 'class')
            if handler_class_args is None:
                handler_class_args = [x.strip() for x in self.cnf.get('handler', 'class_args').split(',')]
            if handler_module is None:
                handler_module = self.cnf.get('handler', 'module')
            if end_request is None:
                end_request = self.cnf.get('handler', 'end_request')
            if split_request is None:
                end_request = self.cnf.get('handler', 'end_request')
            if handle_request is None:
                handle_request = self.cnf.get('handler', 'handle_request')
        ## set the remaining defaults not specified by conf
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
            handler_class_name = handler_class
            if handler_module is not None and hasattr(handler_module, handler_class_name) and inspect.isclass(getattr(handler_module, handler_class_name)):
                handler_class = getattr(handler_module, handler_class_name)
            elif self._globals.has_key(handler_class_name) and inspect.isclass(eval(handler_class_name)):
                handler_class = eval(handler_class_name)
            else:
                raise ValueError('handler_class is not the name of a valid class. It is: {}'.format(handler_class_name))
        elif inspect.isclass(handler_class):
            if handler_class_name in (None, ''):
                handler_class_name = handler_class.__name__
        else:
            raise TypeError('handler_class is not a valid class. It is: {} (type {})'.format(handler_class, type(handler_class)))
        if handle_request in (None, ''):
            handle_request = 'handle_request'
        if end_request in (None, ''):
            end_request = 'end_request'
        if split_request in (None, ''):
            split_request = 'split_request'
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
        if isinstance(end_request, basestring):
            end_request_name = end_request
            if self.handler and hasattr(self.handler, end_request_name) and inspect.method(getattr(self.handler, end_request_name)):
                end_request = getattr(self.handler, end_request_name)
            elif self._globals.has_key(end_request_name) and inspect.isroutine(self._globals[end_request_name]):
                end_request = self._globals[end_request_name]
            elif end_request == 'end_request':
                def end_request(request):
                    return('\n' in request.decode('utf8'))
            else:
                raise ValueError('end_request is not the name of a valid method or function. It is: {}'.format(end_request_name))
        elif inspect.isroutine(end_request):
            if end_request_name in (None, ''):
                end_request_name = end_request.__name__
        else:
            raise TypeError('end_request is not a valid function or method. It is: {} (type {})'.format(end_request, type(end_request)))
        if isinstance(split_request, basestring):
            split_request_name = split_request
            if self.handler and hasattr(self.handler, split_request_name) and inspect.method(getattr(self.handler, split_request_name)):
                split_request = getattr(self.handler, split_request_name)
            elif self._globals.has_key(split_request_name) and inspect.isroutine(self._globals[split_request_name]):
                split_request = self._globals[split_request_name]
            elif split_request_name == 'split_request':
                def split_request(request):
                    _req = request.decode('utf8')
                    _splitpoint = _req.find('\n') + 1
                    return(_req[:_splitpoint], _req[_splitpoint:])
            else:
                raise ValueError('split_request is not the name of a valid method or function. It is: {}'.format(split_request_name))
        elif inspect.isroutine(split_request):
            if split_request_name in (None, ''):
                split_request_name = split_request.__name__
        else:
            raise TypeError('split_request is not a valid function or method. It is: {} (type {})'.format(split_request, type(split_request)))
        if isinstance(handle_request, basestring):
            handle_request_name = handle_request
            if self.handler and hasattr(self.handler, handle_request_name) and inspect.method(getattr(self.handler, handle_request_name)):
                handle_request = getattr(self.handler, handle_request_name)
            elif self._globals.has_key(handle_request_name) and inspect.isroutine(self._globals[handle_request_name]):
                handle_request = self._globals[handle_request_name]
            elif handle_request_name == 'handle_request':
                def handle_request(request):
                    return(request.encode('utf8'), False)
            else:
                raise ValueError('handle_request is not the name of a valid method or function. It is: {}'.format(handle_request_name))
        elif inspect.isroutine(handle_request):
            if handle_request_name in (None, ''):
                handle_request_name = handle_request.__name__
        else:
            raise TypeError('handle_request is not a valid function or method. It is: {} (type {})'.format(handle_request, type(handle_request)))
        self.end_request_name = end_request_name
        self.split_request_name = split_request_name
        self.handle_request_name = handle_request_name
        self.end_request = end_request
        self.split_request = split_request
        self.handle_request = handle_request

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
                    if fileno == sock_fileno:
                        ## accept new connection (only once if requested)
                        try:
                            while not finished_accepting:
                                connection, address = sock.accept()
                                connection.setblocking(0)
                                connection_fileno = connection.fileno()
                                epoll.register(connection_fileno, select.EPOLLIN | select.EPOLLET)
                                connections[connection_fileno] = connection
                                requests[connection_fileno] = b''
                                responses[connection_fileno] = response
                                keepalive_flags[connection_fileno] = False
                                if one_req:
                                    finished_accepting = True
                        except socket.error:
                            pass
                    elif event & select.EPOLLIN:
                        ## read data
                        try:
                            requests[fileno] += connections[fileno].recv(self.recv_size)
                        except socket.error, e:
                            if e.args[0] != errno.EWOULDBLOCK:
                                raise
                        if self.end_request(requests[fileno]):
                            processing_request, requests[fileno] = self.split_request(requests[fileno])
                            ##TODO_BEGIN: dispatch the following using threads, procs, pp, etc...
                            responses[fileno], keepalive_flags[fileno] = self.handle_request(processing_request)
                            if self.verbose:
                                log('-' * 40, 'request: ' + processing_request, 'leftover-requests: ' + unicode(requests[fileno]))
                            ##TODO_END
                            epoll.modify(fileno, select.EPOLLOUT | select.EPOLLET)
                    elif event & select.EPOLLOUT:
                        ## write data
                        try:
                            while len(responses[fileno]) > 0:
                                byteswritten = connections[fileno].send(responses[fileno])
                                responses[fileno] = responses[fileno][byteswritten:]
                        except socket.error:
                            pass
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
    # LF end-of-lines, listening on all interfaces, port 8080, IPv4 & IPv6
    # with no keepalive or logging to console) in a loop until interrupted (by
    # keyboard or signal).
    server = Gaidaros()
    server.serve()
