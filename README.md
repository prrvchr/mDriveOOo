<!--
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
-->
# Documentation

**Ce [document][2] en français.**

**The use of this software subjects you to our [Terms Of Use][3] and [Data Protection Policy][4].**

# version [1.0.4][5]

## Introduction:

**mDriveOOo** is part of a [Suite][6] of [LibreOffice][7] ~~and/or [OpenOffice][8]~~ extensions allowing to offer you innovative services in these office suites.  
This extension allows you to work in LibreOffice on your Microsoft oneDrive files, even while offline.

Being free software I encourage you:
- To duplicate its [source code][9].
- To make changes, corrections, improvements.
- To open [issue][10] if needed.

In short, to participate in the development of this extension.
Because it is together that we can make Free Software smarter.

___
## Requirement:

In order to take advantage of the latest versions of the Python libraries used in OAuth2OOo, version 2 of Python has been abandoned in favor of **Python 3.8 minimum**.  
This means that **mDriveOOo no longer supports OpenOffice and LibreOffice 6.x on Windows since version 1.0.0**.
I can only advise you **to migrate to LibreOffice 7.x**.

mDriveOOo uses a local [HsqlDB][12] database version 2.7.2.  
HsqlDB being a database written in Java, its use requires the [installation and configuration][13] in LibreOffice / OpenOffice of a **JRE version 11 or later**.  
I recommend [Adoptium][14] as your Java installation source.

If you are using **LibreOffice on Linux**, you are subject to [bug 139538][15]. To work around the problem, please **uninstall the packages** with commands:
- `sudo apt remove libreoffice-sdbc-hsqldb` (to uninstall the libreoffice-sdbc-hsqldb package)
- `sudo apt remove libhsqldb1.8.0-java` (to uninstall the libhsqldb1.8.0-java package)

If you still want to use the Embedded HsqlDB functionality provided by LibreOffice, then install the [HyperSQLOOo][16] extension.  

___
## Installation:

It seems important that the file was not renamed when it was downloaded.
If necessary, rename it before installing it.

- Install ![OAuth2OOo logo][17] **[OAuth2OOo.oxt][18]** extension version 1.2.1.

You must first install this extension, if it is not already installed.

- Install ![jdbcDriverOOo logo][19] **[jdbcDriverOOo.oxt][20]** extension version 1.0.5.

You must install this extension, if it is not already installed.

- Install ![mDriveOOo logo][1] **[mDriveOOo.oxt][21]** extension version [![Version][0]][21]

Restart LibreOffice / OpenOffice after installation.

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

After authorizing the [OAuth2OOo][23] application to access your Microsoft OneDrive files, your OneDrive files should appear!!! normally  :wink:

___
## Has been tested with:

* LibreOffice 7.3.7.2 - Lubuntu 22.04 - Python version 3.10.12

* LibreOffice 7.5.4.2(x86) - Windows 10 - Python version 3.8.16 (under Lubuntu 22.04 / VirtualBox 6.1.38)

* LibreOffice 7.4.3.2(x64) - Windows 10(x64) - Python version 3.8.15 (under Lubuntu 22.04 / VirtualBox 6.1.38)

* **Does not work with OpenOffice** see [bug 128569][11]. Having no solution, I encourage you to install **LibreOffice**.

I encourage you in case of problem :confused:  
to create an [issue][10]  
I will try to solve it :smile:

___
## Historical:

### What has been done for version 0.0.5:

- Integration and use of the new Hsqldb v2.5.1 system versioning.

- Writing of a new [Replicator][24] interface, launched in the background (python Thread) responsible for:

    - Perform the necessary procedures when creating a new user (initial Pull).

    - Carry out pulls regularly (every ten minutes) in order to synchronize any external changes (Pull all changes).

    - Replicate on demand all changes to the hsqldb 2.5.1 database using system versioning (Push all changes).

- Writing of a new [DataBase][25] interface, responsible for making all calls to the database.

