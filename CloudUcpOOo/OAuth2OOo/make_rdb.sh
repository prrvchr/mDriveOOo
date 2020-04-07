#!/bin/bash

WorkBench=OAuth2OOo
OOoProgram=/usr/lib/libreoffice/program
Path=$(dirname "${0}")

rm ${Path}/${WorkBench}/types.rdb

./rdb/make_rdb.sh ${WorkBench} com/sun/star/auth/RestRequestTokenType
./rdb/make_rdb.sh ${WorkBench} com/sun/star/auth/RestRequestToken
./rdb/make_rdb.sh ${WorkBench} com/sun/star/auth/RestRequestEnumerator
./rdb/make_rdb.sh ${WorkBench} com/sun/star/auth/RestRequestParameter
./rdb/make_rdb.sh ${WorkBench} com/sun/star/auth/XRestKeyMap
./rdb/make_rdb.sh ${WorkBench} com/sun/star/auth/XRestDataParser
./rdb/make_rdb.sh ${WorkBench} com/sun/star/auth/XRestRequest
./rdb/make_rdb.sh ${WorkBench} com/sun/star/auth/XRestEnumeration
./rdb/make_rdb.sh ${WorkBench} com/sun/star/auth/XInteractionUserName
./rdb/make_rdb.sh ${WorkBench} com/sun/star/auth/XOAuth2Request
./rdb/make_rdb.sh ${WorkBench} com/sun/star/auth/XRestUploader
./rdb/make_rdb.sh ${WorkBench} com/sun/star/auth/XOAuth2Service
./rdb/make_rdb.sh ${WorkBench} com/sun/star/auth/OAuth2Service

read -p "Press enter to continue"

${OOoProgram}/regview ${Path}/${WorkBench}/types.rdb
