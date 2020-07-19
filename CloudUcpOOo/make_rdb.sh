#!/bin/bash

OOoProgram=/usr/lib/libreoffice/program
Path=$(dirname "${0}")

rm ${Path}/types.rdb

./rdb/make_rdb.sh com/sun/star/auth/XRestKeyMap
./rdb/make_rdb.sh com/sun/star/auth/XInteractionUserName
./rdb/make_rdb.sh com/sun/star/auth/RestRequestTokenType
./rdb/make_rdb.sh com/sun/star/ucb/RestDataSourceSyncMode
./rdb/make_rdb.sh com/sun/star/ucb/XRestProvider
./rdb/make_rdb.sh com/sun/star/ucb/XRestDataBase
./rdb/make_rdb.sh com/sun/star/ucb/RestProvider
./rdb/make_rdb.sh com/sun/star/ucb/XRestDataSource
./rdb/make_rdb.sh com/sun/star/ucb/XRestUser
./rdb/make_rdb.sh com/sun/star/ucb/XRestIdentifier
./rdb/make_rdb.sh com/sun/star/ucb/XRestContent
./rdb/make_rdb.sh com/sun/star/ucb/XRestContentProvider
./rdb/make_rdb.sh com/sun/star/ucb/RestContentProvider

read -p "Press enter to continue"

${OOoProgram}/regview ${Path}/types.rdb
