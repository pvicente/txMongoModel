from conn import ConnectionManager
from twisted.internet import defer, reactor
from twisted.python import log
from txmongo import filter
import types

DELAYED_INDEX_TIME=5
SLEEP_TIME_FUNC = None

class Sort(object):
    @classmethod
    def _get_order(cls, field_list):
        return reduce(lambda x,y: x+y, [filter.DESCENDING(name[1:]) if name[0] == '-' else filter.ASCENDING(name) for name in field_list])
    
    @classmethod
    def getFilter(cls, field_list):
        return filter.sort(cls._get_order(field_list))

class Indexes(object):
    @classmethod
    def get_index_from_string(cls, index):
        """Return an index from simple string. 
        Example: "index_name" (index_name ASCENDING) -index_name (index_name DESCENDING)"""
        sort_fields = Sort.getFilter([index])
        return {'sort_fields': sort_fields}
    
    @classmethod
    def get_index_from_tuple(cls, index):
        """Return an index from elements in tuple. 
        Example ("index_name_1", "index_name_2", "-index_name_3") -> 3 fields Index("index_name_1" ASCENDING, "index_name_2" ASCENDING, "index_name_3" DESCENDING)"""
        sort_fields = Sort.getFilter(index)
        return {'sort_fields': sort_fields}
    
    @classmethod
    def get_index_from_dict(cls, index):
        """Return an index from elements in dict.
        Example {'fields': ("index_name_1", "-index_name_2"), 'name': 'myindex', 'unique': True, 'dropDups': True, 'bucketSize': 2048, 'expireAfterSeconds': 3600
        Return an index ("index_name_1" ASCENDING, "index_name_2" DESCENDING) with name myindex unique dropping duplicates with bucketSize 2048 bytes and fields are removed after 3600 seconds
        """
        fields = index.pop('fields', None)
        if fields is None:
            raise ValueError('Not found key fields in index: %s'%(index))
        if not isinstance(fields, (types.StringType, types.TupleType)):
            raise TypeError('fields key in index must be string or tuple types. Now is %s'%(type(fields)))
        fields = [fields] if isinstance(fields, types.StringType) else fields
        sort_fields = Sort.getFilter(fields)
        ret = {'sort_fields': sort_fields}
        ret.update(index)
        return ret
    
    def __init__(self, indexes=[]):
        if not isinstance(indexes, types.ListType):
            raise TypeError('fields must be a ListType')
        self.indexes = []
        for index in indexes:
            if not isinstance(index, (types.StringType, types.TupleType, types.DictType)):
                raise TypeError('Element %s is not a valid Type'%(str(index)))
            if isinstance(index, types.StringType) and index:
                self.indexes.append(self.get_index_from_string(index))
            elif isinstance(index, types.TupleType) and index:
                self.indexes.append(self.get_index_from_tuple(index))
            else:
                self.indexes.append(self.get_index_from_dict(index))
    
    def create(self, model):
        for index in self.indexes:
            reactor.callLater(DELAYED_INDEX_TIME, model.ensure_index, index)
    
class Model(object):
    """
    """
    db = ""
    collection = ""
    pool = True
    indexes = None
    MAX_RETRY = 3
    RETRY_DELAY = 1
    METRIC_RETRY=0
    METRIC_SAVE = 0

    def __init__(self, logging=None):
        self.connMan = ConnectionManager(pool=self.pool)
        if not self.indexes is None:
            self.indexes.create(self)
        if logging is None:
            logging = log
        self.log = logging

    @defer.inlineCallbacks
    def execute(self, function):
        collection = yield self.connMan.getCollection(self.db, self.collection)
        ret = None

        retries = self.MAX_RETRY
        while retries>0:
            try:
                ret = yield function(collection)
                retries=0
            except Exception, e:
                global SLEEP_TIME_FUNC
                self.METRIC_RETRY+=1
                retries-=1
                if not SLEEP_TIME_FUNC is None:
                    yield SLEEP_TIME_FUNC(self.RETRY_DELAY)

                if retries == 0:
                    msg = "Max retries exceeded: %d. Error performing %r with exception %r. Accumulated errors: %d"%(self.MAX_RETRY, function, e, self.METRIC_RETRY)
                    self.log.err(msg)
                    if reactor.running:
                        self.log.err("Stopping reactor due to many errors with MONGO")
                        reactor.stop()
                    raise e
        defer.returnValue(ret)

    def insert(self, **data):
        def _insert(collection):
            return collection.insert(data, safe=True)

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
    def find(self, spec={}, fields={}, mongofilter=None):
        def _find(collection):
            return collection.find(spec=spec, fields=fields, filter=mongofilter)

        return self.execute(_find)

    def find_one(self, spec=None, fields=None):
        def _find_one(collection):
            return collection.find_one(spec, fields)
        
        return self.execute(_find_one)

    def remove(self, spec):
        def _remove(collection):
            return collection.remove(spec, safe=True)
        
        return self.execute(_remove)

    @defer.inlineCallbacks
    def save(self, doc):
        def _save(collection):
            return collection.save(doc, safe=True)

        ret = {u'ok': 0.0}
        ret = yield self.execute(_save)
        if isinstance(ret, types.DictionaryType) and ret['ok'] == 0.0:
            self.METRIC_SAVE+=1
            self.log.err("Error saving document: %r. Response: %r. Current save metric: %d"%(doc, ret, self.METRIC_SAVE))
        defer.returnValue(ret)
    
    def update(self, spec, upsert=False, multi=False, **data):
        def _update(collection):
            return collection.update(spec, data, upsert=upsert, multi=multi, safe=True)
        
        return self.execute(_update)
    
    def ensure_index(self, index):
        def _ensure_index(collection):
            return collection.ensure_index(**index)
        
        return self.execute(_ensure_index)
    
    def distinct(self, key, spec=None):
        def _distinct(collection):
            return collection.distinct(key, spec)
        
        return self.execute(_distinct)
    
    def count(self, spec=None, fields=None):
        def _count(collection):
            return collection.count(spec, fields)
        
        return self.execute(_count)
    
    def command(self, command, value=1):
        return self.connMan.command(self.db, command, value=value)

    def dropDatabase(self):
        return self.command("dropDatabase")
    
    def stats(self, collection_stats=True):
        if collection_stats:
            return self.command('collStats', self.collection)
        return self.command('dbStats', 1)
    
