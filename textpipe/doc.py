"""
Clean text, make it readable and obtain metadata from it.
"""

import re
import doctest
from bs4 import BeautifulSoup
from cld2 import detect
import spacy
import textacy
import textacy.text_utils


class Doc:
    """
    Create a doc instance of text, obtain cleaned, readable text and
    metadata from this doc.
    """

    def __init__(self, raw, language=None, pref_language='en'):
        """
        Args:
        raw: incoming, unedited text
        _language: 2-letter code for the language of the text
        _pref_language: language you expect your text to be
        is_detected_language: a boolean indicating if the language was known
            beforehand or detected
        _spacy_nlps: dictionary containing a spacy language module
        _spacy_doc: dictionary containing an instance of a spacy doc
        _text_stats: dictionary containing an instance of textacy textstats
        _clean_text: string containing the cleaned text
        """

        self.raw = raw
        self._language = language
        self._pref_language = pref_language
        self.is_detected_language = language is None
        self._spacy_nlps = {}
        self._spacy_doc = {}
        self._text_stats = {}
        self._clean_text = ''

    @property
    def language(self):
        """Detect the language of a text if no language was provided along with the text

        >>> doc = Doc('Test sentence for testing text', language='en')
        >>> doc.language
        'en'
        >>> doc = Doc('Test sentence for testing text')
        >>> doc.language
        'en'
        """
        if not self._language:
            _, _, best_guesses = detect(self.clean_text, hintLanguage=self._pref_language, bestEffort=True)
            self._language = best_guesses[0][1]
        return self._language

    @property
    def spacy_doc(self):
        """Create a spacy doc and load the language module

        >>> doc = Doc('Test sentence for testing text')
        >>> type(doc.spacy_doc)
        <class 'spacy.tokens.doc.Doc'>

        """
        if not self._spacy_doc:
            lang = self._pref_language if self.language == 'un' else self.language
            if lang not in self._spacy_nlps:
                temp_lang = '_core_web_sm' if lang == 'en' else '_core_news_sm'
                self._spacy_nlps[lang] = spacy.load(lang + temp_lang)
            nlp = self._spacy_nlps[lang]
            self._spacy_doc = nlp(self.clean_text)
        return self._spacy_doc

    @property
    def clean_text(self):
        """Clean HTML and normalise punctuation.

        >>> doc = Doc('“Please clean this piece… of text</b>„')
        >>> doc.clean_text
        '"Please clean this piece... of text"'
        """
        if not self._clean_text:
            if self.raw is not None:
                text = BeautifulSoup(self.raw, 'html.parser').get_text()  # remove HTML
                # Three regexes below adapted from Blendle cleaner.py
                # https://github.com/blendle/research-summarization/blob/master/enrichers/cleaner.py#L29
                text = re.sub('…', '...', text)
                text = re.sub('[`‘’‛⸂⸃⸌⸍⸜⸝]', "'", text)
                text = re.sub('[„“]|(\'\')|(,,)', '"', text)
                self._clean_text = ' '.join([word for word in text.split()
                                             if len(word) > 1])  # remove 1 letter words
            else:
                self._clean_text = ''
        return self._clean_text

    @property
    def ents(self):
        """Extract a list of the named entities in text

        >>> doc = Doc('Sentence for testing RTL text')
        >>> doc.ents
        (RTL,)
        """
        return self.spacy_doc.ents

    @property
    def nsents(self):
        """Extract the number of sentences from text

        >>> doc = Doc('Test sentence. For RTL.')
        >>> doc.nsents
        2
        """
        return len(list(self.spacy_doc.sents))

    @property
    def nwords(self):
        """Extract the number of words from text

        >>> doc = Doc('Sentence for testing RTL text')
        >>> doc.nwords
        5
        """
        return len(self.clean_text.split())

    @property
    def complexity(self):
        """Determine the complexity of text using the Flesch
        reading ease test ranging from 0.0 - 100.0 with 0.0
        being the most difficult to read.

        >>> doc = Doc('Sentence for testing RTL text')
        >>> doc.complexity
        83.32000000000002
        """
        if not self._text_stats:
            self._text_stats = textacy.TextStats(self.spacy_doc)
        return self._text_stats.flesch_readability_ease


if __name__ == "__main__":
    doctest.testmod()
