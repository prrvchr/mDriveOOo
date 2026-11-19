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

import unohelper

from com.sun.star.awt.PosSize import POSSIZE

from com.sun.star.awt import WindowEvent

from com.sun.star.awt import XWindowListener


class SubLayout(unohelper.Base,
                XWindowListener):
    """Composite layout manager enabling recursive nesting and deferred loading of sub-layouts.

    Wraps a primary `Layout` (or another `SubLayout`) and propagates size deltas from the
    host window down to dynamically registered child layouts. Exposes the same `.window`
    and `.size` interface as `Layout` for seamless polymorphism.

    Args:
        layout (Layout | SubLayout): The root layout instance managed at this level.
    """
    def __init__(self, layout):
        self._layout = layout
        self._subs = []

    @property
    def window(self):
        """XWindow: The underlying UNO container window of the root layout."""
        return self._layout.window

    @property
    def size(self):
        """Rectangle: The factory dimensions of the root layout."""
        return self._layout.size

    def addLayout(self, layout):
        """Registers a child layout and immediately synchronizes it with current window deltas.

        Supports deferred instantiation: if the host window was already resized prior to
        registration, the child layout automatically catches up to the current dimensions.

        Args:
            layout (Layout | SubLayout): The child layout instance to attach.

        Returns:
            SubLayout: Returns `self` to enable method chaining.
        """
        if layout not in self._subs:
            self._subs.append(layout)
            event = WindowEvent()
            event.Source = self.window
            self.windowResized(event)
        return self

    def windowResized(self, event):
        """Propagates resize events to the root layout and cascades size deltas to all children.

        Args:
            event (WindowEvent): The UNO window resize event.
        """
        self._layout.windowResized(event)

        possize = self.window.getPosSize()
        width = possize.Width - self.size.Width
        height = possize.Height - self.size.Height

        for layout in self._subs:
            size = layout.size
            layout.window.setPosSize(0, 0, size.Width + width, size.Height + height, POSSIZE)
            event = WindowEvent()
            event.Source = layout.window
            layout.windowResized(event)

    def windowMoved(self, event):
        pass

    def windowShown(self, event):
        pass

    def windowHidden(self, event):
        pass

    def disposing(self, event):
        pass
