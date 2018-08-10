# pylint: disable=too-many-instance-attributes
"""
Clean text, make it readable and obtain metadata from it.
"""

import re
import functools

from bs4 import BeautifulSoup
import cld2
import spacy
import textacy
import textacy.text_utils


class Doc:
    """
    Create a doc instance of text, obtain cleaned, readable text and
    metadata from this doc.
    """

    def __init__(self, raw, language=None, hint_language='en'):
        """
        Args:
        raw: incoming, unedited text
        is_detected_language: a boolean indicating if the language was specified
                              beforehand or detected
        _language: 2-letter code for the language of the text
        _hint_language: language you expect your text to be
        _clean: string containing the cleaned text
        _spacy_nlps: dictionary containing a spacy language module
        _spacy_doc: dictionary containing an instance of a spacy doc
        _text_stats: dictionary containing an instance of textacy textstats
        """

        self.raw = raw
        self.is_detected_language = language is None
        self._language = language
        self._hint_language = hint_language
        self._spacy_nlps = {}
        self._spacy_doc = {}
        self._text_stats = {}

    @property
    def language(self):
        """
        Detect the language of a text if no language was provided along with the text

        >>> doc = Doc('Test sentence for testing text', language='en')
        >>> doc.language
        'en'
        >>> doc = Doc('Test sentence for testing text')
        >>> doc.language
        'en'
        """
        if not self._language:
            _, _, best_guesses = cld2.detect(self.clean, hintLanguage=self._hint_language,
                                             bestEffort=True)
            self._language = best_guesses[0][1]
        return self._language

    @property
    def spacy_doc(self):
        """
        Create a spacy doc and load the language module

        >>> doc = Doc('Test sentence for testing text')
        >>> type(doc.spacy_doc)
        <class 'spacy.tokens.doc.Doc'>
        """
        if not self._spacy_doc:
            lang = self._hint_language if self.language == 'un' else self.language
            if lang not in self._spacy_nlps:
                # loading models with two letter language codes doesn't work for windows due
                self._spacy_nlps[lang] = spacy.load('{}_core_{}_sm'.format(lang, 'web' if lang
                                                                           == 'en' else 'news'))
            nlp = self._spacy_nlps[lang]
            self._spacy_doc = nlp(self.clean)
        return self._spacy_doc

    @property
    def clean(self):
        """
        Cleaned text with sensible defaults.

        >>> doc = Doc('“Please clean this piece… of text</b>„')
        >>> doc.clean
        '"Please clean this piece... of text"'
        """
        return self.clean_text()

    @functools.lru_cache()
    def clean_text(self, remove_html=True, clean_dots=True, clean_quotes=True,
                   clean_whitespace=True):
        """
        Clean HTML and normalise punctuation.

        >>> doc = Doc('“Please clean this piece… of text</b>„')
        >>> doc.clean_text(False, False, False, False) == doc.raw
        True
        """
        text = self.raw
        if remove_html:
            text = BeautifulSoup(text, 'html.parser').get_text()  # remove HTML

        # Three regexes below adapted from Blendle cleaner.py
        # https://github.com/blendle/research-summarization/blob/master/enrichers/cleaner.py#L29
        if clean_dots:
            text = re.sub(r'…', '...', text)
        if clean_quotes:
            text = re.sub(r'[`‘’‛⸂⸃⸌⸍⸜⸝]', "'", text)
            text = re.sub(r'[„“]|(\'\')|(,,)', '"', text)
        if clean_whitespace:
            text = re.sub(r'\s+', ' ', text).strip()

        return text

    @property
    def ents(self):
        """
        Extract a list of the named entities in text

        >>> doc = Doc('Sentence for testing Google text')
        >>> doc.ents
        [('Google', 'ORG')]
        """
        return list({(ent.text, ent.label_) for ent in self.spacy_doc.ents})


    @property
    def nsents(self):
        """
        Extract the number of sentences from text

        >>> doc = Doc('Test sentence for testing text.')
        >>> doc.nsents
        1
        """
        return len(list(self.spacy_doc.sents))

    @property
    def nwords(self):
        """
        Extract the number of words from text

        >>> doc = Doc('Test sentence for testing text')
        >>> doc.nwords
        5
        """
        return len(self.clean.split())

    @property
    def complexity(self):
        """
        Determine the complexity of text using the Flesch
        reading ease test ranging from 0.0 - 100.0 with 0.0
        being the most difficult to read.

        >>> doc = Doc('Test sentence for testing text')
        >>> doc.complexity
        83.32000000000004
        """
        if not self._text_stats:
            self._text_stats = textacy.TextStats(self.spacy_doc)
        if self._text_stats.n_syllables == 0:
            return 100
        return self._text_stats.flesch_reading_ease
