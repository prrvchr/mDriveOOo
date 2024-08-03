package io.github.prrvchr.uno.helper;

import java.io.PrintWriter;
import java.io.StringWriter;
import java.lang.IllegalAccessException;
import java.net.URL;
import java.net.URLClassLoader;
import java.time.OffsetDateTime;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Map;

import com.sun.star.beans.Property;
import com.sun.star.beans.NamedValue;
import com.sun.star.beans.PropertyAttribute;
import com.sun.star.beans.PropertyValue;
import com.sun.star.beans.XIntrospection;
import com.sun.star.beans.XPropertySet;
import com.sun.star.beans.XPropertySetInfo;
import com.sun.star.container.NoSuchElementException;
import com.sun.star.container.XHierarchicalNameAccess;
import com.sun.star.deployment.XPackageInformationProvider;
import com.sun.star.i18n.XLocaleData;
import com.sun.star.lang.IllegalArgumentException;
import com.sun.star.lang.Locale;
import com.sun.star.lang.WrappedTargetException;
import com.sun.star.lang.XComponent;
import com.sun.star.lang.XMultiComponentFactory;
import com.sun.star.lang.XMultiServiceFactory;
import com.sun.star.lang.XServiceInfo;
import com.sun.star.logging.LogLevel;
import com.sun.star.resource.XStringResourceResolver;
import com.sun.star.sdbc.SQLException;
import com.sun.star.sdbc.XRow;
import com.sun.star.uno.AnyConverter;
import com.sun.star.uno.Exception;
import com.sun.star.uno.RuntimeException;
import com.sun.star.uno.Type;
import com.sun.star.uno.UnoRuntime;
import com.sun.star.uno.XComponentContext;
import com.sun.star.uno.XInterface;

import io.github.prrvchr.css.util.Date;
import io.github.prrvchr.css.util.DateTime;
import io.github.prrvchr.css.util.DateTimeWithTimezone;
import io.github.prrvchr.css.util.Time;
import io.github.prrvchr.css.util.TimeWithTimezone;


public class UnoHelper
{

    public static void ensure(boolean condition, String message) {
        ensure(condition, message, null);
    }

    public static void ensure(Object reference, String message) {
        ensure(reference, message, null);
    }

    public static void ensure(boolean condition, String message, EventLogger logger) {
        if (!condition) {
            RuntimeException error = new com.sun.star.uno.RuntimeException(message);
            if (logger != null) {
                logger.logp(LogLevel.SEVERE, error);
            }
            throw error;
        }
    }

    public static void ensure(Object reference, String message, EventLogger logger) {
        if (reference == null) {
            RuntimeException error = new com.sun.star.uno.RuntimeException(message);
            if (logger != null) {
                logger.logp(LogLevel.SEVERE, error);
            }
            throw error;
        }
    }

    public static void disposeComponent(final Object object) {
        final XComponent component = UnoRuntime.queryInterface(XComponent.class, object);
        if (component != null) {
            component.dispose();
        }
    }

    public static void copyProperties(final XPropertySet src,
                                      final XPropertySet dst)
    {
        if (src == null || dst == null) {
            return;
        }
        
        XPropertySetInfo srcPropertySetInfo = src.getPropertySetInfo();
        XPropertySetInfo dstPropertySetInfo = dst.getPropertySetInfo();
        
        for (Property srcProperty : srcPropertySetInfo.getProperties()) {
            if (dstPropertySetInfo.hasPropertyByName(srcProperty.Name)) {
                try {
                    Property dstProperty = dstPropertySetInfo.getPropertyByName(srcProperty.Name);
                    if ((dstProperty.Attributes & PropertyAttribute.READONLY) == 0) {
                        Object value = src.getPropertyValue(srcProperty.Name);
                        if ((dstProperty.Attributes & PropertyAttribute.MAYBEVOID) == 0 || value != null) {
                            dst.setPropertyValue(srcProperty.Name, value);
                        }
                    }
                }
                catch (Exception e) {
                    String error = "Could not copy property '" + srcProperty.Name + "' to the destination set";
                    XServiceInfo serviceInfo = UnoRuntime.queryInterface(XServiceInfo.class, dst);
                    if (serviceInfo != null) {
                        error += " (a '" + serviceInfo.getImplementationName() + "' implementation)";
                    }
                    System.out.println("UnoHelper.copyProperties() ERROR: " + error);
                }
            }
        }
    }

