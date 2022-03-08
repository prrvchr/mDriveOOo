#!/bin/bash
<<COMMENT
╔════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                    ║
║   Copyright (c) 2020 https://prrvchr.github.io                                     ║
║                                                                                    ║
║   Permission is hereby granted, free of charge, to any person obtaining            ║
║   a copy of this software and associated documentation files (the "Software"),     ║
║   to deal in the Software without restriction, including without limitation        ║
║   the rights to use, copy, modify, merge, publish, distribute, sublicense,         ║
║   and/or sell copies of the Software, and to permit persons to whom the Software   ║
║   is furnished to do so, subject to the following conditions:                      ║
║                                                                                    ║
║   The above copyright notice and this permission notice shall be included in       ║
║   all copies or substantial portions of the Software.                              ║
║                                                                                    ║
║   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,                  ║
║   EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES                  ║
║   OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.        ║
║   IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY             ║
║   CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,             ║
║   TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE       ║
║   OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.                                    ║
║                                                                                    ║
╚════════════════════════════════════════════════════════════════════════════════════╝
COMMENT
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
