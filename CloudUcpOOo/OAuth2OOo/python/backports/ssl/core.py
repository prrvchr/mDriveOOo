# -*- coding: utf-8 -*-
"""
The Python 3.4 standard `ssl` module API implemented on top of pyOpenSSL
"""
from __future__ import absolute_import
from __future__ import print_function

try:
    from StringIO import StringIO as BytesIO
except ImportError:
    from io import BytesIO
import errno
try:
    import select
except ImportError:
    select = None
import re
import socket
import time

import six
from six import b

try:
    from .subject_alt_name import get_subject_alt_name
except ImportError:
    get_subject_alt_name = None

try:
    from OpenSSL import crypto
    from OpenSSL import SSL as ossl
    print("OpenSSL import ****************")
except ImportError:
    print("OpenSSL import error ************")
    crypto = None
    ossl = None

__target__ = 'ssl'

__implements__ = ['SSLError', 'CertificateError', 'match_hostname', 'SSLSocket',
                  'SSLContext', 'wrap_socket', '_fileobject']

_OPENSSL_ATTRS = dict(
    OP_NO_COMPRESSION='OP_NO_COMPRESSION',
    PROTOCOL_SSLv23='SSLv23_METHOD',
    PROTOCOL_SSLv3='SSLv3_METHOD',
    PROTOCOL_TLSv1='TLSv1_METHOD',
    PROTOCOL_TLSv1_1='TLSv1_1_METHOD',
    PROTOCOL_TLSv1_2='TLSv1_2_METHOD',
)

# TODO maybe shrink __implements__ if pyOpenSSL unavailable?
if ossl is not None:
    CERT_NONE = ossl.VERIFY_NONE
    CERT_REQUIRED = ossl.VERIFY_PEER | ossl.VERIFY_FAIL_IF_NO_PEER_CERT

    for external, internal in _OPENSSL_ATTRS.items():
        value = getattr(ossl, internal, None)
        if value:
            locals()[external] = value
            __implements__.append(external)

    OP_ALL = 0
    for bit in [31] + list(range(10)): # TODO figure out the names of these other flags
        OP_ALL |= 1 << bit

HAS_NPN = False # TODO

# TODO missing some attributes
class SSLError(OSError):
    pass

class SSLSysCallError(SSLError):
    pass

class SSLZeroReturnError(SSLError):
    pass

class SSLWantReadError(SSLError):
    pass

class SSLWantWriteError(SSLError):
    pass

class SSLSyscallError(SSLError):
    pass

class SSLEOFError(SSLError):
    pass

class CertificateError(ValueError):
    pass

# lifted from the Python 3.4 stdlib
def _dnsname_match(dn, hostname, max_wildcards=1):
    """
    Matching according to RFC 6125, section 6.4.3.

    See http://tools.ietf.org/html/rfc6125#section-6.4.3
    """
    pats = []
    if not dn:
        return False

    parts = dn.split(r'.')
    leftmost = parts[0]
    remainder = parts[1:]

    wildcards = leftmost.count('*')
    if wildcards > max_wildcards:
        # Issue #17980: avoid denials of service by refusing more
        # than one wildcard per fragment.  A survery of established
        # policy among SSL implementations showed it to be a
        # reasonable choice.
        raise CertificateError(
            "too many wildcards in certificate DNS name: " + repr(dn))

    # speed up common case w/o wildcards
    if not wildcards:
        return dn.lower() == hostname.lower()

    # RFC 6125, section 6.4.3, subitem 1.
    # The client SHOULD NOT attempt to match a presented identifier in which
    # the wildcard character comprises a label other than the left-most label.
    if leftmost == '*':
        # When '*' is a fragment by itself, it matches a non-empty dotless
        # fragment.
        pats.append('[^.]+')
    elif leftmost.startswith('xn--') or hostname.startswith('xn--'):
        # RFC 6125, section 6.4.3, subitem 3.
        # The client SHOULD NOT attempt to match a presented identifier
        # where the wildcard character is embedded within an A-label or
        # U-label of an internationalized domain name.
        pats.append(re.escape(leftmost))
    else:
        # Otherwise, '*' matches any dotless string, e.g. www*
        pats.append(re.escape(leftmost).replace(r'\*', '[^.]*'))

    # add the remaining fragments, ignore any wildcards
    for frag in remainder:
        pats.append(re.escape(frag))

    pat = re.compile(r'\A' + r'\.'.join(pats) + r'\Z', re.IGNORECASE)
    return pat.match(hostname)


