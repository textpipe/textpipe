# pylint: disable=too-many-instance-attributes
"""
Clean text, make it readable and obtain metadata from it.
"""

import re
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
        _clean_text: string containing the cleaned text
        _spacy_nlps: dictionary containing a spacy language module
        _spacy_doc: dictionary containing an instance of a spacy doc
        _text_stats: dictionary containing an instance of textacy textstats
        """

        self.raw = raw
        self.is_detected_language = language is None
        self._language = language
        self._hint_language = hint_language
        self._clean_text = None
        self._spacy_nlps = {}
        self._spacy_doc = {}
        self._text_stats = {}

    @property
    def language(self, **kwargs):
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
            _, _, best_guesses = cld2.detect(self.clean_text, hintLanguage=self._hint_language,
                                             bestEffort=True)
            self._language = best_guesses[0][1]
        return self._language

    @property
    def spacy_doc(self, **kwargs):
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
            self._spacy_doc = nlp(self.clean_text)
        return self._spacy_doc

    @property
    def clean_text(self, **kwargs):
        """
        Clean HTML and normalise punctuation.

        >>> doc = Doc('“Please clean this piece… of text</b>„')
        >>> doc.clean_text
        '"Please clean this piece... of text"'
        """
        if self._clean_text is None:
            if self.raw is not None:
                text = BeautifulSoup(self.raw, 'html.parser').get_text()  # remove HTML
                # Three regexes below adapted from Blendle cleaner.py
                # https://github.com/blendle/research-summarization/blob/master/enrichers/cleaner.py#L29
                text = re.sub('…', '...', text)
                text = re.sub('[`‘’‛⸂⸃⸌⸍⸜⸝]', "'", text)
                text = re.sub('[„“]|(\'\')|(,,)', '"', text)
                text = re.sub('\s+', ' ', text)
                self._clean_text = text.strip()
            else:
                self._clean_text = ''
        return self._clean_text

    @property
    def ents(self, **kwargs):
        """
        Extract a list of the named entities in text

        >>> doc = Doc('Sentence for testing Google text')
        >>> doc.ents
        [('Google', 'ORG')]
        """
        return list(set([(ent.text, ent.label_) for ent in self.spacy_doc.ents]))


    @property
    def nsents(self, **kwargs):
        """
        Extract the number of sentences from text

        >>> doc = Doc('Test sentence for testing text.')
        >>> doc.nsents
        1
        """
        return len(list(self.spacy_doc.sents))

    @property
    def nwords(self, **kwargs):
        """
        Extract the number of words from text

        >>> doc = Doc('Test sentence for testing text')
        >>> doc.nwords
        5
        """
        return len(self.clean_text.split())

    @property
    def complexity(self, **kwargs):
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
