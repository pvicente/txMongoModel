from twisted.internet import defer
from twisted.python import log

import txmongo

from mongomodel import conn


class Model(object):
    """
    """
    db = ""
    collection = ""

    def __init__(self, pool=True, **kwargs):
        self.connMan = conn.ConnectionManager(pool=pool)
        self.data = kwargs

    def execute(self, function):
        d = self.connMan.getCollection(self.db, self.collection)
        d.addCallback(function)
        d.addErrback(log.err)
        return d

    def insertOne(self, key, value):

        def _insert(collection):
            return collection.insert({key: value}, safe=True)

        return self.execute(_insert)

    def insertMany(self, dataDict):

        def _insert(collection):
            deferreds = []
            for key, value in dataDict.items():
                d = collection.insert({key: value}, safe=True)
                deferreds.append(d)
            d = defer.DeferredList(deferreds)
            d.addErrback(log.err)
            return d

        return self.execute(_insert)

    def insert(self, key="", value="", data={}):
        if data:
            return self.insertMany(data)
        elif key:
            return self.insertOne(key, value)

    def find(self, fields={}, sortField="", order="asc", **kwargs):
        if "filter" not in kwargs and sortField:
            if order == "asc":
                kwargs["filter"] = self.getAscendingFilter(
                    fields, sortField)

        def _find(collection):
            return collection.find(fields=fields, **kwargs)

        return self.execute(_find)
