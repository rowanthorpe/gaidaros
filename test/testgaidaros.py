#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import with_statement
import socket as sock, ssl, multiprocessing as mp, time, subprocess as sp, tempfile as tf, re
from gaidaros import Gaidaros

def tests():
    def _do_single(*args, **kwargs):
        srv = Gaidaros(*args, **kwargs)
        srv.handle()

    def _do_multiple(*args, **kwargs):
        kwargs.update({'handle_request': lambda x: (x, True)})
        srv = Gaidaros(*args, **kwargs)
        srv.serve()

    _patt = re.compile(r'@HostName@')
    hostname ='localhost'
    with tf.NamedTemporaryFile(suffix='.pem',prefix='gaidaros.') as tempcert:
        with tf.NamedTemporaryFile(suffix='.cnf',prefix='gaidaros.') as tempconf:
            with open('/usr/share/ssl-cert/ssleay.cnf', 'r') as conftemplate:
                for _line in conftemplate.readlines():
                    tempconf.write(_patt.sub('"' + hostname + '"', _line))
                tempconf.flush()
                sp.check_call(['openssl', 'req', '-config', tempconf.name, '-new', '-x509', '-days', '1',
                               '-nodes', '-out', tempcert.name, '-keyout', tempcert.name])
                sp.check_call(['chmod', '644', tempcert.name]) #throwaway cert,no privacy-concern
        _version = (sock.AF_INET, sock.AF_INET6)
        _type = ('single', 'multiple')
        _security = ('plain', 'ssl')
        _sslversion = (ssl.PROTOCOL_TLSv1,)
        _role = ('server', 'client')

        for _v in _version:
            for _t in _type:
                for _s in _security:
                    for _sv in _sslversion:
                        for _r in _role:
                            if _r == 'server':
                                _srv_kwargs = {'port': 4000}
                                if _s == 'ssl':
                                    _srv_kwargs.update(
                                        {'use_ssl': True, 'ssl_certfile': tempcert.name, 'ssl_version': _sv})
                                if _t == 'single':
                                    _target=_do_single
                                else:
                                    _target=_do_multiple
                                _srvsock = mp.Process(target=_target, kwargs=_srv_kwargs)
                                _srvsock.daemon = True
                                _srvsock.start()
                                time.sleep(1)
                            else:
                                _clientsock = sock.socket(_v, sock.SOCK_STREAM)
                                _clientsock.connect((hostname, 4000))
                                _clientsock.setsockopt(sock.SOL_SOCKET, sock.SO_REUSEADDR, 1)
                                if _s == 'ssl':
                                    _clientsock = ssl.wrap_socket(_clientsock, cert_reqs=ssl.CERT_NONE, ssl_version=_sv)
                                if _t == 'single':
                                    _reps = 1
                                else:
                                    _reps = 1024
                                _response = ''
                                for _count in xrange(_reps):
                                    _clientsock.sendall('abc-αβγ-123\n')
                                    _response += _clientsock.recv(1024)
                                _clientsock.close()
                                _srvsock.terminate()
                                assert _response == 'abc-αβγ-123\n' * _reps
