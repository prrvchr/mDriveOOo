#!
# -*- coding: utf_8 -*-

import uno
import unohelper

from com.sun.star.lang import XEventListener
from com.sun.star.logging.LogLevel import INFO
from com.sun.star.logging.LogLevel import SEVERE
from com.sun.star.sdb.CommandType import QUERY
from com.sun.star.ucb import XRestDataSource
from com.sun.star.ucb.ConnectionMode import ONLINE
from com.sun.star.ucb.RestDataSourceSyncMode import SYNC_RETRIEVED
from com.sun.star.ucb.RestDataSourceSyncMode import SYNC_CREATED
from com.sun.star.ucb.RestDataSourceSyncMode import SYNC_FOLDER
from com.sun.star.ucb.RestDataSourceSyncMode import SYNC_FILE
from com.sun.star.ucb.RestDataSourceSyncMode import SYNC_RENAMED
from com.sun.star.ucb.RestDataSourceSyncMode import SYNC_REWRITED
from com.sun.star.ucb.RestDataSourceSyncMode import SYNC_TRASHED

from unolib import KeyMap
from unolib import parseDateTime
from unolib import getResourceLocation

from .user import User
from .dbinit import getDataSourceUrl
from .dbqueries import getSqlQuery
from .dbtools import getDataBaseConnection
from .dbtools import getKeyMapFromResult
from .dbtools import getSequenceFromResult
from .logger import logMessage

import binascii
import traceback


