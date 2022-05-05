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

import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.LineNumberReader;
import java.lang.reflect.Method;
import java.util.ArrayList;

import com.sun.star.lang.XSingleComponentFactory;
import com.sun.star.registry.XRegistryKey;

/**
 * Component main registration class.
 * 
 * <p><strong>This class should not be modified.</strong></p>
 * 
 * @author Cedric Bosdonnat aka. cedricbosdo
 *
 */
public class RegistrationHelper
{

    /**
    * Get a component factory for the implementations handled by this class.
    *
    * <p>This method calls all the methods of the same name from the classes listed
    * in the <code>RegistrationHandler.classes</code> file. <strong>This method
    * should not be modified.</strong></p>
    *
    * @param pImplementationName the name of the implementation to create.
    *
    * @return the factory which can create the implementation.
    */

    public static XSingleComponentFactory __getComponentFactory(final InputStream in,
                                                                final String name)
    {
        XSingleComponentFactory factory = null;
        final Class<?>[] classes = _findServicesImplementationClasses(in);
        int i = 0;
        while (i < classes.length && factory == null)
        {
            final Class<?> clazz = classes[i];
            if (name.equals(clazz.getCanonicalName()))
            {
                try
                {
                    final Class<?>[] types = new Class[]{String.class};
                    final Method method = clazz.getMethod("__getComponentFactory", types);
                    final Object object = method.invoke(null, name);
                    factory = (XSingleComponentFactory)object;
                }
                catch (Exception e)
                {
                    // Nothing to do: skip
                    System.err.println("Error happened");
                    e.printStackTrace();
                }
            }
            i++;
        }
        return factory;
    }

    /**
    * Writes the services implementation informations to the UNO registry.
    *
    * <p>This method calls all the methods of the same name from the classes listed
    * in the <code>RegistrationHandler.classes</code> file. <strong>This method
    * should not be modified.</strong></p>
    *
    * @param pRegistryKey the root registry key where to write the informations.
    *
    * @return <code>true</code> if the informations have been successfully written
    * to the registry key, <code>false</code> otherwise.
    */

    public static boolean __writeRegistryServiceInfo(final InputStream in,
                                                     final XRegistryKey key)
    {
        final Class<?>[] classes = _findServicesImplementationClasses(in);
        boolean success = true;
        int i = 0;
        while (i < classes.length && success)
        {
            final Class<?> clazz = classes[i];
            try
            {
                final Class<?>[] types = new Class[]{XRegistryKey.class};
                final Method method = clazz.getMethod("__writeRegistryServiceInfo", types);
                final Object object = method.invoke(null, key);
                success = success && ((Boolean)object).booleanValue();
            } catch (Exception e)
            {
                success = false;
                e.printStackTrace();
            }
            i++;
        }
        return success;
    }

    /**
     * @return all the UNO implementation classes. 
     */

    private static Class<?>[] _findServicesImplementationClasses(final InputStream in)
    {
        final ArrayList<Class<?>> classes = new ArrayList<Class<?>>();
        final LineNumberReader reader = new LineNumberReader(new InputStreamReader(in));
        try {
            String line = reader.readLine();
            while (line != null) {
                if (!line.equals("")) {
                    line = line.trim();
                    try {
                        final Class<?> clazz = Class.forName(line);
                        final Class<?>[] rtypes = new Class[]{XRegistryKey.class};
                        final Class<?>[] ftypes = new Class[]{String.class};
                        final Method registry = clazz.getMethod("__writeRegistryServiceInfo", rtypes);
                        final Method factory = clazz.getMethod("__getComponentFactory", ftypes);
                        if (registry != null && factory != null) {
                            classes.add(clazz);
                        }
                    }
                    catch (LinkageError | ClassNotFoundException | NoSuchMethodException e) {
                        e.printStackTrace();
                    }
                }
                line = reader.readLine();
            }
        }
        catch (IOException e) {
            e.printStackTrace();
        }
        finally {
            try {
                reader.close();
                in.close();
            }
            catch (Exception e) {};
        }
        return classes.toArray(new Class[classes.size()]);
    }


}
