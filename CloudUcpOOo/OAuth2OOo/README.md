**Ce [document](https://prrvchr.github.io/OAuth2OOo/README_fr) en français.**

**The use of this software subjects you to our** [**Terms Of Use**](https://prrvchr.github.io/OAuth2OOo/OAuth2OOo/registration/TermsOfUse_en) **and** [**Data Protection Policy**](https://prrvchr.github.io/OAuth2OOo/OAuth2OOo/registration/PrivacyPolicy_en).

# version [0.0.5](https://prrvchr.github.io/OAuth2OOo#historical)

## Introduction:

**OAuth2OOo** is part of a [Suite](https://prrvchr.github.io/) of [LibreOffice](https://www.libreoffice.org/download/download/) and/or [OpenOffice](https://www.openoffice.org/download/index.html) extensions allowing to offer you innovative services in these office suites.  
This extension is the implementation of the OAuth 2.0 protocol. Protocol allowing you to obtain your consent so that an application can access your data present at the GAFA.

Being free software I encourage you:
- To duplicate its [source code](https://github.com/prrvchr/OAuth2OOo).
- To make changes, corrections, improvements.
- To open [issue](https://github.com/prrvchr/OAuth2OOo/issues/new) if needed.

In short, to participate in the development of this extension.
Because it is together that we can make Free Software smarter.

## Uno OAuth2.0 API for LibreOffice / OpenOffice.

![OAuth2OOo Wizard Page1 screenshot](OAuth2Wizard1.png)

![OAuth2OOo Wizard Page2 screenshot](OAuth2Wizard2.png)

![OAuth2OOo Wizard Page3 screenshot](OAuth2Wizard3.png)

![OAuth2OOo Wizard Page4 screenshot](OAuth2Wizard4.png)

The OAuth2.0 protocol allows the connection to resource servers, after acceptance of the connection authorization, by exchange of tokens.

The revocation takes place in the management of the applications associated with your account.

No more password is stored in LibreOffice / OpenOffice.

## Install:

It seems important that the file was not renamed when it was downloaded.
If necessary, rename it before installing it.

- Install the [OAuth2OOo.oxt](https://github.com/prrvchr/OAuth2OOo/raw/master/OAuth2OOo.oxt) extension version 0.0.5.

- Restart LibreOffice / OpenOffice after installation.

## Use:

This extension is not made to be used alone, but provide OAuth2 service to other LibreOffice / OpenOffice extensions.  
Here's how we use its API:

### Create OAuth2 service:

> identifier = "com.gmail.prrvchr.extensions.OAuth2OOo.OAuth2Service"  
> service = ctx.ServiceManager.createInstanceWithContext(identifier, ctx)

### Initialize Session or at least Url:

- Initialize Session: 

> initialized = service.initializeSession(registered_url, user_account)

- Initialize Url:

> initialized = service.initializeUrl(registered_url)

The returned value: `initialized` is True if `registered_url` and/or `user_account` has been retreived from the OAuth2 service configuration.

### Get the access token:

> format = 'Bearer %s'  
> token = service.getToken(format)

## Has been tested with:

* LibreOffice 6.4.4.2 - Ubuntu 20.04 -  LxQt 0.14.1

* LibreOffice 7.0.0.0.alpha1 - Ubuntu 20.04 -  LxQt 0.14.1

* OpenOffice 4.1.5 x86_64 - Ubuntu 20.04 - LxQt 0.14.1

* OpenOffice 4.2.0.Build:9820 x86_64 - Ubuntu 20.04 - LxQt 0.14.1

* LibreOffice 6.1.5.2 - Raspbian 10 buster - Raspberry Pi 4 Model B

* LibreOffice 6.4.4.2 (x64) - Windows 7 SP1

I encourage you in case of problem :-(  
to create an [issue](https://github.com/prrvchr/OAuth2OOo/issues/new)  
I will try to solve it ;-)

## Historical:

### What has been done for version 0.0.5:

- Writing of a new [XWizard](https://github.com/prrvchr/OAuth2OOo/blob/master/python/wizard.py) interface in order to replace the Wizard service which became defective with version 6.4.x and 7.x of LibreOffice (see [bug 132110](https://bugs.documentfoundation.org/show_bug.cgi?id=132110)).

    This new interface also fixes [bug 132661](https://bugs.documentfoundation.org/show_bug.cgi?id=132661) and [bug 132666](https://bugs.documentfoundation.org/show_bug.cgi?id=132666) and allows access to versions 6.4.x and 7.x of LibreOffice...

    In addition this new XWizard adds new functionality such as:

    - Automatic resizing of the Wizard to the dimensions of the first displayed page.
    - Automatic move to page X on opening if possible.

- Fixed an issue with tokens without expiration (as used by Dropbox) on testing their validity...

- Many other fix...

### What remains to be done for version 0.0.5:

- Write the implementation of the Help button (CommandButton5) in the new [XWizard](https://github.com/prrvchr/OAuth2OOo/blob/master/python/wizard.py) interface.

- Add new language for internationalization...

- Anything welcome...
