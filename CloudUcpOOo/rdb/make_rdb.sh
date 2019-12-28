#!/bin/bash

if [ $# -eq 0 ]
    then
        echo "***************************************************************"
        echo "    Usage: make_rdb.sh chemin/du/module/nom_du_fichier(idl)    "
        echo "***************************************************************"
    else
        OOoSDK=/usr/lib/libreoffice/sdk
        OOoProgram=/usr/lib/libreoffice/program
        Path=$(dirname "${0}")
        Component=$(basename "${1}")
        Module=$(dirname "${1}")
        ${OOoSDK}/bin/idlc -verbose -O${Path}/urd/${Module} -I${OOoSDK}/idl -I${Path}/idl ${Path}/idl/${Module}/${Component}.idl
        ${OOoProgram}/regmerge ${Path}/../types.rdb /UCR ${Path}/urd/${Module}/${Component}.urd
fi