# lifted from the Python 3.4 stdlib
def match_hostname(cert, hostname):
    """
    Verify that ``cert`` (in decoded format as returned by
    ``SSLSocket.getpeercert())`` matches the ``hostname``.  RFC 2818 and RFC
    6125 rules are followed, but IP addresses are not accepted for ``hostname``.

    ``CertificateError`` is raised on failure. On success, the function returns
    nothing.
    """
    if not cert:
        raise ValueError("empty or no certificate, match_hostname needs a "
                         "SSL socket or SSL context with either "
                         "CERT_OPTIONAL or CERT_REQUIRED")
    dnsnames = []
    san = cert.get('subjectAltName', ())
    for key, value in san:
        if key == 'DNS':
            if _dnsname_match(value, hostname):
                return
            dnsnames.append(value)
    if not dnsnames:
        # The subject is only checked when there is no dNSName entry
        # in subjectAltName
        for sub in cert.get('subject', ()):
            for key, value in sub:
                # XXX according to RFC 2818, the most specific Common Name
                # must be used.
                if key == 'commonName':
                    if _dnsname_match(value, hostname):
                        return
                    dnsnames.append(value)
    if len(dnsnames) > 1:
        raise CertificateError("hostname %r "
            "doesn't match either of %s"
            % (hostname, ', '.join(map(repr, dnsnames))))
    elif len(dnsnames) == 1:
        raise CertificateError("hostname %r "
            "doesn't match %r"
            % (hostname, dnsnames[0]))
    else:
        raise CertificateError("no appropriate commonName or "
            "subjectAltName fields were found")


def _proxy(method):
    return lambda self, *args, **kwargs: getattr(self._conn, method)(*args, **kwargs)


# Lovingly stolen from CherryPy (http://svn.cherrypy.org/tags/cherrypy-3.2.1/cherrypy/wsgiserver/ssl_pyopenssl.py).
SSL_RETRY = .01
def _safe_ssl_call(suppress_ragged_eofs, sock, call, *args, **kwargs):
    """Wrap the given call with SSL error-trapping."""
    start = time.time()
    while True:
        try:
            return getattr(sock, call)(*args, **kwargs)

        except (ossl.WantReadError, ossl.WantWriteError):
            if select is None:
                if time.time() - start > sock.gettimeout():
                    raise socket.timeout()
                time.sleep(SSL_RETRY)
            elif not select.select([sock], [], [], sock.gettimeout())[0]:
                raise socket.timeout()

        except ossl.SysCallError as e:
            if suppress_ragged_eofs and e.args[0] == (-1, 'Unexpected EOF'):
                return b''
            elif e.args[0] == 0:
                raise SSLEOFError(*e.args)
            raise SSLSysCallError(*e.args)

        except ossl.ZeroReturnError as e:
            raise SSLZeroReturnError(*e.args)

        except ossl.Error as e:
            raise SSLError(*e.args)


class SSLSocket():
    pass
