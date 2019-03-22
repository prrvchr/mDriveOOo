#!
# -*- coding: utf_8 -*-

import uno
import unohelper

from com.sun.star.io import XOutputStream
from com.sun.star.io import XInputStream
from com.sun.star.io import IOException

from .drivetools import g_itemfields
from .drivetools import g_chunk
from .drivetools import g_length
from .drivetools import g_pages
from .drivetools import g_timeout
from .drivetools import g_upload
from .drivetools import g_url


class ChildGenerator():
    def __init__(self, session, id):
        print("onedrive.ChildGenerator.__init__()")
        self.session = session
        self.url = '%s/me/drive/items/%s/children' % (g_url, id)
        self.params = {'$select': g_itemfields}
        self.params['$top'] = g_pages
        print("onedrive.ChildGenerator.__init__()")
    def __iter__(self):
        self.rows, self.url = self._getChunk()
        return self
    def __next__(self):
        if self.rows:
            pass
        elif self.url:
            self.rows, self.url = self._getChunk()
        else:
            raise StopIteration
        return self.rows.pop(0)
    # for python v2.xx
    def next(self):
        return self.__next__()
    def _getChunk(self):
        rows, url = [], None
        with self.session.get(self.url, params=self.params, timeout=g_timeout) as r:
            print("onedrive.ChildGenerator(): %s" % r.json())
            if r.status_code == self.session.codes.ok:
                rows = r.json().get('value', [])
                url = r.json().get('@odata:nextLink', None)
        return rows, url


class InputStream(unohelper.Base, XInputStream):
    def __init__(self, session, id, size):
        self.session = session
        url = '%s/me/drive/items/%s/content' % (g_url, id)
        redirect = None
        self.chunks = lambda: iter(())
        self.buffers = b''
        with self.session.get(url, timeout=g_timeout, allow_redirects=False) as r:
            if r.status_code == self.session.codes.found:
                redirect = r.headers.get('Location', None)
        if redirect is not None:
            self.chunks = (s for c in Downloader(self.session, redirect, size) for s in c)
        print("onedrive.InputStream.__init__()")

    #XInputStream
    def readBytes(self, sequence, length):
        available = length - len(self.buffers)
        if available < 0:
            i = abs(available)
            sequence = uno.ByteSequence(self.buffers[:i])
            self.buffers = self.buffers[i:]
        else:
            sequence = uno.ByteSequence(self.buffers)
            self.buffers = b''
            while available > 0:
                chunk = next(self.chunks, b'')
                if not chunk:
                    break
                elif len(chunk) > available:
                    sequence += chunk[:available]
                    self.buffers = chunk[available:]
                    break
                sequence += chunk
                available = length - len(sequence)
        return len(sequence), sequence
    def readSomeBytes(self, sequence, length):
        print("onedrive.InputStream.readSomeBytes()")
        return self.readBytes(sequence, length)
    def skipBytes(self, length):
        # This method seem to never be called
        print("onedrive.InputStream.skipBytes()")
        pass
    def available(self):
        # This method seem to never be called
        print("onedrive.InputStream.available()")
        return g_chunk
    def closeInput(self):
        print("onedrive.InputStream.closeInput() 1: %s" % (self.session.headers, ))
        self.session.headers.pop('Range', None)
        self.session.close()
        print("onedrive.InputStream.closeInput() 2: %s" % (self.session.headers, ))


class Downloader():
    def __init__(self, session, url, size=0):
        self.session = session
        self.url = url
        self.size = size
        self.start = 0
        self.closed = False
        self.chunked = size > g_chunk
        # We don't need authentication, 'url' is an ephemeral link...
        self.auth = NoOAuth2()
        print("onedrive.Downloader.__init__()")
    def __iter__(self):
        return self
    def __next__(self):
        if self.closed:
            raise StopIteration
        end = min(self.start + g_chunk, self.size)
        if self.chunked:
            self.session.headers.update({'Range': 'bytes=%s-%s' % (self.start, end -1)})
        # We cannot use a 'Context Manager' here... iterator needs access to the response...
        r = self.session.get(self.url, timeout=g_timeout, stream=True, auth=self.auth)
        if (r.status_code == self.session.codes.ok or
            r.status_code == self.session.codes.partial_content):
            self.start = end
            self.closed = self.start == self.size
        else:
            # Without 'Context Manager', to release the connection back to the pool,
            # because we don't have consumed all the data, we need to close the response
            r.close()
            self.closed = True
            raise StopIteration
        return r.iter_content(chunk_size=g_length)
    # for python v2.xx
    def next(self):
        return self.__next__()


