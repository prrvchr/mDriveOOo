/*
╔════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                    ║
║   Copyright (c) 2020-24 https://prrvchr.github.io                                  ║
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

import com.sun.star.container.NoSuchElementException;
import com.sun.star.lang.NullPointerException;
import com.sun.star.resource.MissingResourceException;
import com.sun.star.resource.XStringResourceResolver;
import com.sun.star.uno.Exception;
import com.sun.star.uno.XComponentContext;


public class OfficeResourceBundle
    implements AutoCloseable
{

    private XComponentContext m_xContext;
    private String m_identifier;
    private String m_path;
    private String m_basename;
    private boolean m_attempted;
    private XStringResourceResolver m_xResolver;

    /** constructs a resource bundle
        @param  context
            the component context to operate in
        @param  basename
            the base name of the resource file which should be accessed
        @throws com.sun.star.lang.NullPointerException
            if the given component context is null
     */
    public OfficeResourceBundle(XComponentContext context,
                                String identifier,
                                String path,
                                String basename)
        throws NullPointerException
    {
        if (context == null) {
            throw new NullPointerException();
        }
        m_xContext = context;
        m_identifier = identifier;
        m_path = path;
        m_basename = basename;
        m_attempted = false;
    }

    @Override
    public void close() {
        UnoHelper.disposeComponent(m_xResolver);
    }

    /**
     * Return the bundle's base name as passed to the constructor.
     */
    public String getBaseName() {
        return m_basename;
    }

    /**
     * Return the extension identifier name as passed to the constructor.
     */
    public String getIdentifier() {
        return m_identifier;
    }

    /** loads the string with the given resource id from the resource bundle
        @param  id
            the id of the string to load
        @return
            the requested resource string. If no string with the given id exists in the resource bundle,
            an empty string is returned.
     * @throws Exception 
     * @throws NoSuchElementException 
     * @throws MissingResourceException 
    */
    public String loadString( int id )
        throws MissingResourceException,
               NoSuchElementException,
               Exception
    {
        synchronized (this) {
            String string = "";
            if (loadResolver()) {
                string =  m_xResolver.resolveString(getStringResourceKey(id));
            }
            return string;
        }
    }

    /** determines whether the resource bundle has a string with the given id
        @param  id
            the id of the string whose existence is to be checked
        @return
            true if and only if a string with the given ID exists in the resource
            bundle.
     * @throws Exception 
     * @throws NoSuchElementException 
    */
    public boolean hasString( int id )
        throws NoSuchElementException,
               Exception
    {
        synchronized (this) {
            boolean has = false;
            if (loadResolver()) {
                has = m_xResolver.hasEntryForId(getStringResourceKey(id));
            }
            return has;
        }
    }

    private String getStringResourceKey(int id)
    {
        return Integer.toString(id);
    }

    private boolean loadResolver()
        throws NoSuchElementException,
               Exception
    {
        if (m_attempted) {
            return m_xResolver != null;
        }
        m_attempted = true;
        XStringResourceResolver resolver = UnoHelper.getResourceResolver(m_xContext, m_identifier, m_path, m_basename);
        if (resolver != null) {
            m_xResolver = resolver;
            return true;
        }
        return false;
    }

}
