import sys


def _print(object, string):
    print object.id + " " + repr(string)[1:]


def _error(object, string):
    print >> sys.stderr, object.id + " " + repr(string)[1:]
