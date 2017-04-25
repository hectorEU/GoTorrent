#
# This example illusatrates how binary data can be efficiently be passed
# between a bitarray object and an ndarray with dtype bool
#
import numpy

import bitarray

a = bitarray.bitarray('100011001001')
print a

# bitarray  ->  ndarray
b = numpy.fromstring(a.unpack(), dtype=bool)
print repr(b)

# ndarray  ->  bitarray
c = bitarray.bitarray()
c.pack(b.tostring())

assert a == c