'''    def __init__(self, conn, server_side, do_handshake_on_connect,
                 suppress_ragged_eofs, server_hostname, check_hostname):
        self._conn = conn
        self._do_handshake_on_connect = do_handshake_on_connect
        self._suppress_ragged_eofs = suppress_ragged_eofs
        self._check_hostname = check_hostname

        if server_side:
            self._conn.set_accept_state()
        else:
            if server_hostname:
                self._conn.set_tlsext_host_name(server_hostname.encode('utf-8'))
            self._conn.set_connect_state() # FIXME does this override do_handshake_on_connect=False?

        if self.connected and self._do_handshake_on_connect:
            self.do_handshake()

    @property
    def connected(self):
        try:
            self._conn.getpeername()
        except socket.error as e:
            if e.errno != errno.ENOTCONN:
                # It's an exception other than the one we expected if we're not
                # connected.
                raise
            return False
        return True

    def connect(self, address):
        self._conn.connect(address)
        if self._do_handshake_on_connect:
            self.do_handshake()

    def do_handshake(self):
        _safe_ssl_call(False, self._conn, 'do_handshake')
        if self._check_hostname:
            match_hostname(self.getpeercert(), self._conn.get_servername().decode('utf-8'))

    def recv(self, bufsize, flags=None):
        return _safe_ssl_call(self._suppress_ragged_eofs, self._conn, 'recv',
                               bufsize, flags)

    def recv_into(self, buffer, bufsize=None, flags=None):
        # A temporary recv_into implementation. Should be replaced when
        # PyOpenSSL has merged pyca/pyopenssl#121.
        if bufsize is None:
            bufsize = len(buffer)

        data = self.recv(bufsize, flags)
        data_len = len(data)
        buffer[0:data_len] = data
        return data_len

    def send(self, data, flags=None):
        return _safe_ssl_call(False, self._conn, 'send', data, flags)

    def sendall(self, data, flags=None):
        return _safe_ssl_call(False, self._conn, 'sendall', data, flags)

    def selected_npn_protocol(self):
        raise NotImplementedError()

    def getpeercert(self, binary_form=False):
        def resolve_alias(alias):
            return dict(
                C='countryName',
                ST='stateOrProvinceName',
                L='localityName',
                O='organizationName',
                OU='organizationalUnitName',
                CN='commonName',
            ).get(alias, alias)

        def to_components(name):
            # TODO Verify that these are actually *supposed* to all be single-element
            # tuples, and that's not just a quirk of the examples I've seen.
            return tuple([((resolve_alias(name.decode('utf-8')), value.decode('utf-8')),) for name, value in name.get_components()])

        cert = self._conn.get_peer_certificate()

        if binary_form:
            return crypto.dump_certificate(crypto.FILETYPE_ASN1, cert)

        # The standard getpeercert() takes the nice X509 object tree returned
        # by OpenSSL and turns it into a dict according to some format it seems
        # to have made up on the spot. Here, we do our best to emulate that.
        result = dict(
            issuer=to_components(cert.get_issuer()),
            subject=to_components(cert.get_subject()),
            version=cert.get_subject(),
            serialNumber=cert.get_serial_number(),
            notBefore=cert.get_notBefore(),
            notAfter=cert.get_notAfter(),
        )
        if get_subject_alt_name is not None:
            result.update(
                subjectAltName=[('DNS', value) for value in get_subject_alt_name(cert)],
            )
        return result

    # FIXME support other arguments - not included in the signature to make
    # calls that expect them fail fast - use codecs.open()?
    def makefile(self, mode='r', buffering=None):
        if buffering is None:
            buffering = -1
        return _fileobject(self._conn, mode, buffering)

    @property
    def family(self):
        return self._conn._socket.family

    # a dash of magic to reduce boilerplate
    for method in ['accept', 'bind', 'close', 'fileno', 'getsockname', 'listen',
                   'setblocking', 'settimeout', 'gettimeout', 'read']:
        locals()[method] = _proxy(method)
'''

