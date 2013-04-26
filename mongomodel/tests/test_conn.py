from twisted.internet.base import DelayedCall
from twisted.python import log
from twisted.trial import unittest

import txmongo

from mongomodel import conn


DelayedCall.debug = True


class ConnectionManagerTestCase(unittest.TestCase):
    """
    """
    def setUp(self):
        self.connMan = conn.ConnectionManager(pool=False)

    def tearDown(self):

        def close(conn):
            d = conn.disconnect()
            d.addErrback(log.err)
            return d

        d = self.connMan.getConnection()
        d.addCallback(close)
        return d

    def test_init(self):
        self.assertEqual(self.connMan._connection, None)
        self.assertEqual(self.connMan._db, None)
        self.assertEqual(self.connMan._collection, None)

    def test_getConnection(self):

        def checkResult(result):
            self.assertEqual(type(result), txmongo.MongoAPI)

        d = self.connMan.getConnection()
        d.addCallback(checkResult)
        return d

    def test_getDB(self):

        dbName = "test-db"

        def checkResult(result):
            self.assertEqual(result._database_name, dbName)

        d = self.connMan.getDB(dbName)
        d.addCallback(checkResult)
        return d

    def test_getCollection(self):

        dbName = "test-db"
        collName = "test-collection"

        def checkResult(result):
            self.assertEqual(result._collection_name, collName)

        d = self.connMan.getCollection("test-db", "test-collection")
        d.addCallback(checkResult)
        return d

