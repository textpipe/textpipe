"""
Utility functions for Textpipe.
"""

import functools


def hash_dict(func):
    """
    Transform mutable dictionary into immutable.
    Useful to be compatible with cache.
    """
    class HDict(dict):
        """
        Immutable dict class.
        """
        def __hash__(self):
            return hash(frozenset(self.items()))

    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        args = tuple([HDict(arg) if isinstance(arg, dict) else arg for arg in args])
        kwargs = {k: HDict(v) if isinstance(v, dict) else v for k, v in kwargs.items()}
        return func(*args, **kwargs)
    return wrapped
