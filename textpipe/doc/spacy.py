import spacy

from textpipe.doc.language import LanguageDoc


class SpacyDoc(LanguageDoc):
    def __init__(self, **kwargs):
        """
        Args:
        _clean: string containing the cleaned text
        _spacy_nlps: dictionary containing a spacy language module
        _spacy_doc: dictionary containing an instance of a spacy doc
        _text_stats: dictionary containing an instance of textacy textstats
        """
        self._spacy_nlps = {}
        self._spacy_doc = {}

    @property
    def spacy_doc(self):
        """
        Create a spacy doc and load the language module
        >>> from textpipe.doc import Doc
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
    def ents(self):
        """
        Extract a list of the named entities in text
        >>> from textpipe.doc import Doc
        >>> doc = Doc('Sentence for testing Google text')
        >>> doc.ents
        [('Google', 'ORG')]
        """
        return list({(ent.text, ent.label_) for ent in self.spacy_doc.ents})

    @property
    def nsents(self):
        """
        Extract the number of sentences from text
        >>> from textpipe.doc import Doc
        >>> doc = Doc('Test sentence for testing text.')
        >>> doc.nsents
        1
        """
        return len(list(self.spacy_doc.sents))

    @property
    def nwords(self):
        """
        Extract the number of words from text
        >>> from textpipe.doc import Doc
        >>> doc = Doc('Test sentence for testing text')
        >>> doc.nwords
        5
        """
        return len(self.clean.split())
