package io.github.prrvchr.uno.helper;

import java.lang.Exception;
import java.lang.IllegalAccessException;
import java.net.URL;
import java.net.URLClassLoader;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.LocalTime;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Map;

import com.sun.star.beans.Property;
import com.sun.star.beans.NamedValue;
import com.sun.star.beans.PropertyValue;
import com.sun.star.deployment.XPackageInformationProvider;
import com.sun.star.lang.IllegalArgumentException;
import com.sun.star.lang.XComponent;
import com.sun.star.lang.XMultiComponentFactory;
import com.sun.star.lang.XMultiServiceFactory;
import com.sun.star.sdbc.DriverPropertyInfo;
import com.sun.star.sdbc.SQLException;
import com.sun.star.uno.Any;
import com.sun.star.uno.AnyConverter;
import com.sun.star.uno.Type;
import com.sun.star.uno.UnoRuntime;
import com.sun.star.uno.XComponentContext;
import com.sun.star.uno.XInterface;
import com.sun.star.util.Date;
import com.sun.star.util.DateTime;
import com.sun.star.util.Time;


public class UnoHelper
{

    public static void disposeComponent(final XComponent component)
    {
        if (component != null) {
            component.dispose();
        }
    }

    public static Object createService(XComponentContext context,
                                       String identifier)
    {
        Object service = null;
        try
        {
            XMultiComponentFactory manager = context.getServiceManager();
            service = manager.createInstanceWithContext(identifier, context);
        }
        catch (Exception e) { e.printStackTrace(); }
        return service;
    }


    public static XMultiServiceFactory getMultiServiceFactory(XComponentContext context,
                                                              String service)
    {
        return (XMultiServiceFactory) UnoRuntime.queryInterface(XMultiServiceFactory.class, createService(context, service));
    }

    public static Object getConfiguration(final XComponentContext context,
                                          final String path)
        throws com.sun.star.uno.Exception
    {
        return getConfiguration(context, path, false, null);
    }

    public static Object getConfiguration(final XComponentContext context,
                                          final String path,
                                          final boolean update)
        throws com.sun.star.uno.Exception
    {
        return getConfiguration(context, path, update, null);
    }

    public static Object getConfiguration(final XComponentContext context,
                                          final String path,
                                          final boolean update,
                                          final String language)
        throws com.sun.star.uno.Exception
    {
        final String service = "com.sun.star.configuration.Configuration";
        final XMultiServiceFactory provider = getMultiServiceFactory(context, service + "Provider");
        ArrayList<NamedValue> arguments = new ArrayList<>(Arrays.asList(new NamedValue("nodepath", path)));
        if (language != null) {
            arguments.add(new NamedValue("Locale", language));
        }
        return provider.createInstanceWithArguments(service + (update ? "UpdateAccess" : "Access"), arguments.toArray());
    }



    public static String getPackageLocation(XComponentContext context, String identifier, String path)
    {
        String location = getPackageLocation(context, identifier);
        return location + "/" + path + "/";
    }


    public static String getPackageLocation(XComponentContext context, String identifier)
    {
        String location = "";
        XPackageInformationProvider xProvider = null;
        try
        {
            Object oProvider = context.getValueByName("/singletons/com.sun.star.deployment.PackageInformationProvider");
            xProvider = (XPackageInformationProvider) UnoRuntime.queryInterface(XPackageInformationProvider.class, oProvider);
        }
        catch (Exception e) { e.printStackTrace(); }
        if (xProvider != null) location = xProvider.getPackageLocation(identifier);
        return location;
    }


    public static URL getDriverURL(String location)
    {
        URL url = null;
        try
        {
            url = new URL("jar:" + location + "!/");
        }
        catch (Exception e) { e.printStackTrace(); }
        return url;
    }
    public static URL getDriverURL(String location, String jar)
    {
        return getDriverURL(location + jar);
    }

    public static URL getDriverURL(String location, String path, String jar)
    {
        return getDriverURL(location + "/" + path + "/" + jar);
    }


    public static DriverPropertyInfo[] getDriverPropertyInfos()
    {
        ArrayList<DriverPropertyInfo> infos = new ArrayList<>();
        DriverPropertyInfo info1 = getDriverInfo("AutoIncrementCreation",
                                                 "GENERATED BY DEFAULT AS IDENTITY");
        infos.add(0, info1);
        DriverPropertyInfo info2 = getDriverInfo("AutoRetrievingStatement",
                                                 "CALL IDENTITY()");
        infos.add(0, info2);
        int len = infos.size();
        return infos.toArray(new DriverPropertyInfo[len]);
    }


    public static DriverPropertyInfo getDriverInfo(String name, String value)
    {
        DriverPropertyInfo info = new DriverPropertyInfo();
        info.Name = name;
        info.Value = value;
        info.IsRequired = true;
        info.Choices = new String[0];
        return info;
    }

    public static String getDefaultPropertyValue(PropertyValue[] properties, String name, String value)
        throws IllegalArgumentException
    {
        for (PropertyValue property : properties) {
            if (property.Name.equals(name))
                return AnyConverter.toString(property.Value);
        }
        return value;
    }

