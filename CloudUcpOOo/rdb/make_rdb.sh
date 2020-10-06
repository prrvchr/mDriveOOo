#!/bin/bash

OOoPath=/usr/lib/libreoffice
Path=$(dirname "${0}")

rm -f ${Path}/types.rdb

${Path}/merge_rdb.sh ${OOoPath} com/sun/star/auth/XRestKeyMap
${Path}/merge_rdb.sh ${OOoPath} com/sun/star/auth/XInteractionUserName
${Path}/merge_rdb.sh ${OOoPath} com/sun/star/auth/RestRequestTokenType
${Path}/merge_rdb.sh ${OOoPath} com/sun/star/ucb/RestDataSourceSyncMode
${Path}/merge_rdb.sh ${OOoPath} com/sun/star/ucb/XRestProvider
${Path}/merge_rdb.sh ${OOoPath} com/sun/star/ucb/XRestDataBase
${Path}/merge_rdb.sh ${OOoPath} com/sun/star/ucb/XRestReplicator
${Path}/merge_rdb.sh ${OOoPath} com/sun/star/ucb/RestProvider
${Path}/merge_rdb.sh ${OOoPath} com/sun/star/ucb/XRestUser
${Path}/merge_rdb.sh ${OOoPath} com/sun/star/ucb/XRestIdentifier
${Path}/merge_rdb.sh ${OOoPath} com/sun/star/ucb/XRestDataSource
${Path}/merge_rdb.sh ${OOoPath} com/sun/star/ucb/XRestContent
${Path}/merge_rdb.sh ${OOoPath} com/sun/star/ucb/XRestContentProvider
${Path}/merge_rdb.sh ${OOoPath} com/sun/star/ucb/RestContentProvider

read -p "Press enter to continue"

if test -f "${Path}/types.rdb"; then
    ${OOoPath}/program/regview ${Path}/types.rdb
    read -p "Press enter to continue"
fi
