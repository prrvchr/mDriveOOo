#!
# -*- coding: utf-8 -*-

import uno
import unohelper

from com.sun.star.io import XInputStream
from com.sun.star.io import XOutputStream
from com.sun.star.io import XStreamListener

from com.sun.star.io import IOException
from com.sun.star.container import NoSuchElementException

from com.sun.star.logging.LogLevel import INFO
from com.sun.star.logging.LogLevel import SEVERE

from com.sun.star.ucb.ConnectionMode import ONLINE
from com.sun.star.ucb.ConnectionMode import OFFLINE
from com.sun.star.connection import NoConnectException

from com.sun.star.auth import XRestUploader
from com.sun.star.auth import XRestEnumeration
from com.sun.star.auth import XRestRequest
from com.sun.star.auth.RestRequestTokenType import TOKEN_NONE
from com.sun.star.auth.RestRequestTokenType import TOKEN_URL
from com.sun.star.auth.RestRequestTokenType import TOKEN_REDIRECT
from com.sun.star.auth.RestRequestTokenType import TOKEN_QUERY
from com.sun.star.auth.RestRequestTokenType import TOKEN_JSON
from com.sun.star.auth.RestRequestTokenType import TOKEN_SYNC

from unolib import KeyMap
from unolib import NoOAuth2

from .logger import logMessage
from . import requests

import traceback
import sys
import json

# Request / OAuth2 configuration
g_auth = 'com.gmail.prrvchr.extensions.OAuth2OOo'


def getConnectionMode(ctx, host):
    return getSessionMode(ctx, host)

def getSessionMode(ctx, host, port=80):
    connector = ctx.ServiceManager.createInstance('com.sun.star.connection.Connector')
    try:
        connection = connector.connect('socket,host=%s,port=%s' % (host, port))
    except NoConnectException:
        mode = OFFLINE
    else:
        connection.close()
        mode = ONLINE
    return mode


class Iterator(unohelper.Base,
               XRestEnumeration):
    def __init__(self, session, timeout, parameter, parser=None):
        self.session = session
        self.timeout = timeout
        self.parameter = parameter
        self.parser = parser
        self.pagetoken = None
        self.synctoken = ''
        self.error = None
        self.row = 0
        self.page = 0
        self.next = None
        self.end = object()
        self.iterator = self._getIterator()

    @property
    def SyncToken(self):
        return self.synctoken
    @property
    def PageCount(self):
        return self.page
    @property
    def RowCount(self):
        return self.row

    # XRestEnumeration
    def hasMoreElements(self):
        self.next = next(self.iterator, self.end)
        return self.next is not self.end

    def nextElement(self):
        if self.next is not self.end:
            return self.next
        raise NoSuchElementException('no more elements exist', self)

    def _setParameter(self):
        token = self.parameter.Enumerator.Token.Type
        if token & TOKEN_URL:
            self.parameter.Url = self.parameter.Enumerator.Token.Value
        if token & TOKEN_QUERY:
            query = json.loads(self.parameter.Query)
            query.update({self.parameter.Enumerator.Token.Value: self.pagetoken})
            self.parameter.Query = json.dumps(query)
        if token & TOKEN_REDIRECT:
            self.parameter.Url = self.pagetoken
        if token & TOKEN_JSON:
            data = '{"%s": "%s"}' % (self.parameter.Enumerator.Token.Field, self.pagetoken)
            self.parameter.Json = data
        self.pagetoken = None

    def _setToken(self, response):
        token = self.parameter.Enumerator.Token
        if token.Type != TOKEN_NONE:
            if not token.IsConditional:
                if response.hasValue(token.Field):
                    self.pagetoken = response.getValue(token.Field)
            elif response.hasValue(token.ConditionField):
                if response.getValue(token.ConditionField) == token.ConditionValue:
                    self.pagetoken = response.getDefaultValue(token.Field, False)
        if token.Type & TOKEN_SYNC and response.hasValue(token.SyncField):
            self.synctoken = response.getValue(token.SyncField)
        return self.pagetoken is None

    def _getIterator(self):
        lastpage = False
        with self.session as s:
            while not lastpage:
                if self.page:
                    self._setParameter()
                self.page += 1
                lastpage = True
                response, self.error = execute(s, self.parameter, self.timeout, self.parser)
                if response.IsPresent:
                    result = response.Value
                    lastpage = self._setToken(result)
                    field = self.parameter.Enumerator.Field
                    if result.hasValue(field):
                        chunks = result.getValue(field)
                        self.row += len(chunks)
                        for item in chunks:
                            yield item


