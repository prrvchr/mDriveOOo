
cd .\OAuth2OOo

..\zip -0 OAuth2OOo.zip mimetype

..\zip -r OAuth2OOo.zip *

cd ..

move /Y .\OAuth2OOo\OAuth2OOo.zip .\OAuth2OOo.oxt
