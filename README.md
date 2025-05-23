<!--
╔════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                    ║
║   Copyright (c) 2020-25 https://prrvchr.github.io                                  ║
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
-->
# [![mDriveOOo logo][1]][2] Documentation

**Ce [document][3] en français.**

**The use of this software subjects you to our [Terms Of Use][4] and [Data Protection Policy][5].**

# version [1.3.0][6]

## Introduction:

**mDriveOOo** is part of a [Suite][7] of [LibreOffice][8] ~~and/or [OpenOffice][9]~~ extensions allowing to offer you innovative services in these office suites.

This extension allows you to work in LibreOffice on your Microsoft oneDrive files, even while offline.  
It uses [Microsoft Graph API][10] to synchronize your remote Microsoft oneDrive files with the help of a local HsqlDB 2.7.2 database.  
This extension is seen by LibreOffice as a [Content Provider][11] responding to the URL: `vnd-microsoft://*`.

Being free software I encourage you:
- To duplicate its [source code][12].
- To make changes, corrections, improvements.
- To open [issue][13] if needed.

In short, to participate in the development of this extension.
Because it is together that we can make Free Software smarter.

___

## Requirement:

The mDriveOOo extension uses the OAuth2OOo extension to work.  
It must therefore meet the [requirement of the OAuth2OOo extension][14].

The mDriveOOo extension uses the jdbcDriverOOo extension to work.  
It must therefore meet the [requirement of the jdbcDriverOOo extension][15].  
Additionally, mDriveOOo requires the jdbcDriverOOo extension to be configured to provide `com.sun.star.sdb` as the API level, which is the default configuration.

___

## Installation:

It seems important that the file was not renamed when it was downloaded.  
If necessary, rename it before installing it.

- [![OAuth2OOo logo][17]][18] Install **[OAuth2OOo.oxt][19]** extension [![Version][20]][19]

    You must first install this extension, if it is not already installed.

- [![jdbcDriverOOo logo][21]][22] Install **[jdbcDriverOOo.oxt][23]** extension [![Version][24]][23]

    You must install this extension, if it is not already installed.

- ![mDriveOOo logo][25] Install **[mDriveOOo.oxt][26]** extension [![Version][27]][26]

Restart LibreOffice after installation.  
**Be careful, restarting LibreOffice may not be enough.**
- **On Windows** to ensure that LibreOffice restarts correctly, use Windows Task Manager to verify that no LibreOffice services are visible after LibreOffice shuts down (and kill it if so).
- **Under Linux or macOS** you can also ensure that LibreOffice restarts correctly, by launching it from a terminal with the command `soffice` and using the key combination `Ctrl + C` if after stopping LibreOffice, the terminal is not active (no command prompt).

___

## Use:

**Open your Microsoft OneDrive:**

In **File -> Open** enter in the first drop-down list:

- For a named Url: **vnd-microsoft://your_email@your_provider**  

or

- For an unnamed Url (anonymous): **vnd-microsoft:///**

And validate not by the **Open** button but by the **Enter** key.

If you don't give **your_email@your_provider**, you will be asked for...

Anonymous Urls allow you to remain anonymous (your account does not appear in the Url) while named Urls allow you to access several accounts simultaneously.

After authorizing the [OAuth2OOo][18] application to access your Microsoft OneDrive files, your OneDrive files should appear!!! normally  :wink:

___

## How to customize LibreOffice menus:

In order to be able to keep using system dialog windows for opening and saving files in LibreOffice, it is now possible to create custom menus for the commands: **Open Remote** and **Save Remote**.

In the **Menu** tab of the **Tools -> Customize** window, select **Macros** in **Category** to access the two macros: `OpenRemote` and `SaveRemote` under: **My Macros -> mDriveOOo**.  
You will first need to add the `OpenRemote` macro to one of the menus with the **Scope** set to **LibreOffice**, then you will need to open the applications (Writer, Calc, Draw...) possibly using a new document, and add the `OpenRemote` and `SaveRemote` macros with the **Scope** set to the application you want to add the menus to.

The `OpenRemote` macro supports any type of **Scope**, while the `SaveRemote` macro should only be assigned to application-type scopes because it requires a document to already be open in LibreOffice.  
This only needs to be done once for LibreOffice and each application, and unfortunately I haven't found anything simpler yet.

___

## How to build the extension:

