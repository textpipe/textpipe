import textacy
import textacy.text_utils

from textpipe.doc.spacy import SpacyDoc


class TextacyDoc(SpacyDoc):
    def __init__(self, **kwargs):
        SpacyDoc.__init__(self, **kwargs)
        self._text_stats = {}

    @property
    def complexity(self):
        """
        Determine the complexity of text using the Flesch
        reading ease test ranging from 0.0 - 100.0 with 0.0
        being the most difficult to read.
        >>> from textpipe.doc import Doc
        >>> doc = Doc('Test sentence for testing text')
        >>> doc.complexity
        83.32000000000004
        """
        if not self._text_stats:
            self._text_stats = textacy.TextStats(self.spacy_doc)
        if self._text_stats.n_syllables == 0:
            return 100
        return self._text_stats.flesch_reading_ease