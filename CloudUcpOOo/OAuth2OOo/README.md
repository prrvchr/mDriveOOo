**The use of this software subjects you to our** [Terms Of Use](https://prrvchr.github.io/OAuth2OOo/OAuth2OOo/registration/TermsOfUse_en) **and** [Data Protection Policy](https://prrvchr.github.io/OAuth2OOo/OAuth2OOo/registration/PrivacyPolicy_en)

## OAuth2OOo v.0.0.4

### Uno OAuth2.0 API for LibreOffice / OpenOffice.

![OAuth2OOo Wizard Page1 screenshot](OAuth2Wizard1.png)

![OAuth2OOo Wizard Page2 screenshot](OAuth2Wizard2.png)

![OAuth2OOo Wizard Page3 screenshot](OAuth2Wizard3.png)

The OAuth2.0 protocol allows the connection to resource servers, after acceptance of the connection authorization, by exchange of tokens.

The revocation takes place in the management of the applications associated with your account.

No more password is stored in LibreOffice.

### Use:

#### Create OAuth2 service:

service = context.ServiceManager.createInstanceWithContext("com.gmail.prrvchr.extensions.OAuth2OOo.OAuth2Service", context)

#### Optional (give a username and a remote resource url):

service.UserName = your_user_account

service.ResourceUrl = your_registered_url

#### Get the access token:

token = service.getToken('Bearer %s')

### Has been tested with:

* LibreOffice 6.0.2.1 x86_64 - Ubuntu 17.10 - LxQt 0.11.1

* OpenOffice 4.1.5 x86_64 - Ubuntu 17.10 - LxQt 0.11.1

I encourage you in case of problem to create an [issue](https://github.com/prrvchr/OAuth2OOo/issues/new)
I will try to solve it :-)