class OutputStream(unohelper.Base, XOutputStream):
    def __init__(self, session, url, size, update):
        self.session = session
        self.url = url
        self.size = size
        self.update = update
        self.buffers = []
        self.length = 0
        self.start = 0
        self.closed = False
        self.chunked = size > g_upload
        self.auth = NoOAuth2() if self.chunked else None
    # XOutputStream
    def writeBytes(self, sequence):
        if self.closed:
            raise IOException('OutputStream is closed...', self)
        self.buffers.append(sequence.value)
        self.length += len(sequence)
        if self._flushable() and not self._flush():
            raise IOException('Error Uploading file...', self)
        else:
            print("onedrive.OutputStream.writeBytes() Bufferize: %s - %s" % (self.start, self.length))
    def flush(self):
        print("onedrive.OutputStream.flush()")
        if self.closed:
            raise IOException('OutputStream is closed...', self)
        if self._flushable(True) and not self._flush():
            raise IOException('Error Uploading file...', self)
    def closeOutput(self):
        print("onedrive.OutputStream.closeOutput() 1")
        if not self.closed:
            self._close()
        print("onedrive.OutputStream.closeOutput() 2")
    def _flushable(self, last=False):
        if last:
            return self.length > 0
        elif self.chunked:
            return self.length >= g_chunk
        return False
    def _flush(self):
        print("onedrive.OutputStream._write() 1: %s" % (self.start, ))
        end = self.start + self.length -1
        if self.chunked:
            self.session.headers.update({'Content-Range': 'bytes %s-%s/%s' % (self.start, end, self.size)})
        print("onedrive.OutputStream._write() 2: %s" % (self.session.headers, ))
        with self.session.put(self.url, data=iter(self.buffers), auth=self.auth) as r:
            print("onedrive.OutputStream._write() 3: %s" % (r.request.headers, ))
            print("onedrive.OutputStream._write() 4: %s - %s" % (r.status_code, r.headers))
            print("onedrive.OutputStream._write() 5: %s" % (r.json(), ))
            if r.status_code == self.session.codes.ok:
                print("onedrive.OutputStream._write() 6")
                self.start = end
                self.buffers = []
                self.length = 0
                return True
            elif r.status_code == self.session.codes.created:
                print("onedrive.OutputStream._write() 7")
                self.start = end
                print("onedrive.OutputStream._write() 8")
                self.buffers = []
                self.length = 0
                id = r.json().get('id', None)
                print("onedrive.OutputStream._write() 9 %s" % id)
                self._updateItem(id)
                return True
            elif r.status_code == self.session.codes.accepted:
                #self.start = int(r.json().get('nextExpectedRanges').split('-')[0])
                self.start = end
                self.buffers = []
                self.length = 0
                return True
            else:
                print("onedrive.OutputStream._write() 10 %s" % r.text)
        return False
    def _close(self):
        print("onedrive.OutputStream._close() 1")
        self.flush()
        print("onedrive.OutputStream._close() 2: %s" % (self.session.headers, ))
        self.session.headers.pop('Content-Range', None)
        self.session.close()
        self.closed = True
        print("onedrive.OutputStream._close() 3: %s" % (self.session.headers, ))
    def _updateItem(self, id):
        if id is not None:
            self.update.setString(4, id)
            self.update.execute()
            result = self.update.getString(5)
            self.update.close()
            print("onedrive.OutputStream._updateItem(): %s" % result)


class NoOAuth2(object):
    def __eq__(self, other):
        return False

    def __ne__(self, other):
        return not self == other

    def __call__(self, request):
        print("onedrive.NoOAuth2.__call__()")
        return request
