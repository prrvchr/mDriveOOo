#!/bin/bash

./make_rdb.sh

cd ./OAuth2OOo/

zip -0 OAuth2OOo.zip mimetype

zip -r OAuth2OOo.zip *

cd ..

mv ./OAuth2OOo/OAuth2OOo.zip ./OAuth2OOo.oxt
