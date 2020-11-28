# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function

import sys

# borrowed largely from gevent 1.0

__all__ = ['patch']


if sys.version_info[0] >= 3:
    string_types = str,
else:
    import __builtin__
    string_types = __builtin__.basestring


# maps module name -> attribute name -> original item
# e.g. "time" -> "sleep" -> built-in function sleep
saved = {}


def _get_original(name, items):
    d = saved.get(name, {})
    values = []
    module = None
    for item in items:
        if item in d:
            values.append(d[item])
        else:
            if module is None:
                module = __import__(name)
            values.append(getattr(module, item))
    return values


def get_original(name, item):
    if isinstance(item, string_types):
        return _get_original(name, [item])[0]
    else:
        return _get_original(name, item)


def patch_item(module, attr, newitem):
    NONE = object()
    olditem = getattr(module, attr, NONE)
    if olditem is not NONE:
        saved.setdefault(module.__name__, {}).setdefault(attr, olditem)
    setattr(module, attr, newitem)


def remove_item(module, attr):
    NONE = object()
    olditem = getattr(module, attr, NONE)
    if olditem is NONE:
        return
    saved.setdefault(module.__name__, {}).setdefault(attr, olditem)
    delattr(module, attr)


def patch_module(name, items=None):
    print("patch_module() 1 %s" % (dir(__import__('backports').ssl), ))
    backported_module = getattr(__import__('backports').ssl, name)
    print("patch_module() 2 %s" % (dir(backported_module), ))
    module_name = getattr(backported_module, '__target__', name)
    module = __import__(module_name)
    if items is None:
        items = getattr(backported_module, '__implements__', None)
        if items is None:
            raise AttributeError('%r does not have __implements__' % backported_module)
    for attr in items:
        patch_item(module, attr, getattr(backported_module, attr))

def patch():
    patch_module('core')
