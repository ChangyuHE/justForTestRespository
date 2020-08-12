from collections import defaultdict

class QueryCache:
    def __init__(self):
        self.__cache = {}

    def get(self, cls):
        queryset_key = cls.__name__
        cached_query = self.__cache.get(queryset_key, None)

        if cached_query is None:
            cached_query = cls.objects.all()
            self.__cache[queryset_key] = cached_query

        return cached_query

    def clear(self, *classes):
        if not classes:
            self.__cache.clear()
        else:
            for cls in classes:
                self.__cache.pop(cls.__name__, None)


class ObjectsCache:
    def __init__(self):
        self.__cache = defaultdict(set)

    def clear(self):
        self.__cache.clear()

    def update(self, cls, id):
        self.__cache[cls.__name__].add(id)

    def is_known(self, cls, id):
        return id in self.__cache.get(cls.__name__, set())
