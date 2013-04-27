from twisted.internet.base import DelayedCall
from twisted.python import log
from twisted.trial import unittest

import txmongo
from txmongo._pymongo import objectid

from mongomodel import model


DelayedCall.debug = True


class TestModel(model.Model):
    "Just a test model"
    db = "test-db"
    collection = "test-collection"


class ModelTestCase(unittest.TestCase):
    """
    """
    def setUp(self):
        self.model = TestModel(pool=False)

    def tearDown(self):

        def close(conn):
            d = conn.disconnect()
            d.addErrback(log.err)
            return d

        d = self.model.connMan.getConnection()
        d.addCallback(close)
        return d

    def test_init(self):

        def checkResult(result):
            self.assertEqual(type(result), txmongo.MongoAPI)

        d = self.model.connMan.getConnection()
        d.addCallback(checkResult)
        return d

    def test_insert_one(self):

        def checkResult(result):
            self.assertEqual(type(result), objectid.ObjectId)

        d = self.model.insert("my key", "my value")
        d.addCallback(checkResult)
        return d
