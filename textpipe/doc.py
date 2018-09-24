"""
Clean text, make it readable and obtain metadata from it.
"""

import functools
import re

import cld2
import spacy
import textacy
import textacy.text_utils
from bs4 import BeautifulSoup


class TextpipeMissingModelException(Exception):
    """Raised when the requested model is missing"""
    pass


class Doc:
    """
    Create a doc instance of text, obtain cleaned, readable text and
    metadata from this doc.

    Properties:
    raw: incoming, unedited text
    language: 2-letter code for the language of the text
    is_detected_language: is the language detected or specified beforehand
    is_reliable_language: is the language specified or was it reliably detected
    hint_language: language you expect your text to be
    _spacy_nlps: nested dictionary {lang: {model_id: model}} with loaded spacy language modules
    """

    def __init__(self, raw, language=None, hint_language='en', spacy_nlps=None):
        self.raw = raw
        self.hint_language = hint_language
        self._spacy_nlps = spacy_nlps or dict()
        self.is_detected_language = language is None
        self._language = language
        self._is_reliable_language = True if language else None

        self._text_stats = {}

    @property
    def language(self):
        """
        Provided or detected language of a text

        >>> from textpipe.doc import Doc
        >>> Doc('Test sentence for testing text').language
        'en'
        >>> Doc('Test sentence for testing text', language='en').language
        'en'
        >>> Doc('Test', hint_language='nl').language
        'nl'
        """
        if not self._language:
            self._is_reliable_language, self._language = self.detect_language(self.hint_language)
        return self._language

    @property
    def is_reliable_language(self):
        """
        True if the language was specified or if was it reliably detected

        >>> Doc('...').is_reliable_language
        False
        >>> Doc('Test', hint_language='nl').is_reliable_language
        True
        """
        if self._is_reliable_language is None:
            self._is_reliable_language, self._language = self.detect_language(self.hint_language)
        return self._is_reliable_language

    @functools.lru_cache()
    def detect_language(self, hint_language=None):
        """
        Detected the language of a text if no language was provided along with the text

        Args:
        hint_language: language you expect your text to be

        Returns:
        is_reliable: is the top language is much better than 2nd best language?
        language: 2-letter code for the language of the text

        >>> from textpipe.doc import Doc
        >>> doc = Doc('Test')
        >>> doc.detect_language()
        (True, 'en')
        >>> doc.detect_language('nl')
        (True, 'nl')
        >>> Doc('...').detect_language()
        (False, 'un')
        """
        is_reliable, _, best_guesses = cld2.detect(self.clean,
                                                   hintLanguage=hint_language,
                                                   bestEffort=True)

        if len(best_guesses) == 0 or len(best_guesses[0]) != 4 or best_guesses[0][1] == 'un':
            return False, 'un'

        return is_reliable, best_guesses[0][1]

    @property
    def _spacy_doc(self):
        """
        Loads the default spacy doc or creates one if necessary

        >>> doc = Doc('Test sentence for testing text')
        >>> type(doc._spacy_doc)
        <class 'spacy.tokens.doc.Doc'>
        """
        lang = self.language if self.is_reliable_language else self.hint_language

        return self._load_spacy_doc(lang)

    @functools.lru_cache()
    def _load_spacy_doc(self, lang, model_name=None):
        """
        Loads a spacy doc or creates one if necessary
        """
        # Load default spacy model if necessary, if not loaded already
        if lang not in self._spacy_nlps or (model_name is None and
                                            model_name not in self._spacy_nlps[lang]):
            self._set_default_nlp(lang)
        if model_name not in self._spacy_nlps[lang] and model_name is not None:
            raise TextpipeMissingModelException(f'Custom model {model_name} '
                                                f'is missing.')
        nlp = self._spacy_nlps[lang][model_name]
        doc = nlp(self.clean_text())
        return doc

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
        A list of the named entities with sensible defaults.

        >>> doc = Doc('Sentence for testing Google text')
        >>> doc.ents
        [('Google', 'ORG')]
        """
        return self.find_ents()

    @functools.lru_cache()
    def find_ents(self, model_name=None):
        """
        Extract a list of the named entities in text, with the possibility of using a custom model.
        >>> doc = Doc('Sentence for testing Google text')
        >>> doc.find_ents()
        [('Google', 'ORG')]
        """
        lang = self.language if self.is_reliable_language else self.hint_language
        return list({(ent.text, ent.label_) for ent in self._load_spacy_doc(lang, model_name).ents})

    def match(self, matcher):
        """
        Run a SpaCy matcher over the cleaned content

        >>> import spacy.matcher
        >>> matcher = spacy.matcher.Matcher(spacy.lang.en.English().vocab)
        >>> matcher.add('HASHTAG', None, [{'ORTH': '#'}, {'IS_ASCII': True}])
        >>> Doc('Test with #hashtag').match(matcher)
        [('#hashtag', 'HASHTAG')]
        """
        return [(self._spacy_doc[start:end].text, matcher.vocab.strings[match_id])
                for match_id, start, end in matcher(self._spacy_doc)]

    @property
    def nsents(self):
        """
        Extract the number of sentences from text

        >>> doc = Doc('Test sentence for testing text. And another sentence for testing!')
        >>> doc.nsents
        2
        """
        return len(list(self._spacy_doc.sents))

    @property
    def sents(self):
        """
        Extract the text and character offset (begin) of sentences from text

        >>> doc = Doc('Test sentence for testing text. And another one with, some, punctuation! And stuff.')
        >>> doc.sents
        [('Test sentence for testing text.', 0), ('And another one with, some, punctuation!', 32), ('And stuff.', 73)]
        """

        return [(span.text, span.start_char) for span in self._spacy_doc.sents]

    @property
    def nwords(self):
        """
        Extract the number of words from text

        >>> doc = Doc('Test sentence for testing text')
        >>> doc.nwords
        5
        """
        return len(self.words)

    @property
    def words(self):
        """
        Extract the text and character offset (begin) of words from text

        >>> doc = Doc('Test sentence for testing text.')
        >>> doc.words
        [('Test', 0), ('sentence', 5), ('for', 14), ('testing', 18), ('text', 26), ('.', 30)]
        """

        return [(token.text, token.idx) for token in self._spacy_doc]

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
            self._text_stats = textacy.TextStats(self._spacy_doc)
        if self._text_stats.n_syllables == 0:
            return 100
        return self._text_stats.flesch_reading_ease

    def _set_default_nlp(self, lang):
        """
        Loads the spacy default language module for the Doc's language into the _spacy_nlps object
        """
        if lang not in self._spacy_nlps:
            self._spacy_nlps[lang] = {}
        model = spacy.load('{}_core_{}_sm'.format(lang, 'web' if lang == 'en' else 'news'))
        self._spacy_nlps[lang][None] = model

    @property
    def sentiment(self):
        """
        Returns polarity score (-1 to 1) and a subjectivity score (0 to 1)

        Currently only English, Dutch, French and Italian supported

        >>> doc = Doc('Dit is een leuke zin.')
        >>> doc.sentiment
        (0.6, 0.9666666666666667)
        """

        if self.language == 'en':
            from pattern.text.en import sentiment as sentiment_en
            return sentiment_en(self.clean)
        elif self.language == 'nl':
            from pattern.text.nl import sentiment as sentiment_nl
            return sentiment_nl(self.clean)
        elif self.language == 'fr':
            from pattern.text.fr import sentiment as sentiment_fr
            return sentiment_fr(self.clean)
        elif self.language == 'it':
            from pattern.text.it import sentiment as sentiment_it
            return sentiment_it(self.clean)

        raise TextpipeMissingModelException(f'No sentiment model for {self.language}')
