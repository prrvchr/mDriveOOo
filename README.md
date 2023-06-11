# ![oneDriveOOo logo][1] oneDriveOOo
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

**Ce [document][2] en français.**

**The use of this software subjects you to our [Terms Of Use][3] and [Data Protection Policy][4].**

# version [0.0.6][5]

## Introduction:

**oneDriveOOo** is part of a [Suite][6] of [LibreOffice][7] and/or [OpenOffice][8] extensions allowing to offer you innovative services in these office suites.  
This extension allows you to work in LibreOffice / OpenOffice on your Microsoft OneDrive files, even while offline.

Being free software I encourage you:
- To duplicate its [source code][9].
- To make changes, corrections, improvements.
- To open [issue][10] if needed.

In short, to participate in the development of this extension.
Because it is together that we can make Free Software smarter.

## Requirement:

If you are using **OpenOffice on Windows** regardless of the version then you are subject to [bug 128569][11]. I haven't found a workaround, for now I can only advise you to install **LibreOffice**...

oneDriveOOo uses a local [HsqlDB][12] database version 2.7.1.  
HsqlDB being a database written in Java, its use requires the [installation and configuration][13] in LibreOffice / OpenOffice of a **JRE version 11 or later**.  
I recommend [Adoptium][14] as your Java installation source.

If you are using **LibreOffice on Linux**, you need to make sure of two things:
  - You are subject to [bug 139538][15]. To work around the problem, please **uninstall the packages** with commands:
    - `sudo apt remove libreoffice-sdbc-hsqldb` (to uninstall the libreoffice-sdbc-hsqldb package)
    - `sudo apt remove libhsqldb1.8.0-java` (to uninstall the libhsqldb1.8.0-java package)

If you still want to use the Embedded HsqlDB functionality provided by LibreOffice, then install the [HsqlDBembeddedOOo][16] extension.  

  - If the python3-cffi-backend package is installed then you need to **install the python3-cffi package** with the command:
    - `dpkg -s python3-cffi-backend` (to know if the python3-cffi-backend package is installed)
    - `sudo apt install python3-cffi` (to install the python3-cffi package if needed)

OpenOffice on Linux and LibreOffice on Windows are not subject to these malfunctions.

## Installation:

It seems important that the file was not renamed when it was downloaded.
If necessary, rename it before installing it.

- Install ![OAuth2OOo logo][17] **[OAuth2OOo.oxt][18]** extension version 0.0.6.

You must first install this extension, if it is not already installed.

- Install ![jdbcDriverOOo logo][19] **[jdbcDriverOOo.oxt][20]** extension version 0.0.4.

You must install this extension, if it is not already installed.

- Install ![oneDriveOOo logo][1] **[oneDriveOOo.oxt][21]** extension version 0.0.6.

Restart LibreOffice / OpenOffice after installation.

## Use:

**Open your Microsoft OneDrive:**

In **File -> Open** enter in the first drop-down list:

- For a named Url: **vnd-microsoft://your_email@your_provider**  

or

- For an unnamed Url (anonymous): **vnd-microsoft:///**

If you don't give **your_email@your_provider**, you will be asked for...

Anonymous Urls allow you to remain anonymous (your account does not appear in the Url) while named Urls allow you to access several accounts simultaneously.

After authorizing the [OAuth2OOo][23] application to access your Microsoft OneDrive files, your OneDrive files should appear!!! normally  ;-)

## Has been tested with:

* LibreOffice 7.3.7.2 - Lubuntu 22.04 - OpenJDK-11-JRE (amd64)

* LibreOffice 7.4.3.2(x64) - Windows 10(x64) - Adoptium JDK Hotspot 11.0.17 (x64) (under Lubuntu 22.04 / VirtualBox 6.1.38)

* OpenOffice 4.1.13 - Lubuntu 22.04 - OpenJDK-11-JRE (amd64) (under Lubuntu 22.04 / VirtualBox 6.1.38)

* **Does not work with OpenOffice on Windows** see [bug 128569][11]. Having no solution, I encourage you to install **LibreOffice**.

I encourage you in case of problem :-(  
to create an [issue][10]  
I will try to solve it ;-)

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

- Rewrite of the [options window][41] accessible by: **Tools -> Options -> Internet -> oneDriveOOo** in order to allow:
  - Access to the two log files concerning the activities of the UCP and the data replicator.
  - Choice of synchronization order.
  - The modification of the interval between two synchronizations.
  - Access to the underlying HsqlDB 2.7.1 database managing your Microsoft oneDrive metadata.

