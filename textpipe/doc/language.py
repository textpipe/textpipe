import cld2

from textpipe.doc.clean import CleanDoc


class LanguageDoc(CleanDoc):
    """
    Detect the language of a text if no language was provided along with the text
    Args:
    language: 2-letter code for the language of the text
    hint_language: language you expect your text to be
    Properties:
    is_detected_language: a boolean indicating if the language was specified
                          beforehand or detected
    >>> from textpipe.doc import Doc
    >>> Doc('Test sentence for testing text').language
    'en'
    >>> Doc('Test sentence for testing text', language='en').language
    'en'
    >>> Doc('Test', hint_language='nl').language
    'nl'
    """

    def __init__(self, language=None, hint_language='en'):
        self.is_detected_language = language is None
        self._language = language
        self._hint_language = hint_language

    @property
    def language(self):
        if not self._language:
            self._language = self.detect_language(self._hint_language)
        return self._language

    def detect_language(self, hint_language):
        """
        >>> from textpipe.doc import Doc
        >>> doc = Doc('Test')
        >>> doc.language
        'en'
        >>> doc.detect_language('nl')
        'nl'
        """
        _, _, best_guesses = cld2.detect(self.clean, hintLanguage=hint_language,
                                         bestEffort=True)
        return best_guesses[0][1]