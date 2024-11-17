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
package io.github.prrvchr.uno.helper;

import com.sun.star.uno.Type;

import io.github.prrvchr.uno.helper.PropertySetAdapter.PropertyGetter;
import io.github.prrvchr.uno.helper.PropertySetAdapter.PropertySetter;


public class PropertyWrapper
{

    private final Type m_type;
    private final short m_attributes;
    private final PropertyGetter m_getter;
    private final PropertySetter m_setter;

    // The constructor method:
    public PropertyWrapper(Type type,
                           PropertyGetter getter,
                           PropertySetter setter)
    {
        this(type, (short) 0, getter, setter);
    }

    public PropertyWrapper(Type type,
                           short attributes,
                           PropertyGetter getter,
                           PropertySetter setter)
    {
        m_type = type;
        m_attributes = attributes;
        m_getter = getter;
        m_setter = setter;
    }

    public Type getType()
    {
        return m_type;
    }

    public short getAttribute()
    {
        return m_attributes;
    }

    public PropertyGetter getGetter()
    {
        return m_getter;
    }

    public PropertySetter getSetter()
    {
        return m_setter;
    }
}
