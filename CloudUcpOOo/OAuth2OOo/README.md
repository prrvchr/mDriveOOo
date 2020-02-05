**The use of this software subjects you to our** [Terms Of Use](https://prrvchr.github.io/OAuth2OOo/OAuth2OOo/registration/TermsOfUse_en) **and** [Data Protection Policy](https://prrvchr.github.io/OAuth2OOo/OAuth2OOo/registration/PrivacyPolicy_en)

## OAuth2OOo v.0.0.4


### Uno OAuth2.0 API for LibreOffice / OpenOffice.

![OAuth2OOo Wizard Page1 screenshot](OAuth2Wizard1.png)

![OAuth2OOo Wizard Page2 screenshot](OAuth2Wizard2.png)

![OAuth2OOo Wizard Page3 screenshot](OAuth2Wizard3.png)

![OAuth2OOo Wizard Page4 screenshot](OAuth2Wizard4.png)

The OAuth2.0 protocol allows the connection to resource servers, after acceptance of the connection authorization, by exchange of tokens.

The revocation takes place in the management of the applications associated with your account.

No more password is stored in LibreOffice.


### Install:

- Download the [extension](https://github.com/prrvchr/OAuth2OOo/releases/download/v0.0.4/OAuth2OOo.oxt)

- Install the extension in LibreOffice / OpenOffice.


### Use:

This extension is not made to be used alone, but provide OAuth2 service to other LibreOffice / OpenOffice extensions. Here's how we use its API:

#### Create OAuth2 service:

> identifier = "com.gmail.prrvchr.extensions.OAuth2OOo.OAuth2Service"  
> service = ctx.ServiceManager.createInstanceWithContext(identifier, ctx)

#### Initialize Session or at least Url:

- Initialize session: 

> initialized = service.initializeSession(registered_url, user_account)

- Initialize Url:

> initialized = service.initializeUrl(registered_url)

The returned value: `initialized` is True if `registered_url` and/or `user_account` has been retreived from the OAuth2 service configuration.

#### Get the access token:

> format = 'Bearer %s'  
> token = service.getToken(format)


### Has been tested with:

* LibreOffice 6.0.2.1 x86_64 - Ubuntu 17.10 - LxQt 0.11.1

* OpenOffice 4.1.5 x86_64 - Ubuntu 17.10 - LxQt 0.11.1

I encourage you in case of problem :-(  
to create an [issue](https://github.com/prrvchr/OAuth2OOo/issues/new)  
I will try to solve it ;-)
