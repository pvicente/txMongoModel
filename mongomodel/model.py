from twisted.internet import defer
from twisted.python import log

import txmongo

from mongomodel import conn


class Model(object):
    """
    """
    db = ""
    collection = ""

    def __init__(self, pool=True):
        self.connMan = conn.ConnectionManager(pool=pool)

    def insert(self, key, value):

        def _insert(collection):
            return collection.insert({key: value}, safe=True)

        d = self.connMan.getCollection(self.db, self.collection)
        d.addCallback(_insert)
        d.addErrback(log.err)
        return d

    def find(self, fields={}, sortField="", order="asc", **kwargs):
        if "filter" not in kwargs and sortField:
            if order == "asc":
                kwargs["filter"] = self.getAscendingFilter(
                    fields, sortField)

        def _find(collection):
            return collection.find(fields=fields, **kwargs)

        d = self.connMan.getCollection(self.db, self.collection)
        d.addCallback(_find)
        d.addErrback(log.err)
        return d
