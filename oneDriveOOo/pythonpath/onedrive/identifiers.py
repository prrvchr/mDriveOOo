#!
# -*- coding: utf_8 -*-

from .drivelib import IdGenerator
from .drivetools import g_IdentifierRange


def isIdentifier(connection, id):
    retreived = False
    call = connection.prepareCall('CALL "isIdentifier"(?)')
    call.setString(1, id)
    result = call.executeQuery()
    if result.next():
        retreived = result.getBoolean(1)
    call.close()
    return retreived

def checkIdentifiers(connection, session, userid):
    result = True
    if _countIdentifier(connection, userid) < min(g_IdentifierRange):
        result = _insertIdentifier(connection, session, userid, max(g_IdentifierRange))
    return result

def getNewIdentifier(connection, userid):
    select = connection.prepareCall('CALL "selectIdentifier"(?)')
    select.setString(1, userid)
    result = select.executeQuery()
    if result.next():
        id = result.getString(1)
    select.close()
    return id

def _countIdentifier(connection, id):
    count = 0
    call = connection.prepareCall('CALL "countIdentifier"(?)')
    call.setString(1, id)
    result = call.executeQuery()
    if result.next():
        count = result.getLong(1)
    call.close()
    return count

def _insertIdentifier(connection, session, userid, count):
    insert = connection.prepareCall('CALL "insertIdentifier"(?, ?, ?)')
    insert.setString(1, userid)
    result = all(_doInsert(insert, id) for id in IdGenerator(session, count))
    insert.close()
    return result

def _doInsert(insert, id):
    insert.setString(2, id)
    insert.execute()
    return insert.getLong(3)