    public static void disposeComponent(final XComponent component)
    {
        if (component != null) {
            component.dispose();
        }
    }

    public static Object createService(XComponentContext context,
                                       String name)
    {
        Object service = null;
        try {
            XMultiComponentFactory manager = context.getServiceManager();
            service = manager.createInstanceWithContext(name, context);
        }
        catch (java.lang.Exception e) {
            e.printStackTrace();
        }
        return service;
    }

    public static Object createService(XComponentContext context,
                                       String name,
                                       Object... arguments)
    {
        Object service = null;
        try {
            XMultiComponentFactory manager = context.getServiceManager();
            service = manager.createInstanceWithArgumentsAndContext(name, arguments, context);
        }
        catch (java.lang.Exception e) {
            e.printStackTrace();
        }
        return service;
    }

    public static XMultiServiceFactory getMultiServiceFactory(XComponentContext context,
                                                              String service)
    {
        return (XMultiServiceFactory) UnoRuntime.queryInterface(XMultiServiceFactory.class, createService(context, service));
    }

    public static XHierarchicalNameAccess getConfiguration(final XComponentContext context,
                                                           final String path)
        throws Exception
    {
        return getConfiguration(context, path, false, null);
    }

    public static XHierarchicalNameAccess getConfiguration(final XComponentContext context,
                                                           final String path,
                                                           final boolean update)
        throws Exception
    {
        return getConfiguration(context, path, update, null);
    }

    public static XHierarchicalNameAccess getConfiguration(final XComponentContext context,
                                                           final String path,
                                                           final boolean update,
                                                           final String language)
        throws Exception
    {
        String service = "com.sun.star.configuration.Configuration";
        final XMultiServiceFactory provider = getMultiServiceFactory(context, service + "Provider");
        ArrayList<NamedValue> arguments = new ArrayList<>(Arrays.asList(new NamedValue("nodepath", path)));
        if (language != null) {
            arguments.add(new NamedValue("Locale", language));
        }
        service += update ? "UpdateAccess" : "Access";
        Object config = provider.createInstanceWithArguments(service, arguments.toArray());
        return (XHierarchicalNameAccess) UnoRuntime.queryInterface(XHierarchicalNameAccess.class, config);
    }

    public static String getPackageLocation(XComponentContext context, String identifier, String path)
    {
        String location = getPackageLocation(context, identifier);
        return location + "/" + path + "/";
    }

    public static String getPackageLocation(XComponentContext context, String identifier)
    {
        String location = "";
        XPackageInformationProvider provider = null;
        String service = "/singletons/com.sun.star.deployment.PackageInformationProvider";
        provider = (XPackageInformationProvider) UnoRuntime.queryInterface(XPackageInformationProvider.class, context.getValueByName(service));
        if (provider != null) {
            location = provider.getPackageLocation(identifier);
        }
        return location;
    }

    public static Locale getCurrentLocale(XComponentContext context)
        throws NoSuchElementException,
               Exception
    {
        String nodepath = "/org.openoffice.Setup/L10N";
        String config = "";
        config = (String) getConfiguration(context, nodepath).getByHierarchicalName("ooLocale");
        String[] parts = config.split("-");
        Locale locale = new Locale(parts[0], "", "");
        if (parts.length > 1) {
            locale.Country = parts[1];
        }
        else {
            Object service = createService(context, "com.sun.star.i18n.LocaleData");
            XLocaleData data = (XLocaleData) UnoRuntime.queryInterface(XLocaleData.class, service);
            locale.Country = data.getLanguageCountryInfo(locale).Country;
        }
        return locale;
    }

    public static XStringResourceResolver getResourceResolver(XComponentContext ctx,
                                                              String identifier,
                                                              String path,
                                                              String filename)
        throws NoSuchElementException,
               Exception
    {
        Locale locale = getCurrentLocale(ctx);
        return getResourceResolver(ctx, identifier, path, filename, locale);
    }

