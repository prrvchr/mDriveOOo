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

import java.sql.Connection;
import java.sql.ResultSet;
import java.sql.Statement;
import java.util.HashMap;

import com.sun.star.container.XNameAccess;
import com.sun.star.sdbcx.XUser;
import com.sun.star.sdbcx.XUsersSupplier;


public class UsersSupplierHelper
implements XUsersSupplier
{
    private final java.sql.Connection m_Connection;

    // The constructor method:
    public UsersSupplierHelper(Connection connection)
    {
        m_Connection = connection;
    }


    // com.sun.star.sdbcx.XUsersSupplier:
    @Override
    public XNameAccess getUsers()
    {
        ResultSet result = null;
        String query = "SELECT * FROM INFORMATION_SCHEMA.SYSTEM_USERS";
        try
        {
            Statement statement = m_Connection.createStatement();
            result = statement.executeQuery(query);
        }
        catch (java.sql.SQLException e) {e.getStackTrace();}
        if (result == null) return null;
        @SuppressWarnings("unused")
        String type = "com.sun.star.sdbc.XUser";
        @SuppressWarnings("unused")
        HashMap<String, XUser> elements = new HashMap<>();
        try
        {
            int i = 1;
            int count = result.getMetaData().getColumnCount();
            while (result.next())
            {
                for (int j = 1; j <= count; j++)
                {
                    String value = UnoHelper.getResultSetValue(result, j);
                    System.out.println("UsersSupplier.getUsers() " + i + " - " + value);
                }
                i++;
            }
        } catch (java.sql.SQLException e) {e.printStackTrace();}
        return null;
    }


}