def execute(session, parameter, timeout, parser=None):
    response = uno.createUnoStruct('com.sun.star.beans.Optional<com.sun.star.auth.XRestKeyMap>')
    error = ''
    kwargs = _getKeyWordArguments(parameter)
    with session as s:
        try:
            with s.request(parameter.Method, parameter.Url, timeout=timeout, **kwargs) as r:
                r.raise_for_status()
        except requests.exceptions.HTTPError as e:
            error = e.args[0]
            print ("Http Error:", error)
            #error = "Request: %s - ERROR: %s - %s" % (parameter.Name, r.status_code, r.text)
        except requests.exceptions.ConnectionError as e:
            cause = e.args[0]
            error = str(cause.args[0])
            print ("Error Connecting:", error)
        except requests.exceptions.Timeout as e:
            cause = e.args[0]
            error = str(cause.args[0])
            print ("Timeout Error:", error)
        except requests.exceptions.RequestException as e:
            cause = e.args[0]
            error = str(cause.args[0])
            print ("OOps: Something Else", error)
        else:
            response.IsPresent = True
            if parser:
                print("OAuth2Service.execute():\n%s" % (r.json(), ))
                response.Value = r.json(object_pairs_hook=parser.jsonParser)
            else:
                print("OAuth2Service.execute():\n%s" % (r, ))
                response.Value = _parseResponse(r)
    return response, error

class Request(unohelper.Base,
              XRestRequest):
    def __init__(self, session, parameter, timeout, parser=None):
        self.session = session
        self.parameter = parameter
        self.timeout = timeout
        self.parser = parser
        self.error = None

    # XRestRequest
    def getWarnings(self):
        return self.error
    def clearWarnings(self):
        self.error = None
    def execute(self):
        response, self.error = execute(self.session, self.parameter, self.timeout, self.parser)
        return response

class Enumeration(unohelper.Base,
                  XRestEnumeration):
    def __init__(self, session, parameter, timeout, parser=None):
        self.session = session
        self.parameter = parameter
        self.timeout = timeout
        self.parser = parser
        t = self.parameter.Enumerator.Token
        self.chunked = t.Type != TOKEN_NONE
        self.synchro = t.Type & TOKEN_SYNC
        self.token = None
        self.sync = ''
        self.PageCount = 0

    @property
    def SyncToken(self):
        return self.sync

    # XRestEnumeration
    def hasMoreElements(self):
        return self.token is None or bool(self.token)
    def nextElement(self):
        if self.hasMoreElements():
            response, self.error = self._getResponse()
            return response
        raise NoSuchElementException()

    def _getResponse(self):
        t = self.parameter.Enumerator.Token
        if self.token:
            if t.Type & TOKEN_URL:
                self.parameter.Url = t.Value
            if t.Type & TOKEN_QUERY:
                query = json.loads(self.parameter.Query)
                query.update({t.Value: self.token})
                self.parameter.Query = json.dumps(query)
            if t.Type & TOKEN_REDIRECT:
                self.parameter.Url = self.token
            if t.Type & TOKEN_JSON:
                self.parameter.Json = '{"%s": "%s"}' % (t.Field, self.token)
        self.token = False
        self.sync = ''
        response, error = execute(self.session, self.parameter, self.timeout, self.parser)
        if response.IsPresent:
            r = response.Value
            #rows = list(r.getDefaultValue(self.parameter.Enumerator.Field, ()))
            if self.chunked:
                if t.IsConditional:
                    if r.getDefaultValue(t.ConditionField, None) == t.ConditionValue:
                        self.token = r.getDefaultValue(t.Field, False)
                else:
                    self.token = r.getDefaultValue(t.Field, False)
            if self.synchro:
                self.sync = r.getDefaultValue(t.SyncField, '')
        return response, error

