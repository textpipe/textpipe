"""
Textpipe utils.
"""
from functools import reduce


def getattr_(obj, field):
    """Nested getattr"""
    try:
        flist = field.split('.')
        return reduce(getattr, flist, obj)
    except AttributeError:
        return None