class DataSource(unohelper.Base,
                 XRestDataSource):
    def __init__(self, ctx, scheme, plugin):
        level = SEVERE
        msg = "DataSource for Scheme: %s loading ... " % scheme
        self.ctx = ctx
        logMessage(self.ctx, INFO, "stage 1", 'DataSource', '__init__()')
        self._Statement = None
        self._CahedUser = {}
        self._Calls = {}
        self._Error = ''
        service = '%s.Provider' % plugin
        self.Provider = self.ctx.ServiceManager.createInstanceWithContext(service, self.ctx)
        dbcontext = self.ctx.ServiceManager.createInstance('com.sun.star.sdb.DatabaseContext')
        logMessage(self.ctx, INFO, "stage 2", 'DataSource', '__init__()')
        url, error = getDataSourceUrl(self.ctx, dbcontext, scheme, plugin, True)
        logMessage(self.ctx, INFO, "stage 3", 'DataSource', '__init__()')
        if error is None:
            logMessage(self.ctx, INFO, "stage 4", 'DataSource', '__init__()')
            connection, error = getDataBaseConnection(dbcontext, url)
            if error is not None:
                msg += " ... Error: %s - %s" % (error, traceback.print_exc())
                msg += "Could not connect to DataSource at URL: %s" % url
                self._Error = msg
            else:
                logMessage(self.ctx, INFO, "stage 5", 'DataSource', '__init__()')
                # Piggyback DataBase Connections (easy and clean ShutDown ;-) )
                self._Statement = connection.createStatement()
                folder, link = self._getContentType()
                self.Provider.initialize(scheme, plugin, folder, link)
                level = INFO
                msg += "Done"
        else:
            logMessage(self.ctx, INFO, "stage 6", 'DataSource', '__init__()')
            self._Error = error.Message
        logMessage(self.ctx, level, msg, 'DataSource', '__init__()')

    @property
    def Connection(self):
        return self._Statement.getConnection()
    @property
    def IsValid(self):
        return not self.Error
    @property
    def Error(self):
        return self.Provider.Error if self.Provider and self.Provider.Error else self._Error

    def getUser(self, name):
        print("DataSource.getUser() 1")
        # User never change... we can cache it...
        if name in self._CahedUser:
            user = self._CahedUser[name]
        else:
            user = User(self.ctx)
            if user.initialize(self, name):
                self.checkNewIdentifier(user.Request, user.MetaData)
                self._CahedUser[name] = user
                print("DataSource.getUser() 2")
        print("DataSource.getUser() 3")
        return user

    def selectUser(self, name):
        user = None
        select = self._getDataSourceCall('getUser')
        select.setString(1, name)
        result = select.executeQuery()
        if result.next():
            user = getKeyMapFromResult(result)
        select.close()
        return user

    def insertUser(self, user, root):
        userid = self.Provider.getUserId(user)
        username = self.Provider.getUserName(user)
        displayname = self.Provider.getUserDisplayName(user)
        rootid = self.Provider.getRootId(root)
        timestamp = parseDateTime()
        insert = self._getDataSourceCall('insertUser')
        insert.setString(1, username)
        insert.setString(2, displayname)
        insert.setString(3, rootid)
        insert.setTimestamp(4, timestamp)
        insert.setString(5, userid)
        insert.execute()
        insert.close()
        if not self._executeRootCall('update', userid, root, timestamp):
            self._executeRootCall('insert', userid, root, timestamp)
        data = KeyMap()
        data.insertValue('UserId', userid)
        data.insertValue('UserName', username)
        data.insertValue('RootId', rootid)
        data.insertValue('RootName', self.Provider.getRootTitle(root))
        return data

    def selectItem(self, user, identifier):
        item = None
        select = self._getDataSourceCall('getItem')
        select.setString(1, user.getValue('UserId'))
        select.setString(2, identifier.getValue('Id'))
        result = select.executeQuery()
        if result.next():
            item = getKeyMapFromResult(result, KeyMap())
        select.close()
        return item

    def insertItem(self, user, item):
        timestamp = parseDateTime()
        rootid = user.getValue('RootId')
        c1 = self._getDataSourceCall('deleteParent')
        c2 = self._getDataSourceCall('insertParent')
        if not self._prepareItemCall('update', c1, c2, user, item, timestamp):
            self._prepareItemCall('insert', c1, c2, user, item, timestamp)
        c1.close()
        c2.close()
        id = self.Provider.getItemId(item)
        identifier = KeyMap()
        identifier.insertValue('Id', id)
        return self.selectItem(user, identifier)

    def _getContentType(self):
        call = self._getDataSourceCall('getContentType')
        result = call.executeQuery()
        if result.next():
            item = getKeyMapFromResult(result)
        call.close()
        return item.getValue('Folder'), item.getValue('Link')

    def _executeRootCall(self, method, userid, root, timestamp):
        row = 0
        id = self.Provider.getRootId(root)
        call = self._getDataSourceCall('%sItem' % method)
        call.setString(1, self.Provider.getRootTitle(root))
        call.setTimestamp(2, self.Provider.getRootCreated(root, timestamp))
        call.setTimestamp(3, self.Provider.getRootModified(root, timestamp))
        call.setString(4, self.Provider.getRootMediaType(root))
        call.setLong(5, self.Provider.getRootSize(root))
        call.setBoolean(6, self.Provider.getRootTrashed(root))
        call.setString(7, id)
        row = call.executeUpdate()
        call.close()
        if row:
            call = self._getDataSourceCall('%sCapability' % method)
            call.setBoolean(1, self.Provider.getRootCanAddChild(root))
            call.setBoolean(2, self.Provider.getRootCanRename(root))
            call.setBoolean(3, self.Provider.getRootIsReadOnly(root))
            call.setBoolean(4, self.Provider.getRootIsVersionable(root))
            call.setString(5, userid)
            call.setString(6, id)
            call.executeUpdate()
            call.close()
        return row

    def _prepareItemCall(self, method, delete, insert, user, item, timestamp):
        row = 0
        userid = user.getValue('UserId')
        rootid = user.getValue('RootId')
        c1 = self._getDataSourceCall('%sItem' % method)
        c2 = self._getDataSourceCall('%sCapability' % method)
        row = self._executeItemCall(c1, c2, delete, insert, userid, rootid, item, timestamp)
        c1.close()
        c2.close()
        return row

    def _executeItemCall(self, c1, c2, c3, c4, userid, rootid, item, timestamp):
        row = 0
        id = self.Provider.getItemId(item)
        c1.setString(1, self.Provider.getItemTitle(item))
        c1.setTimestamp(2, self.Provider.getItemCreated(item, timestamp))
        c1.setTimestamp(3, self.Provider.getItemModified(item, timestamp))
        c1.setString(4, self.Provider.getItemMediaType(item))
        c1.setLong(5, self.Provider.getItemSize(item))
        c1.setBoolean(6, self.Provider.getItemTrashed(item))
        c1.setString(7, id)
        row = c1.executeUpdate()
        if row:
            c2.setBoolean(1, self.Provider.getItemCanAddChild(item))
            c2.setBoolean(2, self.Provider.getItemCanRename(item))
            c2.setBoolean(3, self.Provider.getItemIsReadOnly(item))
            c2.setBoolean(4, self.Provider.getItemIsVersionable(item))
            c2.setString(5, userid)
            c2.setString(6, id)
            c2.executeUpdate()
            c3.setString(1, userid)
            c3.setString(2, id)
            c3.executeUpdate()
            c4.setString(1, userid)
            c4.setString(2, id)
            for parent in self.Provider.getItemParent(item, rootid):
                c4.setString(3, parent)
                c4.executeUpdate()
        return row

    def getDocumentContent(self, request, content):
        return self.Provider.getDocumentContent(request, content)
    def getFolderContent(self, request, user, identifier, content, updated):
        if ONLINE == content.getValue('Loaded') == self.Provider.SessionMode:
            updated = self._updateFolderContent(request, user, content)
        select = self._getChildren(user, identifier)
        return select, updated

    def _updateFolderContent(self, request, user, content):
        updated = []
        c1 = self._getDataSourceCall('updateItem')
        c2 = self._getDataSourceCall('updateCapability')
        c3 = self._getDataSourceCall('insertItem')
        c4 = self._getDataSourceCall('insertCapability')
        c5 = self._getDataSourceCall('deleteParent')
        c6 = self._getDataSourceCall('insertParent')
        userid = user.getValue('UserId')
        rootid = user.getValue('RootId')
        timestamp = parseDateTime()
        enumerator = self.Provider.getFolderContent(request, content)
        while enumerator.hasMoreElements():
            item = enumerator.nextElement()
            print("datasource._updateFolderContent() %s" % (item, ))
            updated.append(self._mergeItem(c1, c2, c3, c4, c5, c6, userid, rootid, item, timestamp))
        c1.close()
        c2.close()
        c3.close()
        c4.close()
        c5.close()
        c6.close()
        return all(updated)

    def _mergeItem(self, c1, c2, c3, c4, c5, c6, userid, rootid, item, timestamp):
        row = self._executeItemCall(c1, c2, c5, c6, userid, rootid, item, timestamp)
        if not row:
            row = self._executeItemCall(c3, c4, c5, c6, userid, rootid, item, timestamp)
        return row

    def _getChildren(self, user, identifier):
        select = self._getDataSourceCall('getChildren')
        scroll = 'com.sun.star.sdbc.ResultSetType.SCROLL_INSENSITIVE'
        select.ResultSetType = uno.getConstantByName(scroll)
        # OpenOffice / LibreOffice Columns:
        #    ['Title', 'Size', 'DateModified', 'DateCreated', 'IsFolder', 'TargetURL', 'IsHidden',
        #    'IsVolume', 'IsRemote', 'IsRemoveable', 'IsFloppy', 'IsCompactDisc']
        # "TargetURL" is done by:
        #    CONCAT(BaseURL,'/',Id) for Foder or CONCAT(BaseURL,'/',Title) for File.
        url = identifier.getValue('BaseURL')
        select.setString(1, url)
        select.setString(2, url)
        select.setString(3, user.getValue('UserId'))
        select.setString(4, identifier.getValue('Id'))
        select.setShort(5, self.Provider.SessionMode)
        return select

    def checkNewIdentifier(self, request, user):
        if self.Provider.isOffLine() or not self.Provider.GenerateIds:
            return
        result = False
        if self._countIdentifier(user) < min(self.Provider.IdentifierRange):
            result = self._insertIdentifier(request, user)
        return
    def getNewIdentifier(self, user):
        if self.Provider.GenerateIds:
            id = ''
            select = self._getDataSourceCall('getNewIdentifier')
            select.setString(1, user.getValue('UserId'))
            result = select.executeQuery()
            if result.next():
                id = result.getString(1)
            select.close()
        else:
            id = binascii.hexlify(uno.generateUuid().value).decode('utf-8')
        return id

    def _countIdentifier(self, user):
        count = 0
        call = self._getDataSourceCall('countNewIdentifier')
        call.setString(1, user.getValue('UserId'))
        result = call.executeQuery()
        if result.next():
            count = result.getLong(1)
        call.close()
        return count
    def _insertIdentifier(self, request, user):
        result = []
        enumerator = self.Provider.getIdentifier(request, user)
        insert = self._getDataSourceCall('insertIdentifier')
        insert.setString(1, user.getValue('UserId'))
        while enumerator.hasMoreElements():
            item = enumerator.nextElement()
            print("datasource._insertIdentifier() %s" % (item, ))
            result.append(self._doInsert(insert, item))
        insert.close()
        return all(result)
    def _doInsert(self, insert, id):
        insert.setString(2, id)
        return insert.executeUpdate()

    def getItemToSync(self, user):
        items = []
        select = self._getDataSourceCall('getItemToSync')
        select.setString(1, user.getValue('UserId'))
        result = select.executeQuery()
        while result.next():
            items.append(getKeyMapFromResult(result, user, self.Provider))
        select.close()
        msg = "Items to Sync: %s" % len(items)
        logMessage(self.ctx, INFO, msg, "DataSource", "_getItemToSync()")
        return tuple(items)

    def syncItem(self, request, uploader, item):
        try:
            response = False
            mode = item.getValue('Mode')
            sync = item.getValue('SyncId')
            id = item.getValue('Id')
            msg = "SyncId - ItemId - Mode: %s - %s - %s" % (sync, id, mode)
            logMessage(self.ctx, INFO, msg, "DataSource", "_syncItem()")
            if mode == SYNC_FOLDER:
                response = self.Provider.createFolder(request, item)
            elif mode == SYNC_FILE:
                response = self.Provider.createFile(request, uploader, item)
            elif mode == SYNC_CREATED:
                response = self.Provider.uploadFile(request, uploader, item, True)
            elif mode == SYNC_REWRITED:
                response = self.Provider.uploadFile(request, uploader, item, False)
            elif mode == SYNC_RENAMED:
                response = self.Provider.updateTitle(request, item)
            elif mode == SYNC_TRASHED:
                response = self.Provider.updateTrashed(request, item)
            return response
        except Exception as e:
            msg = "SyncId: %s - ERROR: %s - %s" % (sync, e, traceback.print_exc())
            logMessage(self.ctx, SEVERE, msg, "DataSource", "_syncItem()")

    def callBack(self, item, response):
        if response.IsPresent:
            self.updateSync(item, response.Value)

    def updateSync(self, item, response):
        oldid = item.getValue('Id')
        newid = self.Provider.getResponseId(response, oldid)
        oldname = item.getValue('Title')
        newname = self.Provider.getResponseTitle(response, oldname)
        delete = self._getDataSourceCall('deleteSyncMode')
        delete.setLong(1, item.getValue('SyncId'))
        row = delete.executeUpdate()
        msg = "execute deleteSyncMode OldId: %s - NewId: %s - Row: %s" % (oldid, newid, row)
        logMessage(self.ctx, INFO, msg, "DataSource", "updateSync")
        delete.close()
        if row and newid != oldid:
            update = self._getDataSourceCall('updateItemId')
            update.setString(1, newid)
            update.setString(2, oldid)
            row = update.executeUpdate()
            msg = "execute updateItemId OldId: %s - NewId: %s - Row: %s" % (oldid, newid, row)
            logMessage(self.ctx, INFO, msg, "DataSource", "updateSync")
            update.close()
        return '' if row != 1 else newid

    def insertNewDocument(self, userid, itemid, parentid, content):
        modes = self.Provider.FileSyncModes
        return self._insertNewContent(userid, itemid, parentid, content, modes)
    def insertNewFolder(self, userid, itemid, parentid, content):
        modes = self.Provider.FolderSyncModes
        return self._insertNewContent(userid, itemid, parentid, content, modes)

    def _insertNewContent(self, userid, itemid, parentid, content, modes):
        c1 = self._getDataSourceCall('insertItem')
        c1.setString(1, content.getValue("Title"))
        c1.setTimestamp(2, content.getValue('DateCreated'))
        c1.setTimestamp(3, content.getValue('DateModified'))
        c1.setString(4, content.getValue('MediaType'))
        c1.setLong(5, content.getValue('Size'))
        c1.setBoolean(6, content.getValue('Trashed'))
        c1.setString(7, itemid)
        row = c1.executeUpdate()
        c1.close()
        c2 = self._getDataSourceCall('insertCapability')
        c2.setBoolean(1, content.getValue('CanAddChild'))
        c2.setBoolean(2, content.getValue('CanRename'))
        c2.setBoolean(3, content.getValue('IsReadOnly'))
        c2.setBoolean(4, content.getValue('IsVersionable'))
        c2.setString(5, userid)
        c2.setString(6, itemid)
        row += c2.executeUpdate()
        c2.close()
        c3 = self._getDataSourceCall('insertParent')
        c3.setString(1, userid)
        c3.setString(2, itemid)
        c3.setString(3, parentid)
        row += c3.executeUpdate()
        c3.close()
        c4 = self._getDataSourceCall('insertSyncMode')
        c4.setString(1, userid)
        c4.setString(2, itemid)
        c4.setString(3, parentid)
        for mode in modes:
            c4.setLong(4, mode)
            row += c4.execute()
        c4.close()
        return row == 3 + len(modes)

    def updateLoaded(self, userid, itemid, value, default):
        update = self._getDataSourceCall('updateLoaded')
        update.setLong(1, value)
        update.setString(2, itemid)
        row = update.executeUpdate()
        update.close()
        return default if row != 1 else value

    def updateTitle(self, userid, itemid, parentid, value, default):
        row = 0
        update = self._getDataSourceCall('updateTitle')
        update.setString(1, value)
        update.setString(2, itemid)
        if update.executeUpdate():
            insert = self._getDataSourceCall('insertSyncMode')
            insert.setString(1, userid)
            insert.setString(2, itemid)
            insert.setString(3, parentid)
            insert.setLong(4, SYNC_RENAMED)
            row = insert.executeUpdate()
            insert.close()
        update.close()
        return default if row != 1 else value

    def updateSize(self, userid, itemid, parentid, size):
        row = 0
        update = self._getDataSourceCall('updateSize')
        update.setLong(1, size)
        update.setString(2, itemid)
        if update.executeUpdate():
            insert = self._getDataSourceCall('insertSyncMode')
            insert.setString(1, userid)
            insert.setString(2, itemid)
            insert.setString(3, parentid)
            insert.setLong(4, SYNC_REWRITED)
            row = insert.executeUpdate()
            insert.close()
        update.close()
        return None if row != 1 else size

    def updateTrashed(self, userid, itemid, parentid, value, default):
        row = 0
        update = self._getDataSourceCall('updateTrashed')
        update.setLong(1, value)
        update.setString(2, itemid)
        if update.executeUpdate():
            insert = self._getDataSourceCall('insertSyncMode')
            insert.setString(1, userid)
            insert.setString(2, itemid)
            insert.setString(3, parentid)
            insert.setLong(4, SYNC_TRASHED)
            row = insert.executeUpdate()
            insert.close()
        update.close()
        return default if row != 1 else value

    def isChildId(self, userid, itemid, title):
        ischild = False
        call = self._getDataSourceCall('isChildId')
        call.setString(1, userid)
        call.setString(2, itemid)
        call.setString(3, title)
        result = call.executeQuery()
        if result.next():
            ischild = result.getBoolean(1)
        call.close()
        return ischild

    def countChildTitle(self, userid, parent, title):
        count = 1
        call = self._getDataSourceCall('countChildTitle')
        call.setString(1, userid)
        call.setString(2, parent)
        call.setString(3, title)
        result = call.executeQuery()
        if result.next():
            count = result.getLong(1)
        call.close()
        return count

    # User.initializeIdentifier() helper
    def selectChildId(self, userid, parent, basename):
        id = ''
        call = self._getDataSourceCall('getChildId')
        call.setString(1, userid)
        call.setString(2, parent)
        call.setString(3, basename)
        result = call.executeQuery()
        if result.next():
            id = result.getString(1)
        call.close()
        return id

    # User.initializeIdentifier() helper
    def isIdentifier(self, userid, id):
        isit = False
        call = self._getDataSourceCall('isIdentifier')
        call.setString(1, id)
        result = call.executeQuery()
        if result.next():
            isit = result.getBoolean(1)
        call.close()
        return isit

    def _getDataSourceCall(self, name, cache=False):
        if name in self._Calls:
            return self._Calls[name]
        else:
            query = getSqlQuery(name)
            call = self.Connection.prepareCall(query)
            if cache:
                self._Calls[name] = call
        return call

    def synchronize(self):
        try:
            print("DataSource.synchronize() 1")
            results = []
            for user in self._CahedUser.values():
                uploader = user.Request.getUploader(self)
                for item in self.getItemToSync(user.MetaData):
                    response = self.syncItem(user.Request, uploader, item)
                    if response is None:
                        results.append(True)
                    elif response and response.IsPresent:
                        results.append(self.updateSync(item, response.Value))
                    else:
                        msg = "ERROR: ItemId: %s" % item.getDefaultValue('Id')
                        logMessage(self.ctx, SEVERE, msg, "DataSource", "synchronize()")
                        results.append(False)
            result = all(results)
            print("DataSource.synchronize() 2 %s" % result)
        except Exception as e:
            print("DataSource.synchronize() ERROR: %s - %s" % (e, traceback.print_exc()))
