#/usr/bin/env python
# encoding: utf-8

"""
Async server micro-framework for control freaks
"""
__version__ = '0.2.5'
__all__ = ['Gaidaros', 'usage', 'warn', 'die', 'log']
import sys, os, re
import __main__ as main

def __print_nl(data, ostream = sys.stdout):
    ostream.write(data + ['\n', ''][data[-1:] == '\n'])

def usage(ostream = sys.stderr): pass

def warn(warning, ostream = sys.stderr, with_usage = False, usage_func = None):
    if with_usage:
        if hasattr(usage_func, '__call__'): usage_func(ostream = ostream)
        else: usage(ostream = ostream)
        ostream.write('\n')
    __print_nl(os.path.basename(main.__file__) + ': ' + warning, ostream = ostream)

def die(warning = None, stack = None, with_usage = False, usage_func = None):
    if warning: warn(warning, with_usage = with_usage, usage_func = usage_func)
    if stack:
        sys.stderr.write('\n')
        raise
    else: sys.exit(1)

def log(*args):
    for message in args: warn(message, ostream = sys.stderr)

class Gaidaros(object):

    def __init__( self, verbose = None, conf = None, host = None, port = None, ip_version = None, \
                  backlog = None, poll_timeout = None, recv_size = None, \
                  handler_class = None, handler_class_args = None, handler_module = None, \
                  handle_request = None, end_request = None, split_request = None):
        import ConfigParser
        if conf:
            ## source conf for remaining settings
            self.cnf = ConfigParser.ConfigParser()
            self.cnf.MAX_INTERPOLATION_DEPTH = 3
            cnf_fp = open(os.path.expanduser(conf))
            self.cnf.readfp(cnf_fp)
            cnf_fp.close()
            if verbose == None: verbose = self.cnf.getbool('global', 'verbose')
            if host == None: host = self.cnf.get('global', 'host')
            if port == None: port = self.cnf.getint('global', 'port')
            if ip_version == None: ip_version = self.cnf.getint('global', 'ip_version')
            if backlog == None: backlog = self.cnf.getint('global', 'backlog')
            if poll_timeout == None: poll_timeout = self.cnf.getint('global', 'poll_timeout')
            if recv_size == None: recv_size = self.cnf.getint('global', 'recv_size')
            if handler_class == None: handler_class = self.cnf.get('handler', 'class')
            if handler_class_args == None: handler_class_args = map(lambda x: x.strip(), self.cnf.get('handler', 'class_args').split(','))
            if handler_module == None: handler_module = self.cnf.get('handler', 'module')
            if handle_request == None: handle_request = self.cnf.get('handler', 'handle_request')
            if end_request == None: end_request = self.cnf.get('handler', 'end_request')
            if split_request == None: end_request = self.cnf.get('handler', 'end_request')
        ## set remaining defaults not specified by conf
        if verbose == None: verbose = False
        if host == None: host = '::'
        if port == None: port = 8080
        if ip_version == None: ip_version = 0
        if backlog == None: backlog = 50
        if poll_timeout == None: poll_timeout = 1
        if recv_size == None: recv_size = 1024
        if handler_class:
            if not isinstance(handler_class, type):
                if handler_module:
                    if not isinstance(handler_module, type):
                        import importlib
                        handler_module_obj = importlib.import_module(handler_module)
                    if not hasattr(handler_module_obj, handler_class):
                        handler_module_obj = importlib.import_module(handler_module + '.' + handler_module)
                    handler_class = getattr(handler_module_obj, handler_class)
                else: handler_class = globals()[handler_class]
            if handler_class_args == None: handler_class_args = []
        else:
            class handler_class(object): pass
            handler_class_args = []
            handler_module = None
        if handle_request in [ None, '' ]: handle_request = 'handle_request'
        if end_request in [ None, '' ]: end_request = 'end_request'
        if split_request in [ None, '' ]: split_request = 'split_request'
        ## set long-lived vars including handler instance
        self.verbose = verbose
        self.host = host
        self.port = port
        self.ip_version = ip_version
        self.backlog = backlog
        self.poll_timeout = poll_timeout
        self.recv_size = recv_size
        self.handler = handler_class(*handler_class_args)

        if isinstance(handle_request, basestring):
            if handle_request[:8] == 'compile:': exec('handle_request = ' + handle_request[8:] + '\n')
            elif hasattr(self.handler, handle_request): handle_request = getattr(self.handler, handle_request)
            else:
                def handle_request(request): return([request, 0])
        if hasattr(handle_request, '__call__'): self.handle_request = handle_request
        else:
            self.__handle_request = handle_request
            self.handle_request = eval(self.__handle_request)
        if isinstance(end_request, basestring):
            if end_request[:8] == 'compile:': exec('end_request = ' + end_request[8:] + '\n')
            elif hasattr(self.handler, end_request): end_request = getattr(self.handler, end_request)
            else:
                def end_request(request): return(b'\n' in request)
        if hasattr(end_request, '__call__'): self.end_request = end_request
        else:
            self.__end_request = end_request
            self.end_request = eval(self.__end_request)
        if isinstance(split_request, basestring):
            if split_request[:8] == 'compile:': exec('split_request = ' + split_request[8:] + '\n')
            elif hasattr(self.handler, split_request): split_request = getattr(self.handler, split_request)
            else:
                def split_request(request): return(request[:request.find('\n') + 1], request[request.find('\n') + 1:])
        if hasattr(split_request, '__call__'): self.split_request = split_request
        else:
            self.__split_request = split_request
            self.split_request = eval(self.__split_request)

    def ioloop(self, one_req = False):
        import socket, select
        ## initial state
        finished_accepting = 0
        shutdown_wanted = 0
        response  = b''
        ## socket setup - ip version(s), host, port, backlog
        if self.ip_version == 4: sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        else: sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        if self.ip_version == 6: sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 1)
        else: sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((self.host, self.port))
        sock.listen(self.backlog)
        sock.setblocking(0)
        sock_fileno = sock.fileno()
        ## setup poller
        epoll = select.epoll()
        epoll.register(sock_fileno, select.EPOLLIN | select.EPOLLET)
        try:
            ## initialise connection states
            connections = {}; requests = {}; responses = {}; keepalive_flags = {}
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
                                if one_req: finished_accepting = 1
                        except socket.error: pass
                    elif event & select.EPOLLIN:
                        ## read data
                        try:
                            while 1:
                                requests[fileno] += connections[fileno].recv(self.recv_size)
                        except socket.error: pass
                        if self.end_request(requests[fileno]):
                            processing_request, requests[fileno] = self.split_request(requests[fileno])
                            ##TODO: begin - dispatch the following using threads, procs, pp, etc...
                            response_args = self.handle_request(processing_request)
                            if isinstance(response_args, basestring): responses[fileno] = response_args
                            else:
                                responses[fileno] = response_args.pop(0)
                                if response_args: keepalive_flags[fileno] = response_args.pop(0)
                            if self.verbose: log('-' * 40, 'request: ' + processing_request, 'leftover-requests: ' + requests[fileno])
                            ##TODO: end
                            epoll.modify(fileno, select.EPOLLOUT | select.EPOLLET)
                    elif event & select.EPOLLOUT:
                        ## write data
                        try:
                            while len(responses[fileno]) > 0:
                                byteswritten = connections[fileno].send(responses[fileno])
                                responses[fileno] = responses[fileno][byteswritten:]
                        except socket.error: pass
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
                                    shutdown_wanted = 1
                    elif event & select.EPOLLHUP:
                        ## finish connection
                        epoll.unregister(fileno)
                        connections[fileno].close()
                        del connections[fileno]
                        if one_req: shutdown_wanted = 1
        finally:
            ## close server
            epoll.unregister(sock_fileno)
            epoll.close()
            sock.close()

    def handle(self): self.ioloop(one_req = 1)

    def serve(self): self.ioloop()

if __name__ == '__main__':
    # If executed directly this file inputs and returns (echoes) a one-line request (on all interfaces, port 8080, IPv4 & IPv6) in a loop until interrupted (by keyboard or signal).
    server = Gaidaros(verbose = True)
    server.serve()
