from twisted.internet import defer
from twisted.python import log

import txmongo


class ConnectionManager(object):
    """
    """
    def __init__(self, pool=True):
        self.pool = pool
        self._connection = None
        self._db = None
        self._collection = None

    def setConnection(self, conn):
        self._connection = conn
        return self._connection

    def _getConnection(self):
        if self._connection:
            return self._connection
        else:
            if self.pool:
                return txmongo.MongoConnectionPool()
            else:
                return txmongo.MongoConnection()

    def getConnection(self):
        d = defer.maybeDeferred(self._getConnection)
        d.addErrback(log.err)
        d.addCallback(self.setConnection)
        return d

    def setDB(self, ignored, dbName):
        self._db = getattr(self._connection, dbName)
        return self._db

    def _getDB(self, dbName):
        if self._db:
            return self._db
        elif self._connection:
            return self.setDB(None, dbName)
        else:
            d = self.getConnection()
            d.addCallback(self.setDB, dbName)
            d.addErrback(log.err)
            return d

    def getDB(self, dbName):
        return defer.maybeDeferred(self._getDB, dbName)

    def setCollection(self, ignored, collName):
        self._collection = getattr(self._db, collName)
        return self._collection

    def _getCollection(self, dbName, collName):
        if self._collection:
            return self._collection
        else:
            d = self.getDB(dbName)
            d.addCallback(self.setCollection, collName)
            d.addErrback(log.err)
            return d

    def getCollection(self, dbName, collName):
        return defer.maybeDeferred(self._getCollection, dbName, collName)

    def command(self, dbName, command, value=1):

        def _command(db):
            d = db["$cmd"].find_one({command: value})
            d.addErrback(log.err)
            return d

        d = self.getDB(dbName)
        d.addCallback(_command)
        d.addErrback(log.err)
        return d

    def dropDatabase(self, dbName):
        return self.command(dbName, "dropDatabase")