- The presence or absence of a trailing slash in the Url is now supported.

- Many other fix...

### What remains to be done for version 0.0.6:

- Add new language for internationalization...

- Anything welcome...

[1]: <img/oneDriveOOo.png>
[2]: <https://prrvchr.github.io/oneDriveOOo/README_fr>
[3]: <https://prrvchr.github.io/oneDriveOOo/source/oneDriveOOo/registration/TermsOfUse_en>
[4]: <https://prrvchr.github.io/oneDriveOOo/source/oneDriveOOo/registration/PrivacyPolicy_en>
[5]: <https://prrvchr.github.io/oneDriveOOo#historical>
[6]: <https://prrvchr.github.io/>
[7]: <https://www.libreoffice.org/download/download/>
[8]: <https://www.openoffice.org/download/index.html>
[9]: <https://github.com/prrvchr/oneDriveOOo>
[10]: <https://github.com/prrvchr/oneDriveOOo/issues/new>
[11]: <https://bz.apache.org/ooo/show_bug.cgi?id=128569>
[12]: <http://hsqldb.org/>
[13]: <https://wiki.documentfoundation.org/Documentation/HowTo/Install_the_correct_JRE_-_LibreOffice_on_Windows_10>
[14]: <https://adoptium.net/releases.html?variant=openjdk11>
[15]: <https://bugs.documentfoundation.org/show_bug.cgi?id=139538>
[16]: <https://prrvchr.github.io/HsqlDBembeddedOOo/>
[17]: <https://prrvchr.github.io/OAuth2OOo/img/OAuth2OOo.png>
[18]: <https://github.com/prrvchr/OAuth2OOo/raw/master/OAuth2OOo.oxt>
[19]: <https://prrvchr.github.io/jdbcDriverOOo/img/jdbcDriverOOo.png>
[20]: <https://github.com/prrvchr/jdbcDriverOOo/raw/master/source/jdbcDriverOOo/dist/jdbcDriverOOo.oxt>
[21]: <https://github.com/prrvchr/oneDriveOOo/raw/master/source/oneDriveOOo/dist/oneDriveOOo.oxt>
[23]: <https://prrvchr.github.io/OAuth2OOo>
[24]: <https://github.com/prrvchr/oneDriveOOo/blob/master/uno/lib/uno/ucb/replicator.py>
[25]: <https://github.com/prrvchr/oneDriveOOo/blob/master/uno/lib/uno/ucb/database.py>
[26]: <https://github.com/prrvchr/oneDriveOOo/blob/master/uno/lib/uno/ucb/datasource.py#L127>
[27]: <https://github.com/prrvchr/oneDriveOOo/blob/master/uno/lib/uno/ucb/dbqueries.py#L154>
[28]: <https://datatracker.ietf.org/doc/html/draft-king-vnd-urlscheme-03>
[29]: <https://github.com/prrvchr/oneDriveOOo/blob/master/uno/lib/uno/ucb/dbqueries.py#L163>
[30]: <https://github.com/prrvchr/oneDriveOOo/blob/master/uno/lib/uno/ucb/dbqueries.py#L173>
[31]: <https://github.com/prrvchr/oneDriveOOo/blob/master/uno/lib/uno/ucb/dbqueries.py#L193>
[32]: <https://github.com/prrvchr/oneDriveOOo/blob/master/uno/lib/uno/ucb/dbqueries.py#L213>
[33]: <https://github.com/prrvchr/oneDriveOOo/blob/master/uno/lib/uno/ucb/ucp/provider.py>
[34]: <https://github.com/prrvchr/oneDriveOOo/blob/master/source/oneDriveOOo/oneDriveOOo.xcu#L42>
[35]: <https://github.com/prrvchr/oneDriveOOo/blob/master/uno/rdb/idl/io/github/prrvchr/css/util/DateTimeWithTimezone.idl>
[36]: <https://prrvchr.github.io/jdbcDriverOOo>
[37]: <https://bz.apache.org/ooo/show_bug.cgi?id=128560>
[38]: <https://github.com/prrvchr/oneDriveOOo/blob/master/uno/lib/uno/ucb/dbqueries.py#L512>
[39]: <https://github.com/prrvchr/oneDriveOOo/blob/master/uno/lib/uno/ucb/dbqueries.py#L557>
[40]: <https://github.com/prrvchr/oneDriveOOo/blob/master/uno/lib/uno/ucb/dbqueries.py#L494>
[41]: <https://github.com/prrvchr/oneDriveOOo/tree/master/uno/lib/uno/options/ucb>
