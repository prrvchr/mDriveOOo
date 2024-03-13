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

import java.util.Arrays;

import com.sun.star.container.XNameAccess;
import com.sun.star.lib.uno.helper.WeakBase;
import com.sun.star.sdbc.DataType;
import com.sun.star.sdbc.SQLException;
import com.sun.star.sdbc.XArray;
import com.sun.star.sdbc.XResultSet;


public class Array
    extends WeakBase
    implements XArray
{

    private Object[] m_Array = null;
    private String m_Type = null;

    // The constructor method:
    public Array(java.sql.Array array)
        throws SQLException
    {
        try {
            m_Array = (Object[]) array.getArray();
            m_Type = array.getBaseTypeName();
        }
        catch (java.sql.SQLException e) {
            throw UnoHelper.getSQLException(e, this);
        }
        
    }
    public Array(Object[] array,
                 String type)
    {
        m_Array = array;
        m_Type = type;
    }

    @Override
    public Object[] getArray(XNameAccess map)
        throws SQLException
    {
        return m_Array;
    }

    @Override
    public Object[] getArrayAtIndex(int index, int count, XNameAccess map)
        throws SQLException
    {
        return Arrays.copyOfRange(m_Array, index, index + count);
    }

    @Override
    public int getBaseType()
        throws SQLException
    {
        try {
            return UnoHelper.getConstantValue(DataType.class, m_Type);
        }
        catch (java.sql.SQLException e) {
            throw UnoHelper.getSQLException(e, this);
        }
    }

    @Override
    public String getBaseTypeName()
        throws SQLException
    {
        return m_Type;
    }

    @Override
    public XResultSet getResultSet(XNameAccess map)
        throws SQLException
    {
        return null;
    }

    @Override
    public XResultSet getResultSetAtIndex(int index, int count, XNameAccess map)
        throws SQLException
    {
        return null;
    }


}