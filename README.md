# oneDriveOOo v.0.0.1

## Microsotf OneDrive implementation for LibreOffice / OpenOffice.

![oneDriveOOo screenshot](oneDrive.png)

## Use:

### Install [OAuth2OOo](https://github.com/prrvchr/OAuth2OOo/raw/master/OAuth2OOo.oxt) extention v 0.0.3.

You must install this extention first!!!

Restart LibreOffice / OpenOffice after installation.

### Install [CloudUcpOOo](https://github.com/prrvchr/CloudUcpOOo/raw/master/CloudUcpOOo.oxt) extention v 0.0.1.

You must install this extention first!!!

Restart LibreOffice / OpenOffice after installation.

### Install [oneDriveOOo](https://github.com/prrvchr/oneDriveOOo/raw/master/oneDriveOOo.oxt) extention v 0.0.1.

Restart LibreOffice / OpenOffice after installation.

### Configure Open / Save dialogs:

#### For OpenOffice or LibreOffice V5.0 and before:

In menu Tools - Options - Libre/OpenOffice - General: check use Libre/OpenOffice dialogs.

#### For LibreOffice V6.0 and above:

In menu Tools - Options - LibreOffice - Advanced - Open Expert Configuration

Search for: UseSystemFileDialog (Found under: org.openoffice.Office.Common > Misc)

Edit or change "true" to "false" (set it to "false")

### Open your OneDrive:

In File - Open - File name enter: vnd.microsoft-apps://your_account/ or vnd.microsoft-apps:///

If you don't give your_account, you will be asked for...

After authorizing the OAuthOOo application to access your OneDrive, your OneDrive should open!!! normally  ;-)

## Has been tested with:

* LibreOffice 6.0.4.2 - Ubuntu 17.10 -  LxQt 0.11.1

* OpenOffice 4.1.5 x86_64 - Ubuntu 17.10 - LxQt 0.11.1
	
I encourage you in case of problem to create an [issue](https://github.com/prrvchr/oneDriveOOo/issues/new)
I will try to solve it :-)
