from numpy import unravel_index, ravel_multi_index, prod

from bolt.utils import argpack, istransposeable, isreshapeable
from bolt.spark.array import BoltArraySpark


class Shapes(object):

    @property
    def shape(self):
        raise NotImplementedError

    @property
    def ndim(self):
        return len(self.shape)

    def reshape(self):
        raise NotImplementedError

    def transpose(self):
        raise NotImplementedError

class Keys(Shapes):

    def __init__(self, barray):
        self._barray = barray

    @property
    def shape(self):
        return self._barray.shape[:self._barray.split]

    def reshape(self, *shape):

        new = argpack(shape)
        old = self.shape
        isreshapeable(new, old)

        if new == old:
            return self._barray

        def f(k):
            return unravel_index(ravel_multi_index(k, old), new)

        newrdd = self._barray._rdd.map(lambda kv: (f(kv[0]), kv[1]))
        newsplit = len(new)
        newshape = new + self._barray.values.shape

        return BoltArraySpark(newrdd, shape=newshape, split=newsplit)

    def transpose(self, *axes):

        new = argpack(axes)
        old = range(self.ndim) 
        istransposeable(new, old)

        if new == old:
            return self._barray

        def f(k):
            return tuple(k[i] for i in new)

        newrdd = self._barray._rdd.map(lambda kv: (f(kv[0]), kv[1]))
        newshape = tuple(self.shape[i] for i in new) + self._barray.values.shape

        return BoltArraySpark(newrdd, shape=newshape).__finalize__(self._barray)

    def __str__(self):
        s = "BoltArray Keys\n"
        s += "shape: %s" % str(self.shape)
        return s

    def __repr__(self):
        return str(self)

class Values(Shapes):

    def __init__(self, barray):
        self._barray = barray

    @property
    def shape(self):
        return self._barray.shape[self._barray.split:]

    def reshape(self, *shape):

        new = argpack(shape)
        old = self.shape 
        isreshapeable(new, old)

        if new == old:
            return self._barray

        def f(v):
            return v.reshape(new)

        newrdd = self._barray._rdd.mapValues(f)
        newshape = self._barray.keys.shape + new

        return BoltArraySpark(newrdd, shape=newshape).__finalize__(self._barray)

    def transpose(self, *axes):

        new = argpack(axes)
        old = range(self.ndim) 
        istransposeable(new, old)

        if new == old:
            return self._barray

        def f(v):
            return v.transpose(new)

        newrdd = self._barray._rdd.mapValues(f)
        newshape = self._barray.keys.shape + tuple(self.shape[i] for i in new)

        return BoltArraySpark(newrdd, shape=newshape).__finalize__(self._barray)

    def __str__(self):
        s = "BoltArray Values\n"
        s += "shape: %s" % str(self.shape)
        return s

    def __repr__(self):
        return str(self)
