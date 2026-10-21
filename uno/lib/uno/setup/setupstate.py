#!
# -*- coding: utf-8 -*-

"""
╔════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                    ║
║   Copyright (c) 2020-25 https://prrvchr.github.io                                  ║
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
"""

from ..configuration import State

from dataclasses import dataclass
from dataclasses import InitVar


@dataclass
class SetupState:
    state: InitVar[bool] = True

    extension: bool = True
    jcode: int = 0
    database: bool = True
    pcode: int = 0

    def __post_init__(self, state: bool):
        if not state:
            self.extension = False
            self.jcode = 6
            self.database = False
            self.pcode = 2

    @property
    def java(self) -> bool:
        return self.jcode == 0

    @property
    def python(self) -> bool:
        return self.pcode == 0

    @property
    def restart(self) -> bool:
        return State.restart

    @property
    def runnable(self) -> bool:
        return all([self.extension, self.java, self.python]) and not self.restart

    @property
    def step(self) -> int:
        if not self.extension:
            return 2
        if not self.java:
            return 2 + self.jcode
        if not self.database:
            return 9
        if not self.python:
            return 9 + self.pcode
        if self.restart:
            return 14
        return 1

