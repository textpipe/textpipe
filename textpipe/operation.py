# pylint: disable=too-few-public-methods
"""
Operation classes must be defined in this module.

In a future version we might consider adding support for fully qualified paths
when creating a Pipeline, e.g.:
Pipeline['CleanText', 'my.org.package.OperationClass'])

so that users do not have to put their Operation classes inside of this module.
"""


class Operation:
    """
    Base class for pipeline operations.
    """
    def __call__(self, doc):
        raise NotImplementedError()


class CleanText(Operation):
    """
    Clean HTML and normalise punctuation.

    >>> from textpipe.doc import Doc
    >>> doc = Doc('“Please clean this piece… of text</b>„')
    >>> CleanText(**{})(doc)
    '"Please clean this piece... of text"'
    """
    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def __call__(self, doc):
        return doc.clean_text


class Raw(Operation):
    """
    Extract the number of words from text

    >>> from textpipe.doc import Doc
    >>> doc = Doc('Test sentence for testing text')
    >>> Raw(**{})(doc)
    'Test sentence for testing text'
    """
    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def __call__(self, doc):
        return doc.raw


class NWords(Operation):
    """
    Extract the number of words from text

    >>> from textpipe.doc import Doc
    >>> doc = Doc('Test sentence for testing text')
    >>> NWords(**{})(doc)
    5
    """
    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def __call__(self, doc):
        return doc.nwords


class Complexity(Operation):
    """
    Determine the complexity of text using the Flesch
    reading ease test ranging from 0.0 - 100.0 with 0.0
    being the most difficult to read.

    >>> from textpipe.doc import Doc
    >>> doc = Doc('Test sentence for testing text')
    >>> Complexity(**{})(doc)
    83.32000000000004
    """
    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def __call__(self, doc):
        return doc.complexity


class NSentences(Operation):
    """
    Extract the number of sentences from text

    >>> from textpipe.doc import Doc
    >>> doc = Doc('Test sentence for testing text')
    >>> NSentences(**{})(doc)
    1
    """
    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def __call__(self, doc):
        return doc.nsents


class Entities(Operation):
    """
    Extract a list of the named entities in text

    >>> from textpipe.doc import Doc
    >>> doc = Doc('Sentence for testing Google text')
    >>> Entities(**{})(doc)
    [('Google', 'ORG')]
    """
    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def __call__(self, doc):
        return doc.ents
