from twisted.trial import unittest

from mongomodel import conn


class ConnectionManagerTestCase(unittest.TestCase):
    """
    """
    def setUp(self):
        self.connMan = conn.ConnectionManager()

    def test_init(self):
        self.assertEqual(self.connMan._connection, None)
        self.assertEqual(self.connMan._db, None)
        self.assertEqual(self.connMan._collection, None)