    public static boolean getDefaultPropertyValue(PropertyValue[] properties, String name, boolean value)
        throws IllegalArgumentException
    {
        for (PropertyValue property : properties) {
            if (property.Name.equals(name))
                return AnyConverter.toBoolean(property.Value);
        }
        return value;
    }

    public static Object getDefaultDriverInfo(PropertyValue[] properties, String name, Object value)
        throws IllegalArgumentException
    {
        for (PropertyValue property : properties) {
            if (property.Name.equals(name))
                return property.Value;
        }
        return value;
    }


    
    public static Property getProperty(String name, String type)
    {
        short attributes = 0;
        return getProperty(name, type, attributes);
    }


    public static Property getProperty(String name, String type, short attributes)
    {
        int handle = -1;
        return getProperty(name, handle, type, attributes);
    }


    public static Property getProperty(String name, int handle, String type, short attributes)
    {
        Property property = new Property();
        property.Name = name;
        property.Handle = handle;
        property.Type = new Type(type);
        property.Attributes = attributes;
        return property;
    }

    public static java.sql.SQLException getSQLException(Exception e)
    {
        return new java.sql.SQLException(e.getMessage(), e);
    }
    
    
    public static SQLException getSQLException(java.sql.SQLException e, XInterface component)
    {
        SQLException exception = null;
        if (e != null)
        {
            exception = new SQLException(e.getMessage());
            exception.Context = component;
            exception.SQLState = e.getSQLState();
            exception.ErrorCode = e.getErrorCode();
            exception.NextException = _getNextSQLException(e.getNextException(), component);
        }
        return exception;
    }

    private static Object _getNextSQLException(java.sql.SQLException e, XInterface component)
    {
        Object exception = Any.VOID;
        if (e != null)
        {
            exception = getSQLException(e, component);
        }
        return exception;
    }

    public static String getObjectString(Object object)
    {
        String value = null;
        if (AnyConverter.isString(object))
        {
            value = AnyConverter.toString(object);
            System.out.println("UnoHelper.getObjectString() 1");
        }
        return value;
    }

    public static Date getUnoDate(java.sql.Date date)
    {
        Date value = new Date();
        if (date != null)
        {
            LocalDate localdate = date.toLocalDate();
            value.Year = (short) localdate.getYear();
            value.Month = (short) localdate.getMonthValue();
            value.Day = (short) localdate.getDayOfMonth();
        }
        return value;
    }


    public static java.sql.Date getJavaDate(Date date)
    {
        LocalDate localdate = LocalDate.of(date.Year, date.Month, date.Day);
        return java.sql.Date.valueOf(localdate);
    }


    public static Time getUnoTime(java.sql.Time time)
    {
        Time value = new Time();
        if (time != null)
        {
            LocalTime localtime = time.toLocalTime();
            value.Hours = (short) localtime.getHour();
            value.Minutes = (short) localtime.getMinute();
            value.Seconds = (short) localtime.getSecond();
            value.NanoSeconds = localtime.getNano();
            //value.HundredthSeconds = 0;
        }
        return value;
    }


    public static java.sql.Time getJavaTime(Time time)
    {
        LocalTime localtime = LocalTime.of(time.Hours, time.Minutes, time.Seconds, time.NanoSeconds);
        return java.sql.Time.valueOf(localtime);
    }


    public static DateTime getUnoDateTime(java.sql.Timestamp timestamp)
    {
        DateTime value = new DateTime();
        if (timestamp != null)
        {
            LocalDateTime localdatetime = timestamp.toLocalDateTime();
            value.Year = (short) localdatetime.getYear();
            value.Month = (short) localdatetime.getMonthValue();
            value.Day = (short) localdatetime.getDayOfMonth();
            value.Hours = (short) localdatetime.getHour();
            value.Minutes = (short) localdatetime.getMinute();
            value.Seconds = (short) localdatetime.getSecond();
            value.NanoSeconds = localdatetime.getNano();
            //value.HundredthSeconds = 0;
        }
        return value;
    }


    public static java.sql.Timestamp getJavaDateTime(DateTime timestamp)
    {
        LocalDateTime localdatetime = LocalDateTime.of(timestamp.Year, timestamp.Month, timestamp.Day, timestamp.Hours, timestamp.Minutes, timestamp.Seconds, timestamp.NanoSeconds);
        return java.sql.Timestamp.valueOf(localdatetime);
    }


    public static Object getObjectFromResult(java.sql.ResultSet result, int index)
    {
        Object value = null;
        try
        {
            value = result.getObject(index);
        }
        catch (java.sql.SQLException e) {e.getStackTrace();}
        return value;
    }


    public static String getResultSetValue(java.sql.ResultSet result, int index)
    {
        String value = null;
        try
        {
            value = result.getString(index);
        }
        catch (java.sql.SQLException e) {e.getStackTrace();}
        return value;
    }


