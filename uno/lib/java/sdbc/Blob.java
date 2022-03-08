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

import java.io.InputStream;

import com.sun.star.io.XInputStream;
import com.sun.star.lib.uno.adapter.InputStreamToXInputStreamAdapter;
import com.sun.star.lib.uno.helper.WeakBase;
import com.sun.star.sdbc.SQLException;
import com.sun.star.sdbc.XBlob;

import io.github.prrvchr.uno.helper.UnoHelper;


public class Blob
extends WeakBase
implements XBlob
{
	private java.sql.Statement m_Statement;
	private java.sql.Blob m_Blob;

	
	// The constructor method:
	public Blob(java.sql.Statement statement,
                java.sql.Blob blob)
	{
		m_Statement = statement;
		m_Blob = blob;
	}


	// com.sun.star.sdbc.XBlob:
	@Override
	public XInputStream getBinaryStream() throws SQLException {
		try
		{
			InputStream input = m_Blob.getBinaryStream();
			return new InputStreamToXInputStreamAdapter(input);
		}
		catch (java.sql.SQLException e)
		{
			throw UnoHelper.getSQLException(e, this);
		}
	}


	@Override
	public byte[] getBytes(long position, int length) throws SQLException {
		try
		{
			return m_Blob.getBytes(position, length);
		}
		catch (java.sql.SQLException e)
		{
			throw UnoHelper.getSQLException(e, this);
		}
	}


	@Override
	public long length() throws SQLException {
		try
		{
			return m_Blob.length();
		}
		catch (java.sql.SQLException e)
		{
			throw UnoHelper.getSQLException(e, this);
		}
	}


	@Override
	public long position(byte[] pattern, long start) throws SQLException {
		try
		{
			return m_Blob.position(pattern, start);
		}
		catch (java.sql.SQLException e)
		{
			throw UnoHelper.getSQLException(e, this);
		}
	}


	@Override
	public long positionOfBlob(XBlob blob, long start) throws SQLException {
		try
		{
			java.sql.Blob b = UnoHelper.getSQLBlob(m_Statement, blob);
			return m_Blob.position(b, start);
		}
		catch (java.sql.SQLException e)
		{
			throw UnoHelper.getSQLException(e, this);
		}
	}


}