- Setting up a cache on the Identifiers, see method: [_getUser()][26], allowing access to a Content (file or folder) without access to the database for subsequent calls.

- Management of duplicate file/folder names by [SQL Views][27]: Child, Twin, Uri, and Title generating unique names if duplicates names exist.  
Although this functionality is only needed for gDriveOOo, it is implemented globally...

- Many other fix...

### What has been done for version 0.0.6:

- Using new scheme: **vnd-microsoft://** as claimed by [draft-king-vnd-urlscheme-03.txt][28]

- Achievement of handling duplicate file/folder names by SQL views in HsqlDB:
  - A [**Twin**][29] view grouping all the duplicates by parent folder and ordering them by creation date, modification date.
  - A [**Uri**][30] view generating unique indexes for each duplicate.
  - A [**Title**][31] view generating unique names for each duplicate.
  - A recursive view [**Path**][32] to generate a unique path for each file / folder.

- Creation of a [Provider][33] able to respond to the two types of Urls supported (named and anonymous).  
  Regular expressions (regex), declared in the [UCB configuration file][34], are now used by OpenOffice/LibreOffice to send URLs to the appropriate ContentProvider.

- Use of the new UNO struct [DateTimeWithTimezone][35] provided by the extension [jdbcDriverOOo][36] since its version 0.0.4.  
  Although this struct already exists in LibreOffice, its creation was necessary in order to remain compatible with OpenOffice (see [Enhancement Request 128560][37]).

- Modification of the [Replicator][24] interface, in order to allow:
  - To choose the data synchronization order (local first then remote or vice versa).
  - Synchronization of local changes by atomic operations performed in chronological order to fully support offline work.  
  To do this, three SQL procedures [GetPushItems][38], [GetPushProperties][39] and [UpdatePushItems][40] are used for each user who has accessed his files / folders.

- Rewrite of the [options window][41] accessible by: **Tools -> Options -> Internet -> mDriveOOo** in order to allow:
  - Access to the two log files concerning the activities of the UCP and the data replicator.
  - Choice of synchronization order.
  - The modification of the interval between two synchronizations.
  - Access to the underlying HsqlDB 2.7.2 database managing your Microsoft oneDrive metadata.

- The presence or absence of a trailing slash in the Url is now supported.

- Many other fix...

### What has been done for version 1.0.0:

- Renamed OneDriveOOo extension to mDriveOOo.

### What has been done for version 1.0.1:

- Implementation of the management of shared files as requested in the request for improvement, see [issue 9][42].

- The name of the shared folder can be defined before any connection in: **Tools -> Options -> Internet -> mDriveOOo -> Handle shared documents in folder:**

- Many other fix...

### What has been done for version 1.0.2:

- The absence or obsolescence of the **OAuth2OOo** and/or **jdbcDriverOOo** extensions necessary for the proper functioning of **mDriveOOo** now displays an error message.

- Many other things...

### What has been done for version 1.0.3:

- Support for version **1.2.0** of the **OAuth2OOo** extension. Previous versions will not work with **OAuth2OOo** extension 1.2.0 or higher.

### What has been done for version 1.0.4:

- Support for version **1.2.1** of the **OAuth2OOo** extension. Previous versions will not work with **OAuth2OOo** extension 1.2.1 or higher.

### What remains to be done for version 1.0.4:

- Add new language for internationalization...

- Anything welcome...

