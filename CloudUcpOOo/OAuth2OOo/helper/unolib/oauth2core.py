#!
# -*- coding: utf-8 -*-

#from __futur__ import absolute_import

import uno

from .oauth2lib import InteractionRequest
from .unotools import getInteractionHandler


def getUserNameFromHandler(ctx, source, name, message=''):
    username = ''
    handler = getInteractionHandler(ctx)
    response = uno.createUnoStruct('com.sun.star.beans.Optional<string>')
    interaction = InteractionRequest(source, name, message, response)
    if handler.handleInteractionRequest(interaction):
        if response.IsPresent:
            username = response.Value
    return username
