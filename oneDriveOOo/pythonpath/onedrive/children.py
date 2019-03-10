#!
# -*- coding: utf_8 -*-

from .drivelib import ChildGenerator
from .items import mergeJsonItemCall
from .items import mergeJsonItem


def selectChildId(connection, parent, uri):
    id = None
    call = connection.prepareCall('CALL "selectChildId"(?, ?)')
    call.setString(1, parent)
    call.setString(2, uri)
    result = call.executeQuery()
    if result.next():
        id = result.getString(1)
    call.close()
    return id

def updateChildren(session, connection, userid, id):
    merge, index = mergeJsonItemCall(connection, userid)
    update = all(mergeJsonItem(merge, item, index) for item in ChildGenerator(session, id))
    merge.close()
    return update
