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
package io.github.prrvchr.uno.lang;

import java.util.Map;
import java.util.Map.Entry;

import com.sun.star.beans.Property;
import com.sun.star.lang.WrappedTargetException;
import com.sun.star.lang.XServiceInfo;
import com.sun.star.lib.uno.helper.PropertySet;

import io.github.prrvchr.uno.helper.UnoHelper;


public abstract class ServiceProperty
extends PropertySet
implements XServiceInfo
{
	private final String m_name;
	private final String[] m_services;

	// The constructor method:
	public ServiceProperty(String name,
						   String[] services)
	{
		super();
		m_name = name;
		m_services = services;
	}
	public ServiceProperty(String name,
						   String[] services,
						   Map<String, Property> properties)
	{
		super();
		m_name = name;
		m_services = services;
		for (Entry <String, Property> map : properties.entrySet())
		{
			registerProperty(map.getValue(), map.getKey());
		}
	}


	// com.sun.star.lang.XServiceInfo:
	@Override
	public String getImplementationName()
	{
		return ServiceInfo.getImplementationName(m_name);
	}

	@Override
	public String[] getSupportedServiceNames()
	{
		return ServiceInfo.getSupportedServiceNames(m_services);
	}

	@Override
	public boolean supportsService(String service)
	{
		return ServiceInfo.supportsService(m_services, service);
	}


	// com.sun.star.lib.uno.helper.PropertySet:
	@Override
	public boolean convertPropertyValue(Property property,
										Object[] newValue,
										Object[] oldValue,
										Object value)
	throws com.sun.star.lang.IllegalArgumentException,
		   com.sun.star.lang.WrappedTargetException
	{
		Object id = getPropertyId(property);
		return UnoHelper.convertPropertyValue(property, newValue, oldValue, value, this, id);
	}

	@Override
	public void setPropertyValueNoBroadcast(Property property,
											Object value)
	throws WrappedTargetException
	{
		Object id = getPropertyId(property);
		UnoHelper.setPropertyValueNoBroadcast(property, value, this, id);
	}

	@Override
	public Object getPropertyValue(Property property)
	{
		Object id = getPropertyId(property);
		return UnoHelper.getPropertyValue(property, this, id);
	}


}
