#!/bin/bash

OOoPath=/usr/lib/libreoffice
Path=$(dirname "${0}")

rm -f ${Path}/types.rdb

${Path}/merge_rdb.sh ${OOoPath} com/sun/star/auth/RestRequestTokenType
${Path}/merge_rdb.sh ${OOoPath} com/sun/star/auth/RestRequestToken
${Path}/merge_rdb.sh ${OOoPath} com/sun/star/auth/RestRequestEnumerator
${Path}/merge_rdb.sh ${OOoPath} com/sun/star/auth/RestRequestParameter
${Path}/merge_rdb.sh ${OOoPath} com/sun/star/auth/OAuth2Request
${Path}/merge_rdb.sh ${OOoPath} com/sun/star/auth/XRestKeyMap
${Path}/merge_rdb.sh ${OOoPath} com/sun/star/auth/XRestDataParser
${Path}/merge_rdb.sh ${OOoPath} com/sun/star/auth/XRestRequest
${Path}/merge_rdb.sh ${OOoPath} com/sun/star/auth/XRestEnumeration
${Path}/merge_rdb.sh ${OOoPath} com/sun/star/auth/XInteractionUserName
${Path}/merge_rdb.sh ${OOoPath} com/sun/star/auth/XRestUploader
${Path}/merge_rdb.sh ${OOoPath} com/sun/star/auth/XOAuth2Service
${Path}/merge_rdb.sh ${OOoPath} com/sun/star/auth/OAuth2Service

read -p "Press enter to continue"

if test -f "${Path}/types.rdb"; then
    ${OOoPath}/program/regview ${Path}/types.rdb
    read -p "Press enter to continue"
fi
