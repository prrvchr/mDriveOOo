#!/bin/bash

if [ $# -eq 0 ]
    then
        echo "****************************************************************************"
        echo "*   Usage: merge_rdb.sh path/to/OOo_program path/to/module/idl_file_name   *"
        echo "****************************************************************************"
    else
        Path=$(dirname "${0}")
        OOoSDK=${1}/sdk
        OOoProgram=${1}/program
        Component=$(basename "${2}")
        Module=$(dirname "${2}")
        ${OOoSDK}/bin/idlc -verbose -O${Path}/urd/${Module} -I${OOoSDK}/idl -I${Path}/idl ${Path}/idl/${Module}/${Component}.idl
        ${OOoProgram}/regmerge ${Path}/types.rdb /UCR ${Path}/urd/${Module}/${Component}.urd
fi