class Enumerator(unohelper.Base,
                 XRestEnumeration):
    def __init__(self, ctx, session, parameter, timeout):
        self.ctx = ctx
        self.session = session
        self.parameter = parameter
        self.timeout = timeout
        t = self.parameter.Enumerator.Token
        self.chunked = t.Type != TOKEN_NONE
        self.synchro = t.Type & TOKEN_SYNC
        self.rows, self.token, self.sync, error = self._getRows()
        self.PageCount = 0
        if error:
            logMessage(self.ctx, SEVERE, error, "OAuth2Service","Enumerator()")

    @property
    def SyncToken(self):
        return self.sync

    # XRestEnumeration
    def hasMoreElements(self):
        return len(self.rows) > 0 or self.token is not None
    def nextElement(self):
        if self.rows:
            return self.rows.pop(0)
        elif self.token:
            self.rows, self.token, self.sync, error = self._getRows(self.token)
            if not error:
                return self.nextElement()
            logMessage(self.ctx, SEVERE, error, "OAuth2Service","Enumerator()")
        raise NoSuchElementException()

    def _getRows(self, token=None):
        try:
            t = self.parameter.Enumerator.Token
            if token:
                if t.Type & TOKEN_URL:
                    self.parameter.Url = t.Value
                if t.Type & TOKEN_QUERY:
                    query = json.loads(self.parameter.Query)
                    query.update({t.Value: token})
                    self.parameter.Query = json.dumps(query)
                if t.Type & TOKEN_REDIRECT:
                    self.parameter.Url = token
                if t.Type & TOKEN_JSON:
                    self.parameter.Json = '{"%s": "%s"}' % (t.Field, token)
                token = None
            rows = []
            sync = ''
            response, error = execute(self.session, self.parameter, self.timeout)
            if response.IsPresent:
                r = response.Value
                rows = list(r.getDefaultValue(self.parameter.Enumerator.Field, ()))
                if self.chunked:
                    if t.IsConditional:
                        if r.getDefaultValue(t.ConditionField, None) == t.ConditionValue:
                            token = r.getDefaultValue(t.Field, None)
                    else:
                        token = r.getDefaultValue(t.Field, None)
                if self.synchro:
                    sync = r.getDefaultValue(t.SyncField, '')
            return rows, token, sync, error
        except Exception as e:
            msg = "Error: %s - %s" % (e, traceback.print_exc())
            logMessage(self.ctx, SEVERE, msg, 'OAuth2Service', 'Enumerator()')


class InputStream(unohelper.Base,
                  XInputStream):
    def __init__(self, ctx, session, parameter, chunk, buffer, timeout):
        self.downloader = Downloader(ctx, session, parameter, chunk, buffer, timeout)
        self.chunks = self.downloader.getChunks()
        self.buffers = b''

    #XInputStream
    def readBytes(self, sequence, length):
        i = length - len(self.buffers)
        if i < 0:
            j = abs(i)
            sequence = uno.ByteSequence(self.buffers[:j])
            self.buffers = self.buffers[j:]
            return len(sequence), sequence
        sequence = uno.ByteSequence(self.buffers)
        self.buffers = b''
        while i > 0:
            chunk = next(self.chunks, b'')
            j = len(chunk)
            if j == 0:
                break
            elif j > i:
                sequence += chunk[:i]
                self.buffers = chunk[i:]
                break
            sequence += chunk
            i = length - len(sequence)
        return len(sequence), sequence
    def readSomeBytes(self, sequence, length):
        return self.readBytes(sequence, length)
    def skipBytes(self, length):
        self.downloader.skip(length)
    def available(self):
        return self.downloader.available()
    def closeInput(self):
        self.downloader.close()


