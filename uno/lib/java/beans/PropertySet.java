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

package io.github.prrvchr.uno.beans;

import java.lang.reflect.Field;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.util.Map;
import java.util.Map.Entry;

import com.sun.star.beans.Property;
//import com.sun.star.beans.UnknownPropertyException;
//import com.sun.star.beans.XPropertySetInfo;
import com.sun.star.lang.DisposedException;
import com.sun.star.lang.WrappedTargetException;
import com.sun.star.uno.Any;
import com.sun.star.uno.AnyConverter;
import com.sun.star.uno.Type;
import com.sun.star.uno.UnoRuntime;
import com.sun.star.uno.XInterface;


public abstract class PropertySet
extends com.sun.star.lib.uno.helper.PropertySet
{

    private static String m_fieldPrefix = "m_";
    private static String m_getterPrefix = "_get";
    private static String m_setterPrefix = "_set";

    public PropertySet()
    {
        super();
    }
    public PropertySet(Map<String, Property> properties)
    {
        super();
        for (Entry <String, Property> map : properties.entrySet())
        {
            registerProperty(map.getValue(), map.getKey());
        }
    }


    /** Checks whether this component (which you should have locked, prior to this call, and until you are done using) is disposed, throwing DisposedException if it is. */
    protected synchronized final void checkDisposed()
    {
        if (bInDispose || bDisposed)
            throw new DisposedException();
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
        oldValue[0] = getPropertyValue(property);
        Class<?> clazz = property.Type.getZClass();
        boolean voidvalue = false;
        boolean anyvalue = value instanceof Any;
        if (anyvalue)
            voidvalue = ((Any) value).getObject() == null;
        else
            voidvalue = value == null;
        if (voidvalue && clazz.isPrimitive())
            throw new com.sun.star.lang.IllegalArgumentException("The implementation does not support the MAYBEVOID attribute for this property");
        Object converted = null;
        if (clazz.equals(Any.class))
        {
            if (anyvalue)
                converted = value;
            else
            {
                if (value instanceof XInterface)
                {
                    XInterface xInt = UnoRuntime.queryInterface(XInterface.class, value);
                    if (xInt != null)
                        converted = new Any(new Type(XInterface.class), xInt);
                }
                else if (value == null)
                {
                    if (oldValue[0] == null)
                        converted = new Any(new Type(), null);
                    else
                        converted = new Any(((Any)oldValue[0]).getType(), null);
                }
                else
                    converted = new Any(new Type(value.getClass()), value);
            }
        }
        else
            converted = convert(clazz, value);
        newValue[0] = converted;
        return true;
    }

    private static Object convert(Class<?> clazz, Object object)
    throws com.sun.star.lang.IllegalArgumentException
    {
        Object value = null;
        if (object == null || (object instanceof Any && ((Any) object).getObject() == null))
            value = null;
        else if (clazz.equals(Object.class))
        {
            if (object instanceof Any)
                object = ((Any) object).getObject();
            value = object;
        }
        else if (clazz.equals(boolean.class) || clazz.equals(Boolean.class))
            value = Boolean.valueOf(AnyConverter.toBoolean(object));
        else if (clazz.equals(char.class) || clazz.equals(Character.class))
            value = Character.valueOf(AnyConverter.toChar(object));
        else if (clazz.equals(byte.class) || clazz.equals(Byte.class))
            value = Byte.valueOf(AnyConverter.toByte(object));
        else if (clazz.equals(short.class) || clazz.equals(Short.class))
            value = Short.valueOf(AnyConverter.toShort(object));
        else if (clazz.equals(int.class) || clazz.equals(Integer.class))
            value = Integer.valueOf(AnyConverter.toInt(object));
        else if (clazz.equals(long.class) || clazz.equals(Long.class))
            value = Long.valueOf(AnyConverter.toLong(object));
        else if (clazz.equals(float.class) || clazz.equals(Float.class))
            value = Float.valueOf(AnyConverter.toFloat(object));
        else if (clazz.equals(double.class) || clazz.equals(Double.class))
            value = Double.valueOf(AnyConverter.toDouble(object));
        else if (clazz.equals(String.class))
            value = AnyConverter.toString(object);
        else if (clazz.isArray())
            value = AnyConverter.toArray(object);
        else if (clazz.equals(Type.class))
            value = AnyConverter.toType(object);
        else if (XInterface.class.isAssignableFrom(clazz))
            value = AnyConverter.toObject(new Type(clazz), object);
        else if (com.sun.star.uno.Enum.class.isAssignableFrom(clazz))
            value = AnyConverter.toObject(new Type(clazz), object);
        else
            throw new com.sun.star.lang.IllegalArgumentException("Could not convert the argument");
        return value;
    }


    @Override
    public void setPropertyValueNoBroadcast(Property property,
                                            Object value)
    throws WrappedTargetException
    {
        String id = (String) getPropertyId(property);
        if (id != null)
        {
            if (id.startsWith(m_fieldPrefix))
                _setField(property, value, id);
            else
                _setMethod(property, value, id);
        }
    }

    public void _setField(Property property,
                          Object value,
                          String id)
    throws WrappedTargetException
    {
        try
        {    
            Field field = _getField(this.getClass(), id);
            if (field != null)
            {
                field.setAccessible(true);
                field.set(this, value);
            }
            else
                System.out.println("beans.PropertySet._setField() 1 ********************************** " + id);
        }
        catch(java.lang.IllegalAccessException e)
        {
            System.out.println("beans.PropertySet._setField() 2 ********************************** " + id);
            throw new WrappedTargetException(e, "PropertySet.setPropertyValueNoBroadcast", this, e);
        }
    }
    
        
    public void _setMethod(Property property,
                           Object value,
                           String id)
    throws WrappedTargetException
    {
        Method method = null;
        String setter = m_setterPrefix + id;
        try 
        {
            method = _getSetter(this.getClass(), setter, property.Type.getZClass());
            if (method != null)
            {
                method.setAccessible(true);
                method.invoke(this, value);
            }
            else
                System.out.println("beans.PropertySet._setMethod() 1 ********************************** " + setter);
        }
        catch (SecurityException | IllegalAccessException | IllegalArgumentException | InvocationTargetException e)
        {
            System.out.println("beans.PropertySet._setMethod() 2 ********************************** " + setter);
            String msg = e.getMessage();
            throw new WrappedTargetException(msg);
        }
    }

    @Override
    public Object getPropertyValue(Property property)
    {
        Object value = null;
        String id = (String) getPropertyId(property);
        if (id != null)
        {
            if (id.startsWith(m_fieldPrefix))
                value = _getField(property, id);
            else
                value = _getMethod(property, id);
        }
        return value;
    }

    public Object _getField(Property property,
                            String id)
    {
        Object value = null;
        try
        {
            Field field = _getField(this.getClass(), id);
            if (field != null)
            {
                field.setAccessible(true);
                value = field.get(this);
            }
            else
                System.out.println("beans.PropertySet._getField() 1 ********************************** " + id);
        }
        catch(java.lang.IllegalAccessException e)
        {
            System.out.println("beans.PropertySet._getField() 2 ********************************** " + id);
            e.printStackTrace();
        }
        return value;
    }

    public Object _getMethod(Property property,
                             String id)
        {
        Object value = null;
        Method method = null;
        String getter = m_getterPrefix + id;
        try
        {
            method = _getGetter(this.getClass(), getter);
            if (method != null)
            {
                method.setAccessible(true);
                value = method.invoke(this);
            }
            else
                System.out.println("beans.PropertySet._getMethod() 1 ********************************** " + getter);
        }
        catch (SecurityException | IllegalAccessException | InvocationTargetException e)
        {
            System.out.println("beans.PropertySet._getMethod() 2 ********************************** " + getter);
            e.printStackTrace();
        }
        return value;
    }

    private static Field _getField(Class<?> clazz, String name)
    {
        Field field = null;
        while (clazz != null && field == null) {
            try {
                field = clazz.getDeclaredField(name);
            }
            catch (NoSuchFieldException e) {
                clazz = clazz.getSuperclass();
            }
        }
        return field;
    }

    private static Method _getGetter(Class<?> clazz, String name)
    {
        Method method = null;
        while (clazz != null && method == null) {
            try {
                method = clazz.getDeclaredMethod(name);
            }
            catch (NoSuchMethodException e) {
                clazz = clazz.getSuperclass();
            }
        }
        return method;
    }

    private static Method _getSetter(Class<?> clazz, String name, Class<?> type)
    {
        Method method = null;
        while (clazz != null && method == null) {
            try {
                method = clazz.getDeclaredMethod(name, type);
            }
            catch (NoSuchMethodException e) {
                clazz = clazz.getSuperclass();
            }
        }
        return method;
    }

/*  @Override
    public synchronized com.sun.star.beans.XPropertySetInfo getPropertySetInfo()
    {
        if (propertySetInfo == null)
            propertySetInfo = new PropertySetInfo(this.getClass().getName());
        return propertySetInfo;
    }


    @SuppressWarnings("unused")
    private class PropertySetInfo implements XPropertySetInfo
    {
        private final String m_class;
        public PropertySetInfo(String clazz)
        {
            m_class = clazz;
        }
        public com.sun.star.beans.Property[] getProperties()
        {
            System.out.println("beans.PropertySet.getProperties() 1 ");
            return PropertySet.this.getProperties();
        }

        public com.sun.star.beans.Property getPropertyByName(String name) throws UnknownPropertyException
        {
            System.out.println("beans.PropertySet.getPropertyByName() 1 : Class: " + m_class + " Name: " + name);
            return getProperty(name);
        }

        public boolean hasPropertyByName(String name)
        {
            System.out.println("beans.PropertySet.hasPropertyByName() 1 : Class: " + m_class + " Name: " + name);
            return getProperty(name) != null;
        }
    } */


}