    public static Object getValueFromResult(java.sql.ResultSet result, int index)
    {
        // TODO: 'TINYINT' is buggy: don't use it
        Object value = null;
        try
        {
            String dbtype = result.getMetaData().getColumnTypeName(index);
            if (dbtype == "VARCHAR")
                value = result.getString(index);
            else if (dbtype == "BOOLEAN")
                value = result.getBoolean(index);
            else if (dbtype == "TINYINT")
                value = result.getShort(index);
            else if (dbtype == "SMALLINT")
                value = result.getShort(index);
            else if (dbtype == "INTEGER")
                value = result.getInt(index);
            else if (dbtype == "BIGINT")
                value = result.getLong(index);
            else if (dbtype == "FLOAT")
                value = result.getFloat(index);
            else if (dbtype == "DOUBLE")
                value = result.getDouble(index);
            else if (dbtype == "TIMESTAMP")
                value = result.getTimestamp(index);
            else if (dbtype == "TIME")
                value = result.getTime(index);
            else if (dbtype == "DATE")
                value = result.getDate(index);
        }
        catch (java.sql.SQLException e)
        {
            e.getStackTrace();
        }
        return value;
    }


    public static Integer getConstantValue(Class<?> clazz, String name)
    throws java.sql.SQLException
    {
        int value = 0;
        if (name != null && !name.isBlank())
        {
            try
            {
                value = (int) clazz.getDeclaredField(name).get(null);
            }
            catch (IllegalArgumentException | IllegalAccessException | NoSuchFieldException | SecurityException e)
            {
                e.printStackTrace(System.out);
            }
        }
        return value;
    }


    public static int mapSQLDataType(int type)
    {
        Map<Integer, Integer> maps = Map.ofEntries(Map.entry(-16, -1),
                                                   Map.entry(-15, 1),
                                                   Map.entry(-9, 12),
                                                   Map.entry(-8, 4),
                                                   Map.entry(70, 1111),
                                                   Map.entry(2009, 1111),
                                                   Map.entry(2011, 2005),
                                                   Map.entry(2012, 2006),
                                                   Map.entry(2013, 12),
                                                   Map.entry(2014, 12));

        if (maps.containsKey(type))
        {
            System.out.println("UnoHelper.mapSQLDataType() Type: " + type);
            type = maps.get(type);
        }
        return type;
    }

    public static String mapSQLDataTypeName(String name, int type)
    {
        //String name = null;
        //Map<Integer, String> maps = _getUnoSQLDataType();
        //if (!maps.containsValue(name))
        //    if (maps.containsKey(type))
        //    {
        //        //name = maps.get(type);
        //        System.out.println("UnoHelper.mapSQLDataTypeName() 1 ************************* Name: " + name + " Type: " + type);
        //    }
        //    else
        //        System.out.println("UnoHelper.mapSQLDataTypeName() 2 ************************* Name: " + name + " Type: " + type);
        return name;
    }

    public static Map<Integer, String> _getUnoSQLDataType()
    {
        Map<Integer, String> maps = Map.ofEntries(Map.entry(-7, "BIT"),
                                                  Map.entry(-6, "TINYINT"),
                                                  Map.entry(-5, "BIGINT"),
                                                  Map.entry(-4, "LONGVARBINARY"),
                                                  Map.entry(-3, "VARBINARY"),
                                                  Map.entry(-2, "BINARY"),
                                                  Map.entry(-1, "LONGVARCHAR"),
                                                  Map.entry(0, "SQLNULL"),
                                                  Map.entry(1, "CHAR"),
                                                  Map.entry(2, "NUMERIC"),
                                                  Map.entry(3, "DECIMAL"),
                                                  Map.entry(4, "INTEGER"),
                                                  Map.entry(5, "SMALLINT"),
                                                  Map.entry(6, "FLOAT"),
                                                  Map.entry(7, "REAL"),
                                                  Map.entry(8, "DOUBLE"),
                                                  Map.entry(12, "VARCHAR"),
                                                  Map.entry(16, "BOOLEAN"),
                                                  Map.entry(91, "DATE"),
                                                  Map.entry(92, "TIME"),
                                                  Map.entry(93, "TIMESTAMP"),
                                                  Map.entry(1111, "OTHER"),
                                                  Map.entry(2000, "OBJECT"),
                                                  Map.entry(2001, "DISTINCT"),
                                                  Map.entry(2002, "STRUCT"),
                                                  Map.entry(2003, "ARRAY"),
                                                  Map.entry(2004, "BLOB"),
                                                  Map.entry(2005, "CLOB"),
                                                  Map.entry(2006, "REF"));
        return maps;
    }

    public static String getClassPath()
    {
        StringBuffer buffer = new StringBuffer();
        ClassLoader cl = ClassLoader.getSystemClassLoader();
        URL[] urls = ((URLClassLoader)cl).getURLs();
        for (URL url : urls)
        {
            buffer.append(url.getFile());
            buffer.append(System.getProperty("path.separator"));
        }
        return buffer.toString();
    }

}