class Downloader():
    def __init__(self, ctx, session, parameter, chunk, buffer, timeout):
        self.ctx = ctx
        self.session = session
        self.method = parameter.Method
        self.url = parameter.Url
        kwargs = _getKeyWordArguments(parameter)
        kwargs.update({'stream': True})
        # We need to use a "Range" Header... but it's not shure that parameter has Headers...
        if 'headers' not in kwargs:
            kwargs.update({'headers': {}})
        self.kwargs = kwargs
        self.chunk = chunk
        self.buffer = buffer
        self.timeout = timeout
        self.start = 0
        self.size = 0
        self.closed = False
    def _getSize(self, range):
        if range:
            return int(range.split('/').pop())
        return 0
    def _closed(self):
        return self.start == self.size if self.size else self.closed
    def getChunks(self):
        with self.session as s:
            while not self._closed():
                end = self.start + self.chunk
                if self.size:
                    end = min(end, self.size)
                self.kwargs['headers'].update({'Range': 'bytes=%s-%s' % (self.start, end -1)})
                with s.request(self.method, self.url, timeout=self.timeout, **self.kwargs) as r:
                    if r.status_code == s.codes.ok:
                        self.closed = True
                    elif r.status_code == s.codes.partial_content:
                        if self.size == 0:
                            self.size = self._getSize(r.headers.get('Content-Range'))
                    else:
                        self.closed = True
                        msg = "getChunks() ERROR: %s - %s" % (r.status_code, r.text)
                        logMessage(self.ctx, SEVERE, msg, "OAuth2Service", "Downloader()")
                        break
                    for c in r.iter_content(self.buffer):
                        self.start += len(c)
                        yield c
    def close(self):
        self.session.close()
        self.closed = True
    def available(self):
        return 0 if self.closed else self.chunk
    def skip(self, length):
        self.start += length


class OutputStream(unohelper.Base,
                   XOutputStream):
    def __init__(self, ctx, session, parameter, size, chunk, response, timeout):
        self.ctx = ctx
        self.session = session
        self.method = parameter.Method
        self.url = parameter.Url
        self.size = size
        self.chunk = chunk
        self.chunked = size > chunk
        self.buffers = b''
        self.response = response
        self.timeout = timeout
        kwargs = _getKeyWordArguments(parameter)
        # If Chunked we need to use a "Content-Range" Header...
        # but it's not shure that parameter has Headers...
        if self.chunked and 'headers' not in kwargs:
            kwargs.update({'headers': {}})
        self.kwargs = kwargs
        self.start = 0
        self.closed = False
        self.error = ''

    @property
    def length(self):
        return len(self.buffers)

    # XOutputStream
    def writeBytes(self, sequence):
        if self.closed:
            raise IOException('OutputStream is closed...', self)
        self.buffers += sequence.value
        if self._flushable():
            self._flush()
    def flush(self):
        if self.closed:
            raise IOException('OutputStream is closed...', self)
        if self._flushable(True):
            self._flush()
    def closeOutput(self):
        self.closed = True
        if self._flushable(True):
            self._flush()
        self.session.close()
        if self.error:
            raise IOException('Error Uploading file...', self)
    def _flushable(self, last=False):
        if last:
            return self.length > 0
        elif self.chunked:
            return self.length >= self.chunk
        return False
    def _flush(self):
        end = self.start + self.length -1
        header = {}
        if self.chunked:
            header = {'Content-Range': 'bytes %s-%s/%s' % (self.start, end, self.size)}
            self.kwargs['headers'].update(header)
        self.kwargs.update({'data': self.buffers})
        with self.session.request(self.method, self.url, timeout=self.timeout, **self.kwargs) as r:
            if r.status_code == self.session.codes.ok:
                self.response.IsPresent = True
                self.response.Value = _parseResponse(r)
                self.start = end
                self.buffers = b''
            elif r.status_code == self.session.codes.created:
                self.response.IsPresent = True
                self.response.Value = _parseResponse(r)
                self.start = end
                self.buffers = b''
            elif r.status_code == self.session.codes.permanent_redirect:
                if 'Range' in r.headers:
                    self.start += int(r.headers['Range'].split('-')[-1]) +1
                    self.buffers = b''
            else:
                msg = 'ERROR: %s - %s' % (r.status_code, r.text)
                logMessage(self.ctx, SEVERE, msg, "OAuth2Service","OutputStream()")
        return


