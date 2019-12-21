**The use of this software subjects you to our** [Terms Of Use](https://prrvchr.github.io/oneDriveOOo/oneDriveOOo/registration/TermsOfUse_en) **and** [Data Protection Policy](https://prrvchr.github.io/oneDriveOOo/oneDriveOOo/registration/PrivacyPolicy_en)

## oneDriveOOo v.0.0.4

### Microsotf OneDrive implementation for LibreOffice / OpenOffice.

![oneDriveOOo screenshot](oneDrive.png)

### Use:

#### Install [OAuth2OOo](https://github.com/prrvchr/OAuth2OOo/raw/master/OAuth2OOo.oxt) extention v 0.0.4.

You must install this extention first!!!

Restart LibreOffice / OpenOffice after installation.

#### Install [oneDriveOOo](https://github.com/prrvchr/oneDriveOOo/raw/master/oneDriveOOo.oxt) extention v 0.0.4.

Restart LibreOffice / OpenOffice after installation.

### Requirement:

Using a version of Hsqldb higher than 1.8 requires that LibreOffice users must have no Hsqldb driver installed with LibreOffice  
(check your Installed Application under Windows or your Packet Manager under Linux)  
OpenOffice doesn't seem to need this workaround.

### Configure LibreOffice Open / Save dialogs:

#### For LibreOffice V5.x and before:

In menu Tools - Options - LibreOffice - General: check use LibreOffice dialogs.

#### For LibreOffice V6.x and above:

In menu Tools - Options - LibreOffice - Advanced - Open Expert Configuration

Search for: UseSystemFileDialog (Found under: org.openoffice.Office.Common > Misc)

Edit or change "true" to "false" (set it to "false")

### Open your OneDrive:

In File - Open - File name enter: vnd.microsoft-apps://your_account/ or vnd.microsoft-apps:///

If you don't give your_account, you will be asked for...

After authorizing the OAuthOOo application to access your OneDrive, your OneDrive should open!!! normally  ;-)

### Has been tested with:

* LibreOffice 6.0.4.2 - Ubuntu 17.10 -  LxQt 0.11.1

* OpenOffice 4.1.5 x86_64 - Ubuntu 17.10 - LxQt 0.11.1

I encourage you in case of problem to create an [issue](https://github.com/prrvchr/oneDriveOOo/issues/new)
I will try to solve it :-)
