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

import java.util.Arrays;
import java.util.Comparator;
import java.util.HashMap;
import java.util.Iterator;
import java.util.Map;
import java.util.concurrent.atomic.AtomicInteger;

import com.sun.star.beans.Property;
import com.sun.star.beans.PropertyAttribute;
import com.sun.star.beans.PropertyChangeEvent;
import com.sun.star.beans.PropertyVetoException;
import com.sun.star.beans.UnknownPropertyException;
import com.sun.star.beans.XFastPropertySet;
import com.sun.star.beans.XMultiPropertySet;
import com.sun.star.beans.XPropertiesChangeListener;
import com.sun.star.beans.XPropertyChangeListener;
import com.sun.star.beans.XPropertySet;
import com.sun.star.beans.XPropertySetInfo;
import com.sun.star.beans.XVetoableChangeListener;
import com.sun.star.lang.EventObject;
import com.sun.star.lang.IllegalArgumentException;
import com.sun.star.lang.WrappedTargetException;
import com.sun.star.lib.uno.helper.InterfaceContainer;
import com.sun.star.lib.uno.helper.MultiTypeInterfaceContainer;
import com.sun.star.uno.Any;
import com.sun.star.uno.AnyConverter;
import com.sun.star.uno.Type;
import com.sun.star.uno.TypeClass;
import com.sun.star.uno.XInterface;

import io.github.prrvchr.uno.helper.UnoHelper;


