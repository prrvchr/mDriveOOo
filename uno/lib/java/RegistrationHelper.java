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
package io.github.prrvchr.uno;

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

	public static XSingleComponentFactory __getComponentFactory(InputStream in, String sImplementationName)
	{
		XSingleComponentFactory xFactory = null;
		@SuppressWarnings("rawtypes")
		Class[] classes = findServicesImplementationClasses(in);
		int i = 0;
		while (i < classes.length && xFactory == null)
		{
			@SuppressWarnings("rawtypes")
			Class clazz = classes[i];
			if (sImplementationName.equals(clazz.getCanonicalName()))
			{
				try
				{
					@SuppressWarnings("rawtypes")
					Class[] getTypes = new Class[]{String.class};
					@SuppressWarnings("unchecked")
					Method getFactoryMethod = clazz.getMethod("__getComponentFactory", getTypes);
					Object o = getFactoryMethod.invoke(null, sImplementationName);
					xFactory = (XSingleComponentFactory)o;
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
		return xFactory;
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

	public static boolean __writeRegistryServiceInfo(InputStream in, XRegistryKey xRegistryKey)
	{
		@SuppressWarnings("rawtypes")
		Class[] classes = findServicesImplementationClasses(in);
		boolean success = true;
		int i = 0;
		while (i < classes.length && success)
		{
			@SuppressWarnings("rawtypes")
			Class clazz = classes[i];
			try
			{
				@SuppressWarnings("rawtypes")
				Class[] writeTypes = new Class[]{XRegistryKey.class};
				@SuppressWarnings("unchecked")
				Method getFactoryMethod = clazz.getMethod("__writeRegistryServiceInfo", writeTypes);
				Object o = getFactoryMethod.invoke(null, xRegistryKey);
				success = success && ((Boolean)o).booleanValue();
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

	@SuppressWarnings("rawtypes")
	private static Class[] findServicesImplementationClasses(InputStream in)
	{
		ArrayList<Class> classes = new ArrayList<Class>();
		LineNumberReader reader = new LineNumberReader(new InputStreamReader(in));
		try
		{
			String line = reader.readLine();
			while (line != null)
			{
				if (!line.equals(""))
				{
					line = line.trim();
					try
					{
						Class clazz = Class.forName(line);
						Class[] writeTypes = new Class[]{XRegistryKey.class};
						Class[] getTypes = new Class[]{String.class};
						@SuppressWarnings("unchecked")
						Method writeRegMethod = clazz.getMethod("__writeRegistryServiceInfo", writeTypes);
						@SuppressWarnings("unchecked")
						Method getFactoryMethod = clazz.getMethod("__getComponentFactory", getTypes);
						if (writeRegMethod != null && getFactoryMethod != null)
						{
							classes.add(clazz);
						}
					}
					catch (Exception e)
					{
						e.printStackTrace();
					}
				}
				line = reader.readLine();
			}
		}
		catch (IOException e)
		{
			e.printStackTrace();
		}
		finally
		{
			try
			{
				reader.close();
				in.close();
			}
			catch (Exception e) {};
		}
		return classes.toArray(new Class[classes.size()]);
	}


}
