# ![oneDriveOOo logo](img/oneDriveOOo.png) oneDriveOOo

**Ce [document](https://prrvchr.github.io/oneDriveOOo/README_fr) en français.**

**The use of this software subjects you to our [Terms Of Use](https://prrvchr.github.io/oneDriveOOo/oneDriveOOo/registration/TermsOfUse_en) and [Data Protection Policy](https://prrvchr.github.io/oneDriveOOo/oneDriveOOo/registration/PrivacyPolicy_en).**

# version [0.0.5](https://prrvchr.github.io/oneDriveOOo#historical)

## Introduction:

**oneDriveOOo** is part of a [Suite](https://prrvchr.github.io/) of [LibreOffice](https://www.libreoffice.org/download/download/) and/or [OpenOffice](https://www.openoffice.org/download/index.html) extensions allowing to offer you innovative services in these office suites.  
This extension allows you to work in LibreOffice / OpenOffice on your Microsoft OneDrive files, even while offline.

Being free software I encourage you:
- To duplicate its [source code](https://github.com/prrvchr/oneDriveOOo).
- To make changes, corrections, improvements.
- To open [issue](https://github.com/prrvchr/oneDriveOOo/issues/new) if needed.

In short, to participate in the development of this extension.
Because it is together that we can make Free Software smarter.

## Requirement:

oneDriveOOo uses a local HsqlDB database of version 2.5.1.  
The use of HsqlDB requires the installation and configuration within LibreOffice / OpenOffice of a **JRE version 1.8 minimum** (ie: Java version 8)  
I recommend [AdoptOpenJDK](https://adoptopenjdk.net/) as your Java installation source.

If you are using **LibreOffice on Linux**, then you are subject to [bug 139538](https://bugs.documentfoundation.org/show_bug.cgi?id=139538).  
To work around the problem, please uninstall the packages:
- libreoffice-sdbc-hsqldb
- libhsqldb1.8.0-java

If you still want to use the Embedded HsqlDB functionality provided by LibreOffice, then install the [HsqlDBembeddedOOo](https://prrvchr.github.io/HsqlDBembeddedOOo/) extension.  
OpenOffice and LibreOffice on Windows are not subject to this malfunction.

## Installation:

It seems important that the file was not renamed when it was downloaded.
If necessary, rename it before installing it.

- Install [OAuth2OOo.oxt](https://github.com/prrvchr/OAuth2OOo/raw/master/OAuth2OOo.oxt) extension version 0.0.5.

You must first install this extension, if it is not already installed.

- Install [oneDriveOOo.oxt](https://github.com/prrvchr/oneDriveOOo/raw/master/oneDriveOOo.oxt) extension version 0.0.5.

Restart LibreOffice / OpenOffice after installation.

## Configuration:

Configure LibreOffice Open / Save dialogs (not necessary with OpenOffice):

- **For LibreOffice V5.x and before:**

In menu Tools - Options - LibreOffice - General: check use LibreOffice dialogs.

- **For LibreOffice V6.x and above:**

In menu Tools - Options - LibreOffice - Advanced - Open Expert Configuration

Search for: UseSystemFileDialog (Found under: org.openoffice.Office.Common > Misc)

Edit or change "true" to "false" (set it to "false")

## Use:

**Open your Microsoft OneDrive:**

In File - Open - File name enter:

- **vnd.microsoft-apps://your_account/**

or

- **vnd.microsoft-apps:///**

If you don't give your_account, you will be asked for...

After authorizing the [OAuth2OOo](https://prrvchr.github.io/OAuth2OOo) application to access your Microsoft OneDrive files, your OneDrive files should appear!!! normally  ;-)

## Has been tested with:

* LibreOffice 6.4.4.2 - Ubuntu 20.04 -  LxQt 0.14.1

* LibreOffice 7.0.0.0.alpha1 - Ubuntu 20.04 -  LxQt 0.14.1

* OpenOffice 4.1.8 x86_64 - Ubuntu 20.04 - LxQt 0.14.1

* OpenOffice 4.2.0.Build:9820 x86_64 - Ubuntu 20.04 - LxQt 0.14.1

* LibreOffice 6.1.5.2 - Raspbian 10 buster - Raspberry Pi 4 Model B

* LibreOffice 6.4.4.2 (x64) - Windows 7 SP1

I encourage you in case of problem :-(  
to create an [issue](https://github.com/prrvchr/oneDriveOOo/issues/new)  
I will try to solve it ;-)

## Historical:

### What has been done for version 0.0.5:

- Integration and use of the new Hsqldb v2.5.1 system versioning.

- Writing of a new [Replicator](https://github.com/prrvchr/oneDriveOOo/blob/master/CloudUcpOOo/python/clouducp/replicator.py) interface, launched in the background (python Thread) responsible for:

    - Perform the necessary procedures when creating a new user (initial Pull).

    - Carry out pulls regularly (every ten minutes) in order to synchronize any external changes (Pull all changes).

    - Replicate on demand all changes to the hsqldb 2.5.1 database using system versioning (Push all changes).

- Writing of a new [DataBase](https://github.com/prrvchr/oneDriveOOo/blob/master/CloudUcpOOo/python/clouducp/database.py) interface, responsible for making all calls to the database.

- Setting up a cache on the Identifiers, see method: [getIdentifier()](https://github.com/prrvchr/oneDriveOOo/blob/master/CloudUcpOOo/python/clouducp/datasource.py), allowing access to a Content (file or folder) without access to the database for subsequent calls.

- Management of duplicate file/folder names by [SQL Views](https://github.com/prrvchr/oneDriveOOo/blob/master/CloudUcpOOo/python/clouducp/dbqueries.py): Child, Twin, Uri, and Title generating unique names if duplicates names exist.  
Although this functionality is only needed for gDriveOOo, it is implemented globally...

- Many other fix...

### What remains to be done for version 0.0.5:

- Write the implementation Pull Change in the new [Replicator](https://github.com/prrvchr/oneDriveOOo/blob/master/CloudUcpOOo/python/clouducp/replicator.py) interface.

- Add new language for internationalization...

- Anything welcome...