public class PropertySetAdapter
    implements XPropertySet,
               XFastPropertySet,
               XMultiPropertySet
{

    private final Object lock;
    private final Object eventSource;
    // after registerListeners(), these are read-only:
    private final Map<String,PropertyData> propertiesByName = new HashMap<String,PropertyData>();
    private final Map<Integer,PropertyData> propertiesByHandle = new HashMap<Integer,PropertyData>();
    private AtomicInteger nextHandle = new AtomicInteger(1);
    // interface containers are locked internally:
    protected final MultiTypeInterfaceContainer boundListeners = new MultiTypeInterfaceContainer();
    protected final MultiTypeInterfaceContainer vetoableListeners = new MultiTypeInterfaceContainer();
    protected final InterfaceContainer propertiesChangeListeners = new InterfaceContainer();
    private final PropertySetInfo propertySetInfo = new PropertySetInfo();

    public static interface PropertyGetter
    {
        Object getValue() throws WrappedTargetException;
    }

    public static interface PropertySetter
    {
        void setValue(Object value) throws PropertyVetoException, IllegalArgumentException, WrappedTargetException;
    }

    private static class PropertyData
    {
        Property property;
        PropertyGetter getter;
        PropertySetter setter;
        
        PropertyData(Property property, PropertyGetter getter, PropertySetter setter)
        {
            this.property = property;
            this.getter = getter;
            this.setter = setter;
        }
    }

    private static final Comparator<Property> propertyNameComparator = new Comparator<Property>()
    {
        @Override
        public int compare(Property first,
                           Property second)
        {
            return first.Name.compareTo(second.Name);
        }
    };

    private class PropertySetInfo implements XPropertySetInfo
    {
        @Override
        public Property[] getProperties()
        {
            Property[] properties = new Property[propertiesByName.size()];
            int next = 0;
            for (Map.Entry<String, PropertyData> entry : propertiesByName.entrySet()) {
                properties[next++] = entry.getValue().property;
            }
            Arrays.sort(properties, propertyNameComparator);
            return properties;
        }

        @Override
        public Property getPropertyByName(String propertyName)
            throws UnknownPropertyException
        {
            PropertyData propertyData = getPropertyData(propertyName);
            return propertyData.property;
        }

        @Override
        public boolean hasPropertyByName(String name)
        {
            boolean value = propertiesByName.containsKey(name);
            if (!value) {
                System.out.println("beans.PropertySetAdapter.hasPropertyByName() ERROR *******************************************\n" + lock.getClass().getName() + " : " + name);
            }
            return value;
        }
    }

    /**
     * Creates a new instance.
     * @param lock the lock that will be held while calling the getters and setters
     * @param eventSource the com.sun.star.lang.EventObject Source field, to use in events sent to listeners
     */
    public PropertySetAdapter(Object lock,
                              Object eventSource)
    {
        this.lock = lock;
        this.eventSource = eventSource;
    }

    public void dispose()
    {
        // Create an event with this as sender
        EventObject event = new EventObject(eventSource);
        
        // inform all listeners to release this object
        boundListeners.disposeAndClear(event);
        vetoableListeners.disposeAndClear(event);
    }

    public void registerProperty(String name,
                                 int handle,
                                 Type type,
                                 short attributes,
                                 PropertyGetter getter,
                                 PropertySetter setter)
    {
        Property property = new Property(name, handle, type, attributes);
        PropertyData data = new PropertyData(property, getter, setter);
        propertiesByName.put(name, data);
        propertiesByHandle.put(property.Handle, data);
    }

    public void registerProperty(String name,
                                 Type type,
                                 short attributes,
                                 PropertyGetter getter,
                                 PropertySetter setter)
    {
        int handle;
        // registerProperty() should only be called from one thread, but just in case:
        handle = nextHandle.getAndIncrement();
        registerProperty(name, handle, type, attributes, getter, setter);
    }

    @Override
    public void addPropertyChangeListener(String name,
                                          XPropertyChangeListener listener)
        throws UnknownPropertyException,
               WrappedTargetException
    {
        PropertyData data = getPropertyData(name);
        if ((data.property.Attributes & PropertyAttribute.BOUND) != 0) {
            boundListeners.addInterface(name, listener);
        } // else ignore silently
    }

    @Override
    public void addVetoableChangeListener(String name,
                                          XVetoableChangeListener listener)
        throws UnknownPropertyException,
               WrappedTargetException
    {
        PropertyData data = getPropertyData(name);
        if ((data.property.Attributes & PropertyAttribute.CONSTRAINED) != 0) {
            vetoableListeners.addInterface(name, listener);
        } // else ignore silently
    }

    @Override
    public void addPropertiesChangeListener(String[] names,
                                            XPropertiesChangeListener listener)
    {
        propertiesChangeListeners.add(listener);
    }

    @Override
    public XPropertySetInfo getPropertySetInfo()
    {
        return propertySetInfo;
    }

    private PropertyData getPropertyData(String name)
        throws UnknownPropertyException
    {
        PropertyData data = propertiesByName.get(name);
        if (data == null) {
            System.out.println("beans.PropertySetAdapter.getPropertyData() ERROR Property Name: " + name);
            throw new UnknownPropertyException(name);
        }
        return data;
    }

    private PropertyData getPropertyData(int handle)
        throws UnknownPropertyException
    {
        PropertyData data = propertiesByHandle.get(handle);
        if (data == null) {
            System.out.println("beans.PropertySetAdapter.getPropertyData() ERROR Property handle: " + handle);
            throw new UnknownPropertyException(Integer.toString(handle));
        }
        return data;
    }

    private Object getPropertyValue(PropertyData data)
        throws WrappedTargetException
    {
        Object value;
        synchronized (lock) {
            value = data.getter.getValue();
        }
        
        // null must not be returned. Either a void any is returned or an any containing
        // an interface type and a null reference.
        if (value == null) {
            if (data.property.Type.getTypeClass() == TypeClass.INTERFACE) {
                value = new Any(data.property.Type, null);
            }
            else {
                value = new Any(new Type(void.class), null);
            }
        }
        return value;
    }

    @Override
    public Object getPropertyValue(String name)
        throws UnknownPropertyException,
               WrappedTargetException
    {
        PropertyData propertyData = getPropertyData(name);
        return getPropertyValue(propertyData);
    }

    @Override
    public Object getFastPropertyValue(int handle)
        throws UnknownPropertyException,
               WrappedTargetException
    {

        PropertyData propertyData = getPropertyData(handle);
        return getPropertyValue(propertyData);
    }

    @Override
    public Object[] getPropertyValues(String[] names)
    {
        Object[] values = new Object[names.length];
        for (int i = 0; i < names.length; i++) {
            Object value = null;
            try {
                value = getPropertyValue(names[i]);
            }
            catch (UnknownPropertyException | WrappedTargetException e) {
                System.out.println("beans.PropertySetAdapter.getPropertyValues() ERROR\n" + UnoHelper.getStackTrace(e));
            }
            values[i] = value;
        }
        return values;
    }

    @Override
    public void removePropertyChangeListener(String name,
                                             XPropertyChangeListener listener)
        throws UnknownPropertyException,
               WrappedTargetException
    {
        // check existence:
        getPropertyData(name);
        boundListeners.removeInterface(name, listener);
    }

    @Override
    public synchronized void removeVetoableChangeListener(String name,
                                                          XVetoableChangeListener listener)
        throws UnknownPropertyException,
               WrappedTargetException
    {
        // check existence:
        getPropertyData(name);
        vetoableListeners.removeInterface(name, listener);
    }

    @Override
    public void removePropertiesChangeListener(XPropertiesChangeListener listener)
    {
        propertiesChangeListeners.remove(listener);
    }

    @Override
    public void setPropertyValue(String name,
                                 Object value)
        throws UnknownPropertyException,
               PropertyVetoException,
               IllegalArgumentException,
               WrappedTargetException
    {
        PropertyData propertyData = getPropertyData(name);
        setPropertyValue(propertyData, value);
    }

    @Override
    public void setFastPropertyValue(int handle,
                                     Object value)
        throws UnknownPropertyException,
               PropertyVetoException,
               IllegalArgumentException,
               WrappedTargetException
    {
        PropertyData propertyData = getPropertyData(handle);
        setPropertyValue(propertyData, value);
    }

    private void setPropertyValue(PropertyData data,
                                  Object value)
        throws UnknownPropertyException,
               PropertyVetoException,
               IllegalArgumentException,
               WrappedTargetException
    {
        if ((data.property.Attributes & PropertyAttribute.READONLY) != 0) {
            throw new PropertyVetoException();
        }
        // The value may be null only if MAYBEVOID attribute is set         
        boolean isvoid = false;
        if (value instanceof Any) {
            isvoid = ((Any) value).getObject() == null;
        }
        else {
            isvoid = value == null;
        }
        if (isvoid && (data.property.Attributes & PropertyAttribute.MAYBEVOID) == 0) { 
            throw new IllegalArgumentException("The property must have a value; the MAYBEVOID attribute is not set!");
        }

        // Check if the argument is allowed
        boolean isValueOk = false;
        if (value instanceof Any) {
            isValueOk = checkType(((Any) value).getObject());
        }
        else {
            isValueOk = checkType(value);
        }
        if (!isValueOk) {
            throw new IllegalArgumentException("No valid UNO type");
        }

        Object[] futureValue = new Object[] { AnyConverter.toObject(data.property.Type, value) };
        Object[] currentValue = new Object[] { getPropertyValue(data.property.Name) };
        Property[] properties = new Property[] { data.property };
        
        fire(properties, currentValue, futureValue, false);
        synchronized (lock) {
            data.setter.setValue(futureValue[0]);
        }
        fire(properties, currentValue, futureValue, true);
    }

    @Override
    public void setPropertyValues(String[] names,
                                  Object[] values)
        throws PropertyVetoException,
               IllegalArgumentException,
               WrappedTargetException
    {
        for (int i = 0; i < names.length; i++) {
            try {
                setPropertyValue(names[i], values[i]);
            }
            catch (UnknownPropertyException e) {
                continue;
            }
        }
    }

    private boolean checkType(Object obj) {
        if (obj == null ||
            obj instanceof Boolean ||
            obj instanceof Character ||
            obj instanceof Number ||
            obj instanceof String ||
            obj instanceof XInterface ||
            obj instanceof Type ||
            obj instanceof com.sun.star.uno.Enum ||
            obj.getClass().isArray())
            return true;
        return false;
    }

    @Override
    public void firePropertiesChangeEvent(String[] names,
                                          XPropertiesChangeListener listener)
    {
        PropertyChangeEvent[] events = new PropertyChangeEvent[names.length];
        int count = 0;
        for (int i = 0; i < names.length; i++) {
            try {
                PropertyData data = getPropertyData(names[i]);
                Object value = getPropertyValue(names[i]);
                events[count++] = new PropertyChangeEvent(eventSource, names[i],
                        false, data.property.Handle, value, value);
            }
            catch (UnknownPropertyException e) {
            }
            catch (WrappedTargetException e) {
            }
        }
        if (count > 0) {
            if (events.length != count) {
                PropertyChangeEvent[] tmp = new PropertyChangeEvent[count];
                System.arraycopy(events, 0, tmp, 0, count);
                events = tmp;
            }
            listener.propertiesChange(events);
        }
    }

    private void fire(Property[] properties,
                      Object[] oldvalues,
                      Object[] newvalues,
                      boolean changed)
        throws PropertyVetoException
    {
        PropertyChangeEvent[] events = new PropertyChangeEvent[properties.length];
        int count = 0;
        for (int i = 0; i < properties.length; i++) {
            if ((!changed && (properties[i].Attributes & PropertyAttribute.CONSTRAINED) != 0) ||
                    (changed && (properties[i].Attributes & PropertyAttribute.BOUND) != 0)) {
                events[count++] = new PropertyChangeEvent(
                        eventSource, properties[i].Name, false, properties[i].Handle, oldvalues[i], newvalues[i]);
            }
        }
        for (int i = 0; i < count; i++) {
            fireListeners(changed, events[i].PropertyName, events[i]);
            fireListeners(changed, "", events[i]);
        }
        if (changed && count > 0) {
            if (count != events.length) {
                PropertyChangeEvent[] tmp = new PropertyChangeEvent[count];
                System.arraycopy(events, 0, tmp, 0, count);
                events = tmp;
            }
            for (Iterator<?> it = propertiesChangeListeners.iterator(); it.hasNext();) {
                XPropertiesChangeListener listener = (XPropertiesChangeListener) it.next();
                listener.propertiesChange(events);
            }
        }
    }

    private void fireListeners(boolean changed,
                               String key,
                               PropertyChangeEvent event)
        throws PropertyVetoException
    {
        InterfaceContainer listeners;
        if (changed) {
            listeners = boundListeners.getContainer(key);
        }
        else {
            listeners = vetoableListeners.getContainer(key);
        }
        if (listeners != null) {
            Iterator<?> it = listeners.iterator();
            while (it.hasNext()) {
                Object listener = it.next();
                if (changed) {
                    ((XPropertyChangeListener)listener).propertyChange(event);
                }
                else {
                    ((XVetoableChangeListener)listener).vetoableChange(event);
                }
            }
        }
    }


}
