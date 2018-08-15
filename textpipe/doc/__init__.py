# pylint: disable=too-many-instance-attributes
"""
Clean text, make it readable and obtain metadata from it.
"""

from textpipe.doc.clean import CleanDoc
from textpipe.doc.language import LanguageDoc
from textpipe.doc.spacy import SpacyDoc
from textpipe.doc.textacy import TextacyDoc


class Doc(TextacyDoc, SpacyDoc, LanguageDoc, CleanDoc):
    """
    Create a doc instance of text, obtain cleaned, readable text and
    metadata from this doc.
    """

    def __init__(self, raw, **kwargs):
        """
        Args:
        raw: incoming, unedited text
        """
        CleanDoc.__init__(self, raw, **kwargs)
        LanguageDoc.__init__(self, **kwargs)
        SpacyDoc.__init__(self, **kwargs)
        TextacyDoc.__init__(self, **kwargs)