# lifted from socket.py in Python 2.7.6, with modifications taken from urllib3
class _fileobject(object):
    """Faux file object attached to a socket object."""

    default_bufsize = 8192
    name = "<socket>"

    __slots__ = ["mode", "bufsize", "softspace",
                 # "closed" is a property, see below
                 "_sock", "_rbufsize", "_wbufsize", "_rbuf", "_wbuf", "_wbuf_len",
                 "_close"]

    def __init__(self, sock, mode='rb', bufsize=-1, close=False):
        self._sock = sock
        self.mode = mode # Not actually used in this version
        if bufsize < 0:
            bufsize = self.default_bufsize
        self.bufsize = bufsize
        self.softspace = False
        # _rbufsize is the suggested recv buffer size.  It is *strictly*
        # obeyed within readline() for recv calls.  If it is larger than
        # default_bufsize it will be used for recv calls within read().
        if bufsize == 0:
            self._rbufsize = 1
        elif bufsize == 1:
            self._rbufsize = self.default_bufsize
        else:
            self._rbufsize = bufsize
        self._wbufsize = bufsize
        # We use BytesIO for the read buffer to avoid holding a list
        # of variously sized string objects which have been known to
        # fragment the heap due to how they are malloc()ed and often
        # realloc()ed down much smaller than their original allocation.
        self._rbuf = BytesIO()
        self._wbuf = [] # A list of strings
        self._wbuf_len = 0
        self._close = close

    def _getclosed(self):
        return self._sock is None
    closed = property(_getclosed, doc="True if the file is closed")

    def close(self):
        try:
            if self._sock:
                self.flush()
        finally:
            if self._close:
                self._sock.close()
            self._sock = None

    def __del__(self):
        try:
            self.close()
        except:
            # close() may fail if __init__ didn't complete
            pass

    def flush(self):
        if self._wbuf:
            data = b('').join(self._wbuf)
            self._wbuf = []
            self._wbuf_len = 0
            buffer_size = max(self._rbufsize, self.default_bufsize)
            data_size = len(data)
            write_offset = 0
            view = memoryview(data)
            try:
                while write_offset < data_size:
                    self._sock.sendall(view[write_offset:write_offset+buffer_size])
                    write_offset += buffer_size
            finally:
                if write_offset < data_size:
                    remainder = data[write_offset:]
                    del view, data  # explicit free
                    self._wbuf.append(remainder)
                    self._wbuf_len = len(remainder)

    def fileno(self):
        return self._sock.fileno()

    def write(self, data):
        data = six.binary_type(data) # XXX Should really reject non-string non-buffers
        if not data:
            return
        self._wbuf.append(data)
        self._wbuf_len += len(data)
        if (self._wbufsize == 0 or
            (self._wbufsize == 1 and b('\n') in data) or
            (self._wbufsize > 1 and self._wbuf_len >= self._wbufsize)):
            self.flush()

    def writelines(self, list):
        # XXX We could do better here for very long lists
        # XXX Should really reject non-string non-buffers
        lines = filter(None, map(six.binary_type, list))
        self._wbuf_len += sum(map(len, lines))
        self._wbuf.extend(lines)
        if (self._wbufsize <= 1 or
            self._wbuf_len >= self._wbufsize):
            self.flush()

    def read(self, size=-1):
        # Use max, disallow tiny reads in a loop as they are very inefficient.
        # We never leave read() with any leftover data from a new recv() call
        # in our internal buffer.
        rbufsize = max(self._rbufsize, self.default_bufsize)
        # Our use of BytesIO rather than lists of string objects returned by
        # recv() minimizes memory usage and fragmentation that occurs when
        # rbufsize is large compared to the typical return value of recv().
        buf = self._rbuf
        buf.seek(0, 2)  # seek end
        if size < 0:
            # Read until EOF
            self._rbuf = BytesIO()  # reset _rbuf.  we consume it via buf.
            data = _safe_ssl_call(False, self._sock, 'recv', rbufsize)
            buf.write(data)
            return buf.getvalue()
        else:
            # Read until size bytes or EOF seen, whichever comes first
            buf_len = buf.tell()
            if buf_len >= size:
                # Already have size bytes in our buffer?  Extract and return.
                buf.seek(0)
                rv = buf.read(size)
                self._rbuf = BytesIO()
                self._rbuf.write(buf.read())
                return rv

            self._rbuf = BytesIO()  # reset _rbuf.  we consume it via buf.
            while True:
                left = size - buf_len
                # recv() will malloc the amount of memory given as its
                # parameter even though it often returns much less data
                # than that.  The returned data string is short lived
                # as we copy it into a BytesIO and free it.  This avoids
                # fragmentation issues on many platforms.

                # Note: never pass a large value as the maximum size
                # to pyOpenSSL's recv because it will always allocate
                # a buffer that size but then return a much smaller
                # number buffer (typically 1024 bytes). This causes
                # severe performance problems when `size` is large.
                maxbufsize = min(rbufsize, left)
                data = _safe_ssl_call(False, self._sock, 'recv', maxbufsize)
                if not data:
                    break
                n = len(data)
                if n == size and not buf_len:
                    # Shortcut.  Avoid buffer data copies when:
                    # - We have no data in our buffer.
                    # AND
                    # - Our call to recv returned exactly the
                    #   number of bytes we were asked to read.
                    return data
                if n == left:
                    buf.write(data)
                    del data  # explicit free
                    break
                assert n <= left, "recv(%d) returned %d bytes" % (left, n)
                buf.write(data)
                buf_len += n
                del data  # explicit free
                #assert buf_len == buf.tell()
            return buf.getvalue()

    def readline(self, size=-1):
        buf = self._rbuf
        buf.seek(0, 2)  # seek end
        if buf.tell() > 0:
            # check if we already have it in our buffer
            buf.seek(0)
            bline = buf.readline(size)
            if bline.endswith(b('\n')) or len(bline) == size:
                self._rbuf = BytesIO()
                self._rbuf.write(buf.read())
                return bline
            del bline
        if size < 0:
            # Read until \n or EOF, whichever comes first
            if self._rbufsize <= 1:
                # Speed up unbuffered case
                buf.seek(0)
                buffers = [buf.read()]
                self._rbuf = BytesIO()  # reset _rbuf.  we consume it via buf.
                data = None
                while data != b('\n'):
                    data = _safe_ssl_call(False, self._sock, 'recv', 1)
                    if not data:
                        break
                    buffers.append(data)
                return b('').join(buffers)

            buf.seek(0, 2)  # seek end
            self._rbuf = BytesIO()  # reset _rbuf.  we consume it via buf.
            while True:
                data = _safe_ssl_call(False, self._sock, 'recv', self._rbufsize)
                if not data:
                    break
                nl = data.find(b('\n'))
                if nl >= 0:
                    nl += 1
                    buf.write(data[:nl])
                    self._rbuf.write(data[nl:])
                    del data
                    break
                buf.write(data)
            return buf.getvalue()
        else:
            # Read until size bytes or \n or EOF seen, whichever comes first
            buf.seek(0, 2)  # seek end
            buf_len = buf.tell()
            if buf_len >= size:
                buf.seek(0)
                rv = buf.read(size)
                self._rbuf = BytesIO()
                self._rbuf.write(buf.read())
                return rv
            self._rbuf = BytesIO()  # reset _rbuf.  we consume it via buf.
            while True:
                data = _safe_ssl_call(False, self._sock, 'recv', self._rbufsize)
                if not data:
                    break
                left = size - buf_len
                # did we just receive a newline?
                nl = data.find(b('\n'), 0, left)
                if nl >= 0:
                    nl += 1
                    # save the excess data to _rbuf
                    self._rbuf.write(data[nl:])
                    if buf_len:
                        buf.write(data[:nl])
                        break
                    else:
                        # Shortcut.  Avoid data copy through buf when returning
                        # a substring of our first recv().
                        return data[:nl]
                n = len(data)
                if n == size and not buf_len:
                    # Shortcut.  Avoid data copy through buf when
                    # returning exactly all of our first recv().
                    return data
                if n >= left:
                    buf.write(data[:left])
                    self._rbuf.write(data[left:])
                    break
                buf.write(data)
                buf_len += n
                #assert buf_len == buf.tell()
            return buf.getvalue()

    def readlines(self, sizehint=0):
        total = 0
        list = []
        while True:
            line = self.readline()
            if not line:
                break
            list.append(line)
            total += len(line)
            if sizehint and total >= sizehint:
                break
        return list

    # Iterator protocols

    def __iter__(self):
        return self

    def next(self):
        line = self.readline()
        if not line:
            raise StopIteration
        return line


