#!
# -*- coding: utf-8 -*-

"""
╔════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                    ║
║   Copyright (c) 2020-25 https://prrvchr.github.io                                  ║
║                                                                                    ║
║   Permission is hereby granted, free of charge, to any person obtaining            ║
║   a copy of this software and associated documentation files (the "Software"),     ║
║   to deal in the Software without restriction, including without limitation        ║
║   the rights to use, copy, modify, merge, publish, distribute, sublicense,         ║
║   and/or sell copies of the Software, and to permit persons to whom the Software   ║
║   is furnished to do so, subject to the following conditions:                      ║
║                                                                                    ║
║   The above copyright notice and this permission notice shall be included in       ║
║   all copies or substantial portions of the Software.                              ║
║                                                                                    ║
║   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,                  ║
║   EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES                  ║
║   OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.        ║
║   IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY             ║
║   CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,             ║
║   TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE       ║
║   OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.                                    ║
║                                                                                    ║
╚════════════════════════════════════════════════════════════════════════════════════╝
"""

from .unotool import createService
from .unotool import executeDesktopDispatch
from .unotool import getDesktop
from .unotool import getNamedValue

from .oauth20 import g_identifier as g_identifier1
from .oauth20 import g_extension as g_extension1
from .oauth20 import g_version as g_version1

from .jdbcdriver import g_identifier as g_identifier2
from .jdbcdriver import g_extension as g_extension2
from .jdbcdriver import g_version as g_version2

from .configuration import g_extension
# from .configuration import g_identifier

import traceback


def getExtensions():
    return {g_identifier1: (g_extension1, g_version1),
            g_identifier2: (g_extension2, g_version2)}


# def executeReplicator(ctx, job, logger, cancel, timeout, queue):
#    indicator = _getAvailableStatusIndicator(ctx)
#    while not queue.empty() and not cancel.isSet():
#        arguments, listener = queue.get_nowait()
#        task = Replicator(ctx, job, listener, timeout, **getJobArguments(arguments))
#        runner = Runner(ctx, task, cancel, indicator=indicator, logger=logger)
#        runner.start()


def startReplication1(ctx, listener=None, /, **arguments):
    try:
        service = 'com.sun.star.task.Job'
        args = getNamedValue('JobName', f'{g_extension}.Replicator')
        job = ctx.ServiceManager.createInstanceWithArgumentsAndContext(service, (args, ), ctx)
        # job = createService(ctx, 'com.sun.star.task.Job', args)
        job.executeAsync(arguments, listener)
    except Exception:
        print("helper.startReplication() ERROR: %s" % traceback.format_exc())


def startReplication(ctx, listener=None, /, **kwargs):
    url = f'vnd.sun.star.job:alias={g_extension}.Replicator'
    executeDesktopDispatch(ctx, url, listener, **kwargs)


def _getAvailableStatusIndicator(ctx):
    try:
        frame = getDesktop(ctx).getCurrentFrame()
        if frame and frame.LayoutManager:
            statusbar = frame.LayoutManager.getElement('private:resource/statusbar/statusbar')
            if statusbar and hasattr(statusbar, 'StatusIndicator'):
                return statusbar.StatusIndicator

        factory = createService(ctx, 'com.sun.star.task.StatusIndicatorFactory')
        if factory:
            return factory.createStatusIndicator()
    except Exception:
        print("helper._getAvailableStatusIndicator() ERROR: %s" % traceback.format_exc())
        pass
    return None