[0]: <https://img.shields.io/github/downloads/prrvchr/mDriveOOo/latest/total?label=v1.0.4>
[1]: <img/mDriveOOo.svg>
[2]: <https://prrvchr.github.io/mDriveOOo/README_fr>
[3]: <https://prrvchr.github.io/mDriveOOo/source/mDriveOOo/registration/TermsOfUse_en>
[4]: <https://prrvchr.github.io/mDriveOOo/source/mDriveOOo/registration/PrivacyPolicy_en>
[5]: <https://prrvchr.github.io/mDriveOOo#historical>
[6]: <https://prrvchr.github.io/>
[7]: <https://www.libreoffice.org/download/download/>
[8]: <https://www.openoffice.org/download/index.html>
[9]: <https://github.com/prrvchr/mDriveOOo>
[10]: <https://github.com/prrvchr/mDriveOOo/issues/new>
[11]: <https://bz.apache.org/ooo/show_bug.cgi?id=128569>
[12]: <http://hsqldb.org/>
[13]: <https://wiki.documentfoundation.org/Documentation/HowTo/Install_the_correct_JRE_-_LibreOffice_on_Windows_10>
[14]: <https://adoptium.net/releases.html?variant=openjdk11>
[15]: <https://bugs.documentfoundation.org/show_bug.cgi?id=139538>
[16]: <https://prrvchr.github.io/HyperSQLOOo/>
[17]: <https://prrvchr.github.io/OAuth2OOo/img/OAuth2OOo.svg>
[18]: <https://github.com/prrvchr/OAuth2OOo/releases/latest/download/OAuth2OOo.oxt>
[19]: <https://prrvchr.github.io/jdbcDriverOOo/img/jdbcDriverOOo.svg>
[20]: <https://github.com/prrvchr/jdbcDriverOOo/releases/latest/download/jdbcDriverOOo.oxt>
[21]: <https://github.com/prrvchr/mDriveOOo/releases/latest/download/mDriveOOo.oxt>
[23]: <https://prrvchr.github.io/OAuth2OOo>
[24]: <https://github.com/prrvchr/mDriveOOo/blob/master/uno/lib/uno/ucb/replicator.py>
[25]: <https://github.com/prrvchr/mDriveOOo/blob/master/uno/lib/uno/ucb/database.py>
[26]: <https://github.com/prrvchr/mDriveOOo/blob/master/uno/lib/uno/ucb/datasource.py#L127>
[27]: <https://github.com/prrvchr/mDriveOOo/blob/master/uno/lib/uno/ucb/dbqueries.py#L154>
[28]: <https://datatracker.ietf.org/doc/html/draft-king-vnd-urlscheme-03>
[29]: <https://github.com/prrvchr/mDriveOOo/blob/master/uno/lib/uno/ucb/dbqueries.py#L163>
[30]: <https://github.com/prrvchr/mDriveOOo/blob/master/uno/lib/uno/ucb/dbqueries.py#L173>
[31]: <https://github.com/prrvchr/mDriveOOo/blob/master/uno/lib/uno/ucb/dbqueries.py#L193>
[32]: <https://github.com/prrvchr/mDriveOOo/blob/master/uno/lib/uno/ucb/dbqueries.py#L213>
[33]: <https://github.com/prrvchr/mDriveOOo/blob/master/uno/lib/uno/ucb/ucp/provider.py>
[34]: <https://github.com/prrvchr/mDriveOOo/blob/master/source/mDriveOOo/mDriveOOo.xcu#L42>
[35]: <https://github.com/prrvchr/mDriveOOo/blob/master/uno/rdb/idl/io/github/prrvchr/css/util/DateTimeWithTimezone.idl>
[36]: <https://prrvchr.github.io/jdbcDriverOOo>
[37]: <https://bz.apache.org/ooo/show_bug.cgi?id=128560>
[38]: <https://github.com/prrvchr/mDriveOOo/blob/master/uno/lib/uno/ucb/dbqueries.py#L512>
[39]: <https://github.com/prrvchr/mDriveOOo/blob/master/uno/lib/uno/ucb/dbqueries.py#L557>
[40]: <https://github.com/prrvchr/mDriveOOo/blob/master/uno/lib/uno/ucb/dbqueries.py#L494>
[41]: <https://github.com/prrvchr/mDriveOOo/tree/master/uno/lib/uno/options/ucb>
[42]: <https://github.com/prrvchr/mDriveOOo/issues/9>
