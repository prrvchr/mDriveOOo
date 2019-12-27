#!
# -*- coding: utf_8 -*-

#from __futur__ import absolute_import

import uno
import unohelper

from com.sun.star.awt import XRequestCallback
from com.sun.star.util import XCancellable
from com.sun.star.connection import AlreadyAcceptingException
from com.sun.star.connection import ConnectionSetupException
from com.sun.star.lang import IllegalArgumentException
from com.sun.star.io import IOException
from com.sun.star.logging.LogLevel import INFO
from com.sun.star.logging.LogLevel import SEVERE

from unolib import createService
from unolib import getStringResource

from .requests.compat import unquote_plus

from .logger import logMessage

from .configuration import g_identifier

import time
from threading import Thread
from threading import Condition
from timeit import default_timer as timer
import traceback


class WizardServer(unohelper.Base,
                   XCancellable,
                   XRequestCallback):
    def __init__(self, ctx):
        self.ctx = ctx
        self.watchdog = None

    # XCancellable
    def cancel(self):
        if self.watchdog and self.watchdog.is_alive():
            self.watchdog.cancel()

    # XRequestCallback
    def addCallback(self, controller, configuration):
        lock = Condition()
        code = controller.AuthorizationCode
        uuid = controller.Uuid
        address = configuration.Url.Scope.Provider.RedirectAddress
        port = configuration.Url.Scope.Provider.RedirectPort
        server = Server(self.ctx, code, uuid, address, port, lock)
        timeout = configuration.HandlerTimeout
        self.watchdog = WatchDog(server, controller, timeout, lock)
        server.start()
        self.watchdog.start()
        logMessage(self.ctx, INFO, "WizardServer Started ... Done", 'WizardServer', 'addCallback()')


class WatchDog(Thread):
    def __init__(self, server, controller, timeout, lock):
        Thread.__init__(self)
        self.server = server
        self.controller = controller
        self.timeout = timeout
        self.lock = lock
        self.step = 50
        self.end = 0

    def run(self):
        wait = self.timeout/self.step
        start = now = timer()
        self.end = start + self.timeout
        self.controller.notify(0)
        canceled = True
        with self.lock:
            while now < self.end and self.server.is_alive():
                elapsed = now - start
                percent =  min(99, int(elapsed / self.timeout * 100))
                self.controller.notify(percent)
                self.lock.wait(wait)
                now = timer()
            if self.server.is_alive():
                self.server.acceptor.stopAccepting()
            if self.end != 0:
                self.controller.notify(100)
            self.lock.notifyAll()
            logMessage(self.server.ctx, INFO, "WatchDog Running ... Done", 'WatchDog', 'run()')

    def cancel(self):
        if self.server.is_alive():
            self.end = 0
            self.server.join()


class Server(Thread):
    def __init__(self, ctx, code, uuid, address, port, lock):
        Thread.__init__(self)
        self.ctx = ctx
        self.code = code
        self.uuid = uuid
        self.argument = 'socket,host=%s,port=%s,tcpNoDelay=1' % (address, port)
        self.acceptor = createService(self.ctx, 'com.sun.star.connection.Acceptor')
        self.lock = lock

    def run(self):
        connection = None
        try:
            connection = self.acceptor.accept(self.argument)
        except AlreadyAcceptingException as e:
            msg = "Error: %s - %s" % (e, traceback.print_exc())
            logMessage(self.ctx, SEVERE, msg, 'Server', 'run()')
        except ConnectionSetupException as e:
            msg = "Error: %s - %s" % (e, traceback.print_exc())
            logMessage(self.ctx, SEVERE, msg, 'Server', 'run()')
        except IllegalArgumentException as e:
            msg = "Error: %s - %s" % (e, traceback.print_exc())
            logMessage(self.ctx, SEVERE, msg, 'Server', 'run()')
        if connection:
            with self.lock:
                result = self._getResult(connection)
                location = self._getResultLocation(result)
                header = 'HTTP/1.1 302 Found\r\nLocation: %s\r\nConnection: Closed\r\n\r\n' % location
                try:
                    connection.write(uno.ByteSequence(header.encode('utf8')))
                except IOException as e:
                    msg = "Error: %s - %s" % (e, traceback.print_exc())
                    logMessage(self.ctx, SEVERE, msg, 'Server', 'run()')
                connection.flush()
                connection.close()
                self.acceptor.stopAccepting()
                self.lock.notifyAll()
                logMessage(self.ctx, INFO, "Server Running ... Done", 'Server', 'run()')

    def _readString(self, connection, length):
        length, sequence = connection.read(None, length)
        return sequence.value.decode()

    def _readLine(self, connection, eol='\r\n'):
        line = ''
        while not line.endswith(eol):
            line += self._readString(connection, 1)
        return line.strip()

    def _getRequest(self, connection):
        method, url, version = None, '/', 'HTTP/0.9'
        line = self._readLine(connection)
        parts = line.split(' ')
        if len(parts) > 1:
            method = parts[0].strip()
            url = parts[1].strip()
        if len(parts) > 2:
            version = parts[2].strip()
        return method, url, version

    def _getHeaders(self, connection):
        headers = {'Content-Length': 0}
        while True:
            line = self._readLine(connection)
            if not line:
                break
            parts = line.split(':')
            if len(parts) > 1:
                headers[parts[0].strip()] = ':'.join(parts[1:]).strip()
        return headers

    def _getContentLength(self, headers):
        return int(headers['Content-Length'])

    def _getParameters(self, connection):
        parameters = ''
        method, url, version = self._getRequest(connection)
        headers = self._getHeaders(connection)
        if method == 'GET':
            parts = url.split('?')
            if len(parts) > 1:
                parameters = '?'.join(parts[1:]).strip()
        elif method == 'POST':
            length = self._getContentLength(headers)
            parameters = self._readString(connection, length).strip()
        return unquote_plus(parameters)

    def _getResponse(self, parameters):
        response = {}
        for parameter in parameters.split('&'):
            parts = parameter.split('=')
            if len(parts) > 1:
                name = parts[0].strip()
                value = '='.join(parts[1:]).strip()
                response[name] = value
        return response

    def _getResult(self, connection):
        parameters = self._getParameters(connection)
        response = self._getResponse(parameters)
        if 'code' in response and 'state' in response:
            if response['state'] == self.uuid:
                self.code.Value = response['code']
                self.code.IsPresent = True
                return True
        msg = 'Request response Error: %s - %s' % (parameters, response)
        logMessage(self.ctx, SEVERE, msg, 'Server', '_getResult()')
        return False

    def _getResultLocation(self, result):
        basename = 'Success' if result else 'Error'
        stringresource = getStringResource(self.ctx, g_identifier, 'OAuth2OOo')
        location = stringresource.resolveString('PageWizard3.%s.Url' % basename)
        return location
