/*
╔════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                    ║
║   Copyright (c) 2020 https://prrvchr.github.io                                     ║
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
*/
/**************************************************************
 * 
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements.  See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership.  The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License.  You may obtain a copy of the License at
 * 
 *   http://www.apache.org/licenses/LICENSE-2.0
 * 
 * Unless required by applicable law or agreed to in writing,
 * software distributed under the License is distributed on an
 * "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 * KIND, either express or implied.  See the License for the
 * specific language governing permissions and limitations
 * under the License.
 * 
 *************************************************************/
package io.github.prrvchr.uno.helper;

import java.io.PrintWriter;
import java.io.StringWriter;

import com.sun.star.lang.NullPointerException;
import com.sun.star.resource.MissingResourceException;
import com.sun.star.uno.Exception;
import com.sun.star.uno.XComponentContext;


public class ResourceBasedEventLogger
    extends EventLogger
{
    private String m_basename;
    private String m_identifier;
    private OfficeResourceBundle m_Bundle;

    public ResourceBasedEventLogger(XComponentContext context,
                                    String identifier,
                                    String basename,
                                    String logger)
    {
        super(context, logger);
        m_identifier = identifier;
        m_basename = basename;
        try {
            m_Bundle = new OfficeResourceBundle(context, identifier, basename);
        }
        catch (NullPointerException e) {
            throw new RuntimeException(e);
        }
    }
    
    public ResourceBasedEventLogger(ResourceBasedEventLogger logger)
    {
        super(logger.m_xContext, logger.getName());
        m_identifier = logger.m_identifier;
        m_basename = logger.m_basename;
        try {
            m_Bundle = new OfficeResourceBundle(logger.m_xContext, logger.m_identifier, logger.m_basename);
        }
        catch (NullPointerException nullPointerException) {
            throw new RuntimeException(nullPointerException);
        }
    }
    
    /**
     * Logs a given message with its arguments, without the caller's class and method.
     * @param level the log level
     * @param id the resource ID of the message to log
     * @param arguments the arguments to log, which are converted to strings and replace $1$, $2$, up to $n$ in the message
     * @return whether logging succeeded
     */
    public boolean log(int level,
                       int id,
                       Object... arguments)
    {
        if (isLoggable(level))
            return impl_log(level, null, null, loadStringMessage(id), arguments);
        return false;
    }

    /**
     * Logs a given message with its arguments, with the caller's class and method
     * taken from a (relatively costly!) stack trace.
     * @param level the log level
     * @param id the resource ID of the message to log
     * @param arguments the arguments to log, which are converted to strings and replace $1$, $2$, up to $n$ in the message
     * @return whether logging succeeded
     */
    public boolean logp(int level,
                        int id,
                        Object... arguments)
    {
        if (isLoggable(level)) {
            StackTraceElement caller = Thread.currentThread().getStackTrace()[2];
            return impl_log(level, caller.getClassName(), caller.getMethodName(), loadStringMessage(id), arguments);
        }
        return false;
    }

    protected boolean logp(int level,
                           StackTraceElement caller,
                           int id,
                           Object... arguments)
    {
        if (isLoggable(level)) {
            return impl_log(level, caller.getClassName(), caller.getMethodName(), loadStringMessage(id), arguments);
        }
        return false;
    }

    private String loadStringMessage(int id)
    {
        String message;
        try {
            message = m_Bundle.loadString(id);
        }
        catch (MissingResourceException | Exception e) {
            StringWriter error = new StringWriter();
            e.printStackTrace(new PrintWriter(error));
            message = String.format("<invalid event resource: '%s:%d'>\n%s", m_basename, id, error.getBuffer().toString());
        }
        return message;
    }

}