    public static XStringResourceResolver getResourceResolver(XComponentContext ctx,
                                                              String identifier,
                                                              String path,
                                                              String filename,
                                                              Locale locale)
    {
        String name = "com.sun.star.resource.StringResourceWithLocation";
        String location = getPackageLocation(ctx, identifier, path);
        Object service = createService(ctx, name, location, true, locale, filename, "", null);
        return (XStringResourceResolver) UnoRuntime.queryInterface(XStringResourceResolver.class, service);
    }

    public static URL getDriverURL(String location)
    {
        URL url = null;
        try {
            url = new URL("jar:" + location + "!/");
        }
        catch (java.lang.Exception e) {
            e.printStackTrace();
        }
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

    public static String getDefaultPropertyValue(PropertyValue[] properties, String name, String value)
        throws IllegalArgumentException
    {
        for (PropertyValue property : properties) {
            if (property.Name.equals(name)) {
                return AnyConverter.toString(property.Value);
            }
        }
        return value;
    }

    public static boolean getDefaultPropertyValue(PropertyValue[] properties, String name, boolean value)
        throws IllegalArgumentException
    {
        for (PropertyValue property : properties) {
            if (property.Name.equals(name)) {
                return AnyConverter.toBoolean(property.Value);
            }
        }
        return value;
    }

    public static Object getDefaultDriverInfo(PropertyValue[] properties, String name, Object value)
        throws IllegalArgumentException
    {
        for (PropertyValue property : properties) {
            if (property.Name.equals(name)) {
                return property.Value;
            }
        }
        return value;
    }

    public static Property getProperty(String name, String type)
    {
        short attributes = 0;
        return getProperty(name, type, attributes);
    }

    public static Property getProperty(String name, int handle, String type)
    {
        short attributes = 0;
        return getProperty(name, handle, type, attributes);
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

    public static String getStackTrace(Throwable e)
    {
        StringWriter sw = new StringWriter();
        PrintWriter pw = new PrintWriter(sw);
        e.printStackTrace(pw);
        return sw.toString();
    }

    public static WrappedTargetException getWrappedException(java.lang.Exception e)
    {
        WrappedTargetException exception = null;
        if (e != null) {
            Exception ex = new Exception(e.getMessage());
            exception = getWrappedException(ex);
        }
        return exception;
    }

    public static WrappedTargetException getWrappedException(Exception e)
    {
        WrappedTargetException exception = null;
        if (e != null) {
            exception = new WrappedTargetException(e.getMessage());
            exception.Context = e.Context;
            exception.TargetException = e;
        }
        return exception;
    }

    public static java.sql.SQLException getSQLException(java.lang.Throwable e)
    {
        return new java.sql.SQLException(e.getLocalizedMessage(), e);
    }

    public static SQLException getSQLException(java.sql.SQLException e)
    {
        return getUnoSQLException(e.getLocalizedMessage());
    }

    public static SQLException getSQLException(Exception e, XInterface component)
    {
        SQLException exception = getUnoSQLException(e.getMessage());
        exception.Context = component;
        return exception;
    }

    public static SQLException getSQLException(java.sql.SQLException e, XInterface component)
    {
        SQLException exception = null;
        if (e != null) {
            exception = getUnoSQLException(e.getLocalizedMessage());
            exception.Context = component;
            String state = e.getSQLState();
            if (state != null) {
                exception.SQLState = state;
            }
            exception.ErrorCode = e.getErrorCode();
            SQLException ex = getNextSQLException(e.getNextException(), component);
            if (ex != null) {
                exception.NextException = ex;
            }
        }
        return exception;
    }

    private static SQLException getUnoSQLException(String msg)
    {
        return msg != null ? new SQLException(msg) : new SQLException();
    }

    public static SQLException getSQLException(java.lang.Exception e,
                                               XInterface component)
    {
        SQLException exception = getUnoSQLException(e.getMessage());
        exception.Context = component;
        return exception;
    }

    private static SQLException getNextSQLException(java.sql.SQLException e,
                                                    XInterface component)
    {
        SQLException exception = null;
        if (e != null) {
            exception = getSQLException(e, component);
        }
        return exception;
    }

    public static SQLException getLoggedSQLException(XInterface component,
                                                     ResourceBasedEventLogger logger,
                                                     java.sql.SQLException throwable)
    {
        
        SQLException exception = getSQLException(throwable, component);
        logger.log(LogLevel.SEVERE, throwable);
        return exception;
    }

    public static String getObjectString(Object object)
    {
        String value = null;
        if (AnyConverter.isString(object)) {
            value = AnyConverter.toString(object);
            System.out.println("UnoHelper.getObjectString() 1");
        }
        return value;
    }

    public static com.sun.star.util.Date getUnoDate(java.time.LocalDate date)
    {
        com.sun.star.util.Date value = new com.sun.star.util.Date();
        if (date != null) {
            value.Year = (short) date.getYear();
            value.Month = (short) date.getMonthValue();
            value.Day = (short) date.getDayOfMonth();
        }
        return value;
    }

    public static com.sun.star.util.Time getUnoTime(java.time.LocalTime time)
    {
        com.sun.star.util.Time value = new com.sun.star.util.Time();
        if (time != null) {
            value.Hours = (short) time.getHour();
            value.Minutes = (short) time.getMinute();
            value.Seconds = (short) time.getSecond();
            //value.NanoSeconds = time.getNano();
            //value.HundredthSeconds = 0;
        }
        return value;
    }

    public static com.sun.star.util.DateTime getUnoDateTime(java.time.LocalDateTime datetime)
    {
        com.sun.star.util.DateTime value = new com.sun.star.util.DateTime();
        if (datetime != null) {
            value.Year = (short) datetime.getYear();
            value.Month = (short) datetime.getMonthValue();
            value.Day = (short) datetime.getDayOfMonth();
            value.Hours = (short) datetime.getHour();
            value.Minutes = (short) datetime.getMinute();
            value.Seconds = (short) datetime.getSecond();
            //value.NanoSeconds = datetime.getNano();
            //value.HundredthSeconds = 0;
        }
        return value;
    }

    public static com.sun.star.util.TimeWithTimezone getUnoTimeWithTimezone(java.time.OffsetTime time)
    {
        com.sun.star.util.TimeWithTimezone value = new com.sun.star.util.TimeWithTimezone();
        if (time != null) {
            value.TimeInTZ = getUnoTime(time.toLocalTime());
            value.Timezone = getUnoTimezone(time.getOffset());
        }
        return value;
    }

    public static io.github.prrvchr.css.util.TimeWithTimezone getTimeWithTimezone(java.time.OffsetTime time)
    {
        io.github.prrvchr.css.util.TimeWithTimezone value = new io.github.prrvchr.css.util.TimeWithTimezone();
        if (time != null) {
            value.TimeInTZ = getTime(time.toLocalTime());
            value.Timezone = getUnoTimezone(time.getOffset());
        }
        return value;
    }

    public static io.github.prrvchr.css.util.Time getTime(java.time.LocalTime time)
    {
        io.github.prrvchr.css.util.Time value = new io.github.prrvchr.css.util.Time();
        if (time != null) {
            value.Hours = (short) time.getHour();
            value.Minutes = (short) time.getMinute();
            value.Seconds = (short) time.getSecond();
            value.NanoSeconds = time.getNano();
        }
        return value;
    }

    public static io.github.prrvchr.css.util.DateTimeWithTimezone getDateTimeWithTimezone(OffsetDateTime datetime)
    {
        io.github.prrvchr.css.util.DateTimeWithTimezone value = new io.github.prrvchr.css.util.DateTimeWithTimezone();
        if (datetime != null) {
            value.DateTimeInTZ = getDateTime(datetime.toLocalDateTime());
            value.Timezone = getUnoTimezone(datetime.getOffset());
        }
        return value;
    }

    public static io.github.prrvchr.css.util.DateTime getDateTime(java.time.LocalDateTime datetime)
    {
        io.github.prrvchr.css.util.DateTime value = new io.github.prrvchr.css.util.DateTime();
        if (datetime != null) {
            value.Year = (short) datetime.getYear();
            value.Month = (short) datetime.getMonthValue();
            value.Day = (short) datetime.getDayOfMonth();
            value.Hours = (short) datetime.getHour();
            value.Minutes = (short) datetime.getMinute();
            value.Seconds = (short) datetime.getSecond();
            value.NanoSeconds = datetime.getNano();
            value.IsUTC = false;
        }
        return value;
    }

    public static com.sun.star.util.DateTimeWithTimezone getUnoDateTimeWithTimezone(OffsetDateTime datetime)
    {
        com.sun.star.util.DateTimeWithTimezone value = new com.sun.star.util.DateTimeWithTimezone();
        if (datetime != null) {
            value.DateTimeInTZ = getUnoDateTime(datetime.toLocalDateTime());
            value.Timezone = getUnoTimezone(datetime.getOffset());
        }
        return value;
    }

    public static short getUnoTimezone(java.time.ZoneOffset offset)
    {
        return (short) (offset.getTotalSeconds() / 60);
    }

    public static java.time.LocalDate getJavaLocalDate(com.sun.star.util.Date date)
    {
        return java.time.LocalDate.of(date.Year, date.Month, date.Day);
    }

    public static java.time.LocalDate getJavaLocalDate(Date date)
    {
        return java.time.LocalDate.of(date.Year, date.Month, date.Day);
    }

    public static java.time.LocalTime getJavaLocalTime(com.sun.star.util.Time time)
    {
        //return java.time.LocalTime.of(time.Hours, time.Minutes, time.Seconds, time.NanoSeconds);
        return java.time.LocalTime.of(time.Hours, time.Minutes, time.Seconds);
    }

    public static java.time.LocalTime getJavaLocalTime(Time time)
    {
        return java.time.LocalTime.of(time.Hours, time.Minutes, time.Seconds, time.NanoSeconds);
    }

    public static java.time.LocalDateTime getJavaLocalDateTime(com.sun.star.util.DateTime timestamp)
    {
        //return java.time.LocalDateTime.of(timestamp.Year, timestamp.Month, timestamp.Day, timestamp.Hours, timestamp.Minutes, timestamp.Seconds, timestamp.NanoSeconds);
        return java.time.LocalDateTime.of(timestamp.Year, timestamp.Month, timestamp.Day, timestamp.Hours, timestamp.Minutes, timestamp.Seconds);
    }

    public static java.time.LocalDateTime getJavaLocalDateTime(DateTime timestamp)
    {
        return java.time.LocalDateTime.of(timestamp.Year, timestamp.Month, timestamp.Day, timestamp.Hours, timestamp.Minutes, timestamp.Seconds, timestamp.NanoSeconds);
    }

    public static java.time.ZoneOffset getJavaZoneOffset(int offset)
    {
        return java.time.ZoneOffset.ofTotalSeconds(offset * 60);
    }

    public static java.time.OffsetTime getJavaOffsetTime(com.sun.star.util.TimeWithTimezone time)
    {
        return java.time.OffsetTime.of(getJavaLocalTime(time.TimeInTZ), getJavaZoneOffset(time.Timezone));
    }

    public static java.time.OffsetTime getJavaOffsetTime(TimeWithTimezone time)
    {
        return java.time.OffsetTime.of(getJavaLocalTime(time.TimeInTZ), getJavaZoneOffset(time.Timezone));
    }

    public static OffsetDateTime getJavaOffsetDateTime(com.sun.star.util.DateTimeWithTimezone datetime)
    {
        return OffsetDateTime.of(getJavaLocalDateTime(datetime.DateTimeInTZ), getJavaZoneOffset(datetime.Timezone));
    }

    public static OffsetDateTime getJavaOffsetDateTime(DateTimeWithTimezone datetime)
    {
        return OffsetDateTime.of(getJavaLocalDateTime(datetime.DateTimeInTZ), getJavaZoneOffset(datetime.Timezone));
    }

    public static Object getObjectFromResult(java.sql.ResultSet result, int index)
    {
        Object value = null;
        try {
            value = result.getObject(index);
        }
        catch (java.sql.SQLException e) {
            e.getStackTrace();
        }
        return value;
    }

    public static String getResultSetValue(java.sql.ResultSet result, int index)
    {
        String value = null;
        try {
            value = result.getString(index);
        }
        catch (java.sql.SQLException e) {
            e.getStackTrace();
        }
        return value;
    }

    public static Object getResultValue(java.sql.ResultSet result, int index)
    {
        boolean retrieved = true;
        Object value = null;
        try {
            switch (result.getMetaData().getColumnType(index)) {
            case java.sql.Types.CHAR:
            case java.sql.Types.VARCHAR:
                value = result.getString(index);
                break;
            case java.sql.Types.BOOLEAN:
                value = result.getBoolean(index);
                break;
            case java.sql.Types.TINYINT:
                value = result.getByte(index);
                break;
            case java.sql.Types.SMALLINT:
                value = result.getShort(index);
                break;
            case java.sql.Types.INTEGER:
                value = result.getInt(index);
                break;
            case java.sql.Types.BIGINT:
                value = result.getLong(index);
                break;
            case java.sql.Types.FLOAT:
                value = result.getFloat(index);
                break;
            case java.sql.Types.DOUBLE:
                value = result.getDouble(index);
                break;
            case java.sql.Types.TIMESTAMP:
                value = result.getTimestamp(index);
                break;
            case java.sql.Types.TIME:
                value = result.getTime(index);
                break;
            case java.sql.Types.DATE:
                value = result.getDate(index);
                break;
            case java.sql.Types.BINARY:
                value = result.getBytes(index);
                break;
            case java.sql.Types.TIME_WITH_TIMEZONE:
            case java.sql.Types.TIMESTAMP_WITH_TIMEZONE:
                value = result.getObject(index);
                break;
            default:
                retrieved = false;
            }
            if(retrieved && result.wasNull()) value = null;
        }
        catch (java.sql.SQLException e) {
            e.getStackTrace();
        }
        return value;
    }

    public static Object getRowValue(XRow row, int dbtype, int index)
       throws SQLException
    {
        return getRowValue(row, dbtype, index, null);
    }

    public static Object getRowValue(XRow row, int dbtype, int index, Object value)
        throws SQLException
    {
        boolean retrieved = true;
        switch (dbtype) {
        case java.sql.Types.CHAR:
        case java.sql.Types.VARCHAR:
            value = row.getString(index);
            break;
        case java.sql.Types.BOOLEAN:
            value = row.getBoolean(index);
            break;
        case java.sql.Types.TINYINT:
            value = row.getByte(index);
            break;
        case java.sql.Types.SMALLINT:
            value = row.getShort(index);
            break;
        case java.sql.Types.INTEGER:
            value = row.getInt(index);
            break;
        case java.sql.Types.BIGINT:
            value = row.getLong(index);
            break;
        case java.sql.Types.FLOAT:
            value = row.getFloat(index);
            break;
        case java.sql.Types.DOUBLE:
            value = row.getDouble(index);
            break;
        case java.sql.Types.TIMESTAMP:
            value = row.getTimestamp(index);
            break;
        case java.sql.Types.TIME:
            value = row.getTime(index);
            break;
        case java.sql.Types.DATE:
            value = row.getDate(index);
            break;
        case java.sql.Types.BINARY:
            value = row.getBytes(index);
            break;
        case java.sql.Types.ARRAY:
            value = row.getArray(index);
            break;
        case java.sql.Types.TIME_WITH_TIMEZONE:
        case java.sql.Types.TIMESTAMP_WITH_TIMEZONE:
            value = row.getObject(index, null);
            break;
        default:
            retrieved = false;
        }
        if(retrieved && row.wasNull()) value = null;
        return value;
    }

    public static DateTimeWithTimezone currentDateTimeInTZ() 
    {
        return currentDateTimeInTZ(true);
    }

    public static DateTimeWithTimezone currentDateTimeInTZ(boolean utc) 
    {
        DateTimeWithTimezone dtz = new DateTimeWithTimezone();
        OffsetDateTime now = utc ? OffsetDateTime.now(java.time.ZoneOffset.UTC) : OffsetDateTime.now();
        dtz.DateTimeInTZ = _currentDateTime(now, utc);
        dtz.Timezone =  utc ? 0 : (short) (now.getOffset().getTotalSeconds() / 60);
        return dtz;
    }

    public static com.sun.star.util.DateTime currentUnoDateTime()
    {
        OffsetDateTime now = OffsetDateTime.now(java.time.ZoneOffset.UTC);
        com.sun.star.util.DateTime dt = new com.sun.star.util.DateTime();
        dt.Year = (short) now.getYear();
        dt.Month = (short) now.getMonthValue();
        dt.Day = (short) now.getDayOfMonth();
        dt.Hours = (short) now.getHour();
        dt.Minutes = (short) now.getMinute();
        dt.Seconds = (short) now.getSecond();
        return dt;
    }

    public static DateTime currentDateTime(boolean utc)
    {
        OffsetDateTime now = utc ? OffsetDateTime.now(java.time.ZoneOffset.UTC) : OffsetDateTime.now();
        return _currentDateTime(now, utc);
    }

    private static DateTime _currentDateTime(OffsetDateTime now,
                                             boolean utc)
    {
        DateTime dt = new DateTime();
        dt.Year = (short) now.getYear();
        dt.Month = (short) now.getMonthValue();
        dt.Day = (short) now.getDayOfMonth();
        dt.Hours = (short) now.getHour();
        dt.Minutes = (short) now.getMinute();
        dt.Seconds = (short) now.getSecond();
        dt.NanoSeconds = now.getNano();
        dt.IsUTC = utc;
        return dt;
    }

    public static Integer getConstantValue(Class<?> clazz, String name)
    throws java.sql.SQLException
    {
        int value = 0;
        if (name != null && !name.isBlank()) {
            try {
                value = (int) clazz.getDeclaredField(name).get(null);
            }
            catch (IllegalArgumentException | IllegalAccessException | NoSuchFieldException | SecurityException e) {
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
        if (maps.containsKey(type)) {
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
        for (URL url : urls) {
            buffer.append(url.getFile());
            buffer.append(System.getProperty("path.separator"));
        }
        return buffer.toString();
    }

    public static void inspect(XComponentContext context, XInterface descriptor)
    {
        String service = "mytools.Mri";
        Object object = UnoHelper.createService(context, service);
        XIntrospection mri = (XIntrospection) UnoRuntime.queryInterface(XIntrospection.class, object);
        mri.inspect(descriptor);
    }

    public static String getConfigurationOption(XHierarchicalNameAccess config,
                                                String property,
                                                String value)
    {
        String option = value;
        try {
            if (config.hasByHierarchicalName(property)) {
                option = AnyConverter.toString(config.getByHierarchicalName(property));
            }
        }
        catch (Exception e) {
            e.printStackTrace();
        }
        return option;
    }

    public static boolean getConfigurationOption(XHierarchicalNameAccess config,
                                                 String property,
                                                 boolean value)
    {
        boolean option = value;
        try {
            if (config.hasByHierarchicalName(property)) {
                option = AnyConverter.toBoolean(config.getByHierarchicalName(property));
            }
        }
        catch (Exception e) {
            e.printStackTrace();
        }
        return option;
    }

    public static String getCaller()
    {
        StackWalker stackWalker = StackWalker.getInstance(StackWalker.Option.RETAIN_CLASS_REFERENCE);
        StackWalker.StackFrame frame = stackWalker.walk(stream1 -> stream1.skip(2)
                                                                          .findFirst()
                                                                          .orElse(null));
        if (frame == null) {
            return "caller: null";
        }
        return String.format("caller: %s#%s, %s",
                             frame.getClassName(),
                             frame.getMethodName(),
                             frame.getLineNumber());
    }

    public static void printStackTrace()
    {
        Thread thread = Thread.currentThread();
        StackTraceElement[] stackTrace = thread.getStackTrace();
        for (int i = 1; i < stackTrace.length; i++) {
             System.out.println(stackTrace[i].getClassName() + " " + stackTrace[i].getMethodName() + " " + stackTrace[i].getLineNumber());
        }
    }

}