class SSLContext(object):
    def __init__(self, protocol):
        self.protocol = protocol
        self._ctx = ossl.Context(protocol)
        self.options = OP_ALL
        self.check_hostname = False
        self.set_default_verify_paths()

    @property
    def options(self):
        return self._options

    @options.setter
    def options(self, value):
        self._options = value
        self._ctx.set_options(value)

    @property
    def verify_mode(self):
        return self._ctx.get_verify_mode()

    @verify_mode.setter
    def verify_mode(self, value):
        self._ctx.set_verify(value, lambda conn, cert, errnum, errdepth, ok: ok)

    def set_default_verify_paths(self):
        self._ctx.set_default_verify_paths()

    def load_verify_locations(self, cafile=None, capath=None, cadata=None):
        # TODO factor out common code
        if cafile is not None:
            cafile = cafile.encode('utf-8')
        if capath is not None:
            capath = capath.encode('utf-8')
        self._ctx.load_verify_locations(cafile, capath)
        if cadata is not None:
            self._ctx.load_verify_locations(BytesIO(cadata))

    def load_cert_chain(self, certfile, keyfile=None, password=None):
        self._ctx.use_certificate_file(certfile)
        if password is not None:
            self._ctx.set_password_cb(lambda max_length, prompt_twice, userdata: password)
        self._ctx.use_privatekey_file(keyfile or certfile)

    def set_ciphers(self, cipher_list):
        return self._ctx.set_cipher_list(cipher_list)

    def set_npn_protocols(self, protocols):
        raise NotImplementedError() # TODO

    def wrap_socket(self, sock, server_side=False, do_handshake_on_connect=True,
                    suppress_ragged_eofs=True, server_hostname=None):
        conn = ossl.Connection(self._ctx, sock)
        return SSLSocket(conn, server_side, do_handshake_on_connect,
                         suppress_ragged_eofs, server_hostname,
                         # TODO what if this is changed after the fact?
                         self.check_hostname)


def wrap_socket(sock, keyfile=None, certfile=None, server_side=False,
                cert_reqs=None, ssl_version=None, ca_certs=None,
                do_handshake_on_connect=True, suppress_ragged_eofs=True,
                ciphers=None):
    # TODO the stdlib docs say the SSLContext isn't constructed until connect()
    # is called on the socket, if it's not already connected. Check if we need
    # to emulate that behavior as well, or if it's just an optimization.
    ctx = SSLContext(ssl_version if ssl_version is not None else PROTOCOL_SSLv23)
    ctx.verify_mode = cert_reqs if cert_reqs is not None else CERT_NONE
    if certfile is not None:
        ctx.load_cert_chain(certfile, keyfile)
    if ca_certs is not None:
        ctx.load_verify_locations(ca_certs)
    if ciphers is not None:
        ctx.set_ciphers(ciphers)
    return ctx.wrap_socket(sock, server_side=server_side,
                           do_handshake_on_connect=do_handshake_on_connect,
                           suppress_ragged_eofs=suppress_ragged_eofs)


if ossl is None:
    for impl in ['SSLSocket', 'SSLContext', 'wrap_socket', '_fileobject']:
        del locals()[impl]
