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
import java.sql.Driver;
import java.sql.DriverPropertyInfo;
import java.sql.SQLException;
import java.sql.SQLFeatureNotSupportedException;
import java.util.Properties;
import java.util.logging.Logger;


public class DriverHelper implements Driver
{
	private Driver m_driver;

	// The constructor method:
	public DriverHelper(Driver driver)
	{
		m_driver = driver;
	}

	// java.sql.Driver:
	@Override
	public boolean acceptsURL(String url)
	throws SQLException
	{
		return m_driver.acceptsURL(url);
	}

	@Override
	public Connection connect(String url, Properties properties)
	throws SQLException
	{
		return m_driver.connect(url, properties);
	}

	@Override
	public int getMajorVersion()
	{
		return m_driver.getMajorVersion();
	}

	@Override
	public int getMinorVersion()
	{
		return m_driver.getMinorVersion();
	}

	@Override
	public Logger getParentLogger()
	throws SQLFeatureNotSupportedException
	{
		return null;
	}

	@Override
	public DriverPropertyInfo[] getPropertyInfo(String url, Properties properties)
	throws SQLException
	{
		return m_driver.getPropertyInfo(url, properties);
	}

	@Override
	public boolean jdbcCompliant()
	{
		return m_driver.jdbcCompliant();
	}


}
