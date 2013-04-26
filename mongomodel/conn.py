from twisted.internet import defer
from twisted.python import log

import txmongo

class ConnectionManager(object):
    """
    """
    def __init__(self):
        self._connection = None
        self._db = None
        self._collection = None

    def setConnection(self, conn):
        self._connection = conn
        return self._connection

    def getConnection(self):
        if self._connection:
            result = self._connection
        else:
            result = txmongo.MongoConnectionPool()
        d = defer.maybeDeferred(result)
        d.addErrback(log.err)
        d.addCallback(setConnection)
        return d

    def setDB(self, ignored, dbName):
        self._db = getattr(self._connection, dbName)
        return self._db

    def getDB(self, dbName):
        if self._db:
            result = self._db
        elif self._connection:
            result = self.setDB(dbName)
        else:
            result = self.getConnection()
            result.addCallback(setDB, dbName)
        d = defer.maybeDeferred(result)
        d.addErrback(log.err)
        return d

    def setCollection(self, ignored, collName):
        self._collection = getattr(self._db, collName)
        return self._collection

    def getCollection(self, dbName, collName):
        if self._collection:
            result = self._collection
        else:
            result = self.getDB(dbName)
            result.addCallback(setCollection, collName)
        d = defer.maybeDeferred(result)
        d.addErrback(log.err)
        return d
            

