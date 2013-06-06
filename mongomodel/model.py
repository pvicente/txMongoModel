from twisted.internet import defer
from twisted.python import log

from conn import ConnectionManager

class Model(object):
    """
    """
    db = ""
    collection = ""

    def __init__(self, pool=True, **kwargs):
        self.connMan = ConnectionManager(pool=pool)
        self.data = kwargs

    def execute(self, function):
        d = self.connMan.getCollection(self.db, self.collection)
        d.addCallback(function)
        d.addErrback(log.err)
        return d

    def insert(self, **data):
        if data:
            self.data = data

        def _insert(collection):
            return collection.insert(self.data, safe=True)

        return self.execute(_insert)

    def insertMany(self, listOfDicts):

        def _insert(collection):
            deferreds = []
            for data in listOfDicts:
                d = collection.insert(data, safe=True)
                deferreds.append(d)
            d = defer.DeferredList(deferreds)
            d.addErrback(log.err)
            return d

        return self.execute(_insert)

    # XXX Add unit test(s) for find
    def find(self, fields={}, sortField="", order="asc", **kwargs):
        if "filter" not in kwargs and sortField:
            if order == "asc":
                kwargs["filter"] = self.getAscendingFilter(
                    fields, sortField)

        def _find(collection):
            return collection.find(fields=fields, **kwargs)

        return self.execute(_find)

    def find_one(self, spec=None, fields=None):
        def _find_one(collection):
            return collection.find_one(spec, fields)
        
        return self.execute(_find_one)

    def remove(self, spec):
        def _remove(collection):
            return collection.remove(spec, safe=True)
        
        return self.execute(_remove)

    def command(self, command, value=1):
        return self.connMan.command(self.db, command, value=value)

    def dropDatabase(self):
        return self.command("dropDatabase")
