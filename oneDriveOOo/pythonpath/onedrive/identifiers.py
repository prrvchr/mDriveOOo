#!
# -*- coding: utf_8 -*-


def isIdentifier(connection, userid, id):
    retreived = False
    call = connection.prepareCall('CALL "isIdentifier"(?, ?)')
    call.setString(1, userid)
    call.setString(2, id)
    result = call.executeQuery()
    if result.next():
        retreived = result.getBoolean(1)
    call.close()
    return retreived
