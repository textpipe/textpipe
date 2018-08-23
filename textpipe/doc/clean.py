import functools

import re
from bs4 import BeautifulSoup


class CleanDoc:
    def __init__(self, raw, **kwargs):
        self._raw = raw or ''

    @property
    def raw(self):
        return self._raw

    @property
    def clean(self):
        """
        Cleaned text with sensible defaults.
        >>> doc = CleanDoc('“Please clean this piece… of text</b>„')
        >>> doc.clean
        '"Please clean this piece... of text"'
        """        
        return self.clean_text()

    @functools.lru_cache()
    def clean_text(self, remove_html=True, clean_dots=True, clean_quotes=True,
                   clean_whitespace=True):
        """
        Clean HTML and normalise punctuation.
        >>> doc = CleanDoc('“Please clean this piece… of text</b>„')
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