Normally, the extension is created with Eclipse for Java and [LOEclipse][28]. To work around Eclipse, I modified LOEclipse to allow the extension to be created with Apache Ant.  
To create the mDriveOOo extension with the help of Apache Ant, you need to:
- Install the [Java SDK][29] version 8 or higher.
- Install [Apache Ant][30] version 1.10.0 or higher.
- Install [LibreOffice and its SDK][31] version 7.x or higher.
- Clone the [mDriveOOo][32] repository on GitHub into a folder.
- From this folder, move to the directory: `source/mDriveOOo/`
- In this directory, edit the file: `build.properties` so that the `office.install.dir` and `sdk.dir` properties point to the folders where LibreOffice and its SDK were installed, respectively.
- Start the archive creation process using the command: `ant`
- You will find the generated archive in the subfolder: `dist/`

___

## Has been tested with:

* LibreOffice 7.3.7.2 - Lubuntu 22.04 - Python version 3.10.12

* LibreOffice 7.5.4.2(x86) - Windows 10 - Python version 3.8.16 (under Lubuntu 22.04 / VirtualBox 6.1.38)

* LibreOffice 7.4.3.2(x64) - Windows 10(x64) - Python version 3.8.15 (under Lubuntu 22.04 / VirtualBox 6.1.38)

* LibreOffice 24.8.0.3 (x86_64) - Windows 10(x64) - Python version 3.9.19 (under Lubuntu 22.04 / VirtualBox 6.1.38)

* **Does not work with OpenOffice** see [bug 128569][33]. Having no solution, I encourage you to install **LibreOffice**.

I encourage you in case of problem :confused:  
to create an [issue][13]  
I will try to solve it :smile:

___

## Historical:

### What has been done for version 0.0.5:

- Integration and use of the new Hsqldb v2.5.1 system versioning.

- Writing of a new [Replicator][34] interface, launched in the background (python Thread) responsible for:

    - Perform the necessary procedures when creating a new user (initial Pull).

    - Carry out pulls regularly (every ten minutes) in order to synchronize any external changes (Pull all changes).

    - Replicate on demand all changes to the hsqldb 2.5.1 database using system versioning (Push all changes).

- Writing of a new [DataBase][35] interface, responsible for making all calls to the database.

- Setting up a cache on the Identifiers, see method: [_getUser()][36], allowing access to a Content (file or folder) without access to the database for subsequent calls.

- Management of duplicate file/folder names by [SQL Views][37]: Child, Twin, Uri, and Title generating unique names if duplicates names exist.  
Although this functionality is only needed for gDriveOOo, it is implemented globally...

- Many other fix...

### What has been done for version 0.0.6:

- Using new scheme: **vnd-microsoft://** as claimed by [draft-king-vnd-urlscheme-03.txt][38]

- Achievement of handling duplicate file/folder names by SQL views in HsqlDB:
  - A [**Twin**][39] view grouping all the duplicates by parent folder and ordering them by creation date, modification date.
  - A [**Uri**][40] view generating unique indexes for each duplicate.
  - A [**Title**][41] view generating unique names for each duplicate.
  - A recursive view [**Path**][42] to generate a unique path for each file / folder.

- Creation of a [Provider][43] able to respond to the two types of Urls supported (named and anonymous).  
  Regular expressions (regex), declared in the [UCB configuration file][44], are now used by OpenOffice/LibreOffice to send URLs to the appropriate ContentProvider.

- Use of the new UNO struct [DateTimeWithTimezone][45] provided by the extension [jdbcDriverOOo][22] since its version 0.0.4.  
  Although this struct already exists in LibreOffice, its creation was necessary in order to remain compatible with OpenOffice (see [Enhancement Request 128560][46]).

- Modification of the [Replicator][34] interface, in order to allow:
  - To choose the data synchronization order (local first then remote or vice versa).
  - Synchronization of local changes by atomic operations performed in chronological order to fully support offline work.  
  To do this, three SQL procedures [GetPushItems][47], [GetPushProperties][48] and [UpdatePushItems][49] are used for each user who has accessed his files / folders.

- Rewrite of the [options window][50] accessible by: **Tools -> Options -> Internet -> mDriveOOo** in order to allow:
  - Access to the two log files concerning the activities of the UCP and the data replicator.
  - Choice of synchronization order.
  - The modification of the interval between two synchronizations.
  - Access to the underlying HsqlDB 2.7.2 database managing your Microsoft oneDrive metadata.

- The presence or absence of a trailing slash in the Url is now supported.

- Many other fix...

### What has been done for version 1.0.0:

- Renamed OneDriveOOo extension to mDriveOOo.

### What has been done for version 1.0.1:

- Implementation of the management of shared files as requested in the request for improvement, see [issue 9][51].

- The name of the shared folder can be defined before any connection in: **Tools -> Options -> Internet -> mDriveOOo -> Handle shared documents in folder:**

- Many other fix...

### What has been done for version 1.0.2:

- The absence or obsolescence of the **OAuth2OOo** and/or **jdbcDriverOOo** extensions necessary for the proper functioning of **mDriveOOo** now displays an error message.

- Many other things...

### What has been done for version 1.0.3:

- Support for version **1.2.0** of the **OAuth2OOo** extension. Previous versions will not work with **OAuth2OOo** extension 1.2.0 or higher.

### What has been done for version 1.0.4:

- Support for version **1.2.1** of the **OAuth2OOo** extension. Previous versions will not work with **OAuth2OOo** extension 1.2.1 or higher.

### What has been done for version 1.0.5:

- Support for version **1.2.3** of the **OAuth2OOo** extension. Fixed [issue #12][52].

### What has been done for version 1.0.6:

- Support for version **1.2.4** of the **OAuth2OOo** extension. Many issues resolved.

### What has been done for version 1.0.7:

- Now use Python dateutil package to convert to UNO DateTime.

### What has been done for version 1.1.0:

- All Python packages necessary for the extension are now recorded in a [requirements.txt][53] file following [PEP 508][54].
- Now if you are not on Windows then the Python packages necessary for the extension can be easily installed with the command:  
  `pip install requirements.txt`
- Modification of the [Requirement][55] section.

### What has been done for version 1.1.1:

- Fixed a regression preventing the creation of new files.
- Integration of a fix to workaround the [issue #159988][56].

### What has been done for version 1.1.2:

- The creation of the database, during the first connection, uses the UNO API offered by the jdbcDriverOOo extension since version 1.3.2. This makes it possible to record all the information necessary for creating the database in 6 text tables which are in fact [6 csv files][57].
- Rewriting the [SQL views][58] necessary for managing duplicates. Now a folder or file's path is calculated by a recursive view that supports duplicates.
- Installing the extension will disable the option to create a backup copy (ie: .bak file) in LibreOffice. If this option is validated then the extension is no longer capable of saving files.
- The extension will ask you to install the OAuth2OOo and jdbcDriverOOo extensions in versions 1.3.4 and 1.3.2 respectively minimum.
- Many fixes.

### What has been done for version 1.1.3:

- Updated the [Python python-dateutil][59] package to version 2.9.0.post0.
- Updated the [Python ijson][60] package to version 3.3.0.
- Updated the [Python packaging][61] package to version 24.1.
- Updated the [Python setuptools][62] package to version 72.1.0 in order to respond to the [Dependabot security alert][63].
- The extension will ask you to install the OAuth2OOo and jdbcDriverOOo extensions in versions 1.3.6 and 1.4.2 respectively minimum.

### What has been done for version 1.1.4:

- Updated the [Python setuptools][62] package to version 73.0.1.
- The extension will ask you to install the OAuth2OOo and jdbcDriverOOo extensions in versions 1.3.7 and 1.4.5 respectively minimum.
- Changes to extension options that require a restart of LibreOffice will result in a message being displayed.
- Support for LibreOffice version 24.8.x.

### What has been done for version 1.1.5:

- Fixed a SQL query preventing a new folder from being created correctly.
- Disabling data replication in the extension options will display an explicit message in the replicator log.
- The extension will ask you to install the OAuth2OOo and jdbcDriverOOo extensions in versions 1.3.8 and 1.4.6 respectively minimum.
- Modification of the extension options accessible via: **Tools -> Options... -> Internet -> mDriveOOo** in order to comply with the new graphic charter.

### What has been done for version 1.1.6:

- Remote modifications of the contents of the files are taken into account by the replicator.
- If necessary, it is possible to request an initial synchronization in the extension options. It is also possible to request the download of all files already viewed that have a local copy.
- The replicator provides more comprehensive logging.
- Shared folders are now recognizable by their icon.
- Many fixes.

### What has been done for version 1.2.0:

- The extension will ask you to install the OAuth2OOo and jdbcDriverOOo extensions in versions 1.4.0 and 1.4.6 respectively minimum.
- It is possible to build the extension archive (ie: the oxt file) with the [Apache Ant][30] utility and the [build.xml][64] script file.
- The extension will refuse to install under OpenOffice regardless of version or LibreOffice other than 7.x or higher.
- Added binaries needed for Python libraries to work on Linux and LibreOffice 24.8 (ie: Python 3.9).
- The ability to not specify the user's account name in the URL is working again.

### What has been done for version 1.2.1:

- Updated the [Python packaging][61] package to version 24.2.
- Updated the [Python setuptools][62] package to version 75.8.0.
- Updated the [Python six][65] package to version 1.17.0.
- Support for Python version 3.13.

### What has been done for version 1.3.0:

- Updated the [Python packaging][61] package to version 25.0.
- Downgrade the [Python setuptools][62] package to version 75.3.2. to ensure support for Python 3.8.
- Passive registration deployment that allows for much faster installation of extensions and differentiation of registered UNO services from those provided by a Java or Python implementation. This passive registration is provided by the [LOEclipse][28] extension via [PR#152][66] and [PR#157][67].
- Modified [LOEclipse][28] to support the new `rdb` file format produced by the `unoidl-write` compilation utility. `idl` files have been updated to support both available compilation tools: idlc and unoidl-write.
- It is now possible to build the oxt file of the mDriveOOo extension only with the help of Apache Ant and a copy of the GitHub repository. The [How to build the extension][68] section has been added to the documentation.
- Implemented [PEP 570][69] in [logging][70] to support unique multiple arguments.
- To ensure the correct creation of the mDriveOOo database, it will be checked that the jdbcDriverOOo extension has `com.sun.star.sdb` as API level.
- Wrote two macros `OpenRemote` and `SaveRemote` to create custom menus and be able to keep the system dialog window for opening and saving files in LibreOffice. To make it easier to create these custom menus, the section [How to customize LibreOffice menus][71] has been added to the documentation.
- Requires the **jdbcDriverOOo extension at least version 1.5.0**.
- Requires the **OAuth2OOo extension at least version 1.5.0**.

### What remains to be done for version 1.3.0:

- Add new language for internationalization...

- Anything welcome...

[1]: </img/drive.svg#collapse>
[2]: <https://prrvchr.github.io/mDriveOOo/>
[3]: <https://prrvchr.github.io/mDriveOOo/README_fr>
[4]: <https://prrvchr.github.io/mDriveOOo/source/mDriveOOo/registration/TermsOfUse_en>
[5]: <https://prrvchr.github.io/mDriveOOo/source/mDriveOOo/registration/PrivacyPolicy_en>
[6]: <https://prrvchr.github.io/mDriveOOo#what-has-been-done-for-version-130>
[7]: <https://prrvchr.github.io/>
[8]: <https://www.libreoffice.org/download/download/>
[9]: <https://www.openoffice.org/download/index.html>
[10]: <https://learn.microsoft.com/en-us/graph/api/resources/onedrive?view=graph-rest-1.0>
[11]: <https://wiki.openoffice.org/wiki/Documentation/DevGuide/UCB/Content_Providers>
[12]: <https://github.com/prrvchr/mDriveOOo>
[13]: <https://github.com/prrvchr/mDriveOOo/issues/new>
[14]: <https://prrvchr.github.io/OAuth2OOo/#requirement>
[15]: <https://prrvchr.github.io/jdbcDriverOOo/#requirement>
[17]: <https://prrvchr.github.io/OAuth2OOo/img/OAuth2OOo.svg#middle>
[18]: <https://prrvchr.github.io/OAuth2OOo>
[19]: <https://github.com/prrvchr/OAuth2OOo/releases/latest/download/OAuth2OOo.oxt>
[20]: <https://img.shields.io/github/v/tag/prrvchr/OAuth2OOo?label=latest#right>
[21]: <https://prrvchr.github.io/jdbcDriverOOo/img/jdbcDriverOOo.svg#middle>
[22]: <https://prrvchr.github.io/jdbcDriverOOo>
[23]: <https://github.com/prrvchr/jdbcDriverOOo/releases/latest/download/jdbcDriverOOo.oxt>
[24]: <https://img.shields.io/github/v/tag/prrvchr/jdbcDriverOOo?label=latest#right>
[25]: <img/mDriveOOo.svg#middle>
[26]: <https://github.com/prrvchr/mDriveOOo/releases/latest/download/mDriveOOo.oxt>
[27]: <https://img.shields.io/github/downloads/prrvchr/mDriveOOo/latest/total?label=v1.3.0#right>
[28]: <https://github.com/LibreOffice/loeclipse>
[29]: <https://adoptium.net/temurin/releases/?version=8&package=jdk>
[30]: <https://ant.apache.org/manual/install.html>
[31]: <https://downloadarchive.documentfoundation.org/libreoffice/old/7.6.7.2/>
[32]: <https://github.com/prrvchr/mDriveOOo.git>
[33]: <https://bz.apache.org/ooo/show_bug.cgi?id=128569>
[34]: <https://github.com/prrvchr/mDriveOOo/blob/master/uno/lib/uno/ucb/replicator.py>
[35]: <https://github.com/prrvchr/mDriveOOo/blob/master/uno/lib/uno/ucb/database.py>
[36]: <https://github.com/prrvchr/mDriveOOo/blob/master/uno/lib/uno/ucb/datasource.py#L127>
[37]: <https://github.com/prrvchr/mDriveOOo/blob/master/uno/lib/uno/ucb/dbqueries.py#L154>
[38]: <https://datatracker.ietf.org/doc/html/draft-king-vnd-urlscheme-03>
[39]: <https://github.com/prrvchr/mDriveOOo/blob/master/uno/lib/uno/ucb/dbqueries.py#L163>
[40]: <https://github.com/prrvchr/mDriveOOo/blob/master/uno/lib/uno/ucb/dbqueries.py#L173>
[41]: <https://github.com/prrvchr/mDriveOOo/blob/master/uno/lib/uno/ucb/dbqueries.py#L193>
[42]: <https://github.com/prrvchr/mDriveOOo/blob/master/uno/lib/uno/ucb/dbqueries.py#L213>
[43]: <https://github.com/prrvchr/mDriveOOo/blob/master/uno/lib/uno/ucb/ucp/provider.py>
[44]: <https://github.com/prrvchr/mDriveOOo/blob/master/source/mDriveOOo/mDriveOOo.xcu#L42>
[45]: <https://github.com/prrvchr/mDriveOOo/blob/master/uno/rdb/idl/io/github/prrvchr/css/util/DateTimeWithTimezone.idl>
[46]: <https://bz.apache.org/ooo/show_bug.cgi?id=128560>
[47]: <https://github.com/prrvchr/mDriveOOo/blob/master/uno/lib/uno/ucb/dbqueries.py#L512>
[48]: <https://github.com/prrvchr/mDriveOOo/blob/master/uno/lib/uno/ucb/dbqueries.py#L557>
[49]: <https://github.com/prrvchr/mDriveOOo/blob/master/uno/lib/uno/ucb/dbqueries.py#L494>
[50]: <https://github.com/prrvchr/mDriveOOo/tree/master/uno/lib/uno/options/ucb>
[51]: <https://github.com/prrvchr/mDriveOOo/issues/9>
[52]: <https://github.com/prrvchr/gDriveOOo/issues/12>
[53]: <https://github.com/prrvchr/mDriveOOo/releases/latest/download/requirements.txt>
[54]: <https://peps.python.org/pep-0508/>
[55]: <https://prrvchr.github.io/mDriveOOo/#requirement>
[56]: <https://bugs.documentfoundation.org/show_bug.cgi?id=159988>
[57]: <https://github.com/prrvchr/mDriveOOo/tree/master/uno/lib/uno/ucb/hsqldb>
[58]: <https://github.com/prrvchr/mDriveOOo/blob/master/uno/lib/uno/ucb/dbqueries.py#L111>
[59]: <https://pypi.org/project/python-dateutil/>
[60]: <https://pypi.org/project/ijson/>
[61]: <https://pypi.org/project/packaging/>
[62]: <https://pypi.org/project/setuptools/>
[63]: <https://github.com/prrvchr/mDriveOOo/security/dependabot/1>
[64]: <https://github.com/prrvchr/mDriveOOo/blob/master/source/mDriveOOo/build.xml>
[65]: <https://pypi.org/project/six/>
[66]: <https://github.com/LibreOffice/loeclipse/pull/152>
[67]: <https://github.com/LibreOffice/loeclipse/pull/157>
[68]: <https://prrvchr.github.io/mDriveOOo/#how-to-build-the-extension>
[69]: <https://peps.python.org/pep-0570/>
[70]: <https://github.com/prrvchr/mDriveOOo/blob/master/uno/lib/uno/logger/logwrapper.py#L109>
[71]: <https://prrvchr.github.io/mDriveOOo/#how-to-customize-libreoffice-menus>
