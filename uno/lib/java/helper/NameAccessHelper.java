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
package io.github.prrvchr.uno.helper;

import java.util.Map;

import com.sun.star.container.NoSuchElementException;
import com.sun.star.container.XNameAccess;
import com.sun.star.lang.WrappedTargetException;
import com.sun.star.uno.Type;


public class NameAccessHelper<T>
implements XNameAccess
{
    private final Map<String, T> m_elements;
    private String m_type = "com.sun.star.uno.XInterface";

    // The constructor method:
    public NameAccessHelper(Map<String, T> elements)
    {
        m_elements = elements;
    }
    public NameAccessHelper(Map<String, T> elements,
                            String type)
    {
        m_elements = elements;
        m_type = type;
    }


    // com.sun.star.container.XElementAccess <- XNameAccess:
    @Override
    public Type getElementType()
    {
        return new Type(m_type);
    }

    @Override
    public boolean hasElements()
    {
        return !m_elements.isEmpty();
    }


    // com.sun.star.container.XNameAccess:
    @Override
    public Object getByName(String name)
    throws NoSuchElementException, WrappedTargetException
    {
        if (!hasByName(name)) throw new NoSuchElementException();
        return m_elements.get(name);
    }

    @Override
    public String[] getElementNames()
    {
        int len = m_elements.size();
        return m_elements.keySet().toArray(new String[len]);
    }

    @Override
    public boolean hasByName(String name)
    {
        return m_elements.containsKey(name);
    }


}