class StreamListener(unohelper.Base,
                     XStreamListener):
    def __init__(self, ctx, callback, itemid, response):
        self.ctx = ctx
        self.callback = callback
        self.itemid = itemid
        self.response = response

    # XStreamListener
    def started(self):
        pass
    def closed(self):
        if self.response.IsPresent:
            self.callback(self.itemid, self.response)
        else:
            msg = "ERROR ..."
            logMessage(self.ctx, SEVERE, msg, "OAuth2Service","StreamListener()")
    def terminated(self):
        pass
    def error(self, error):
        msg = "ERROR ..."
        logMessage(self.ctx, SEVERE, msg, "OAuth2Service","StreamListener()")
    def disposing(self, event):
        pass


class Uploader(unohelper.Base,
               XRestUploader):
    def __init__(self, ctx, session, chunk, url, callBack, timeout):
        self.ctx = ctx
        self.session = session
        self.chunk = chunk
        self.url = url
        self.callback = callBack
        self.timeout = timeout

    def start(self, itemid, parameter):
        input, size = self._getInputStream(itemid)
        if size:
            optional = 'com.sun.star.beans.Optional<com.sun.star.auth.XRestKeyMap>'
            response = uno.createUnoStruct(optional)
            output = self._getOutputStream(parameter, size, response)
            listener = self._getStreamListener(itemid, response)
            pump = self.ctx.ServiceManager.createInstance('com.sun.star.io.Pump')
            pump.setInputStream(input)
            pump.setOutputStream(output)
            pump.addListener(listener)
            pump.start()
            return True
        return False

    def _getInputStream(self, itemid):
        url = '%s/%s' % (self.url, itemid)
        sf = self.ctx.ServiceManager.createInstance('com.sun.star.ucb.SimpleFileAccess')
        if sf.exists(url):
            return sf.openFileRead(url), sf.getSize(url)
        return None, None

    def _getOutputStream(self, param, size, resp):
        return OutputStream(self.ctx, self.session, param, size, self.chunk, resp, self.timeout)

    def _getStreamListener(self, itemid, response):
        return StreamListener(self.ctx, self.callback, itemid, response)


# Private method

def _getKeyWordArguments(parameter):
    kwargs = {}
    if parameter.Header:
        kwargs['headers'] = json.loads(parameter.Header)
    if parameter.Query:
        kwargs['params'] = json.loads(parameter.Query)
    if parameter.Data:
        kwargs['data'] = json.loads(parameter.Data)
    if parameter.Json:
        kwargs['json'] = json.loads(parameter.Json)
    if parameter.NoAuth:
        kwargs['auth'] = NoOAuth2()
    if parameter.NoRedirect:
        kwargs['allow_redirects'] = False
    return kwargs

def _parseResponse(response):
    try:
        content = response.headers.get('Content-Type', '')
        if content.startswith('application/json'):
            result = response.json(object_pairs_hook=_jsonParser)
        else:
            result = KeyMap(**response.headers)
        return result
    except Exception as e:
        print("request._parseResponse() ERROR: %s - %s" % (e, traceback.print_exc()))

def _jsonParser(data):
    keymap = KeyMap()
    for key, value in data:
        if isinstance(value, list):
            value = tuple(value)
        keymap.setValue(key, value)
    return keymap
