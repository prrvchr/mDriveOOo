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
package io.github.prrvchr.uno.sdbc;

import java.util.Arrays;

import com.sun.star.container.XNameAccess;
import com.sun.star.lib.uno.helper.WeakBase;
import com.sun.star.sdbc.DataType;
import com.sun.star.sdbc.SQLException;
import com.sun.star.sdbc.XArray;
import com.sun.star.sdbc.XResultSet;

import io.github.prrvchr.uno.helper.UnoHelper;

public class Array
extends WeakBase
implements XArray
{
    private Object[] m_Array = new Object[0];
    private int m_Type = 0;
    private String m_TypeName;

    // The constructor method:
    public Array(java.sql.Array array)
    throws SQLException
    {
        try
        {
            m_Array = (Object[]) array.getArray();
            m_Type = UnoHelper.mapSQLDataType(array.getBaseType());
            m_TypeName = UnoHelper.mapSQLDataTypeName(array.getBaseTypeName(), m_Type);
        } 
        catch (java.sql.SQLException e)
        {
            throw UnoHelper.getSQLException(e, this);
        }
    }
    public Array(Object[] array,
                 String typename)
        throws SQLException
    {
        try
        {
            m_Array = array;
            m_Type = UnoHelper.getConstantValue(DataType.class, typename);
            m_TypeName = typename;
        }
        catch (java.sql.SQLException e)
        {
            throw UnoHelper.getSQLException(e, this);
        }
    }


    @Override
    public Object[] getArray(XNameAccess arg0)
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
        return m_Type;
    }

    @Override
    public String getBaseTypeName()
    throws SQLException
    {
        return m_TypeName;
    }

    @Override
    public XResultSet getResultSet(XNameAccess arg0)
    throws SQLException
    {
        // TODO Auto-generated method stub
        return null;
    }

    @Override
    public XResultSet getResultSetAtIndex(int arg0, int arg1, XNameAccess arg2)
    throws SQLException
    {
        // TODO Auto-generated method stub
        return null;
    }


}
