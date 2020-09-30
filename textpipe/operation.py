# pylint: disable=too-few-public-methods
"""
Operation classes must be defined in this module.

In a future version we might consider adding support for fully qualified paths
when creating a Pipeline, e.g.:
Pipeline['CleanText', 'my.org.package.OperationClass'])

so that users do not have to put their Operation classes inside of this module.
"""
from textpipe.doc import TextpipeMissingModelException


class Operation:
    """
    Base class for pipeline operations.
    """
    model_mapping = {}

    def __call__(self, doc, **kwargs):
        raise NotImplementedError()

    def get_model(self, doc):
        """
        Gets model for the language of a given document.
        """
        lang = doc.language if doc.is_reliable_language else doc.hint_language
        try:
            model = self.model_mapping[lang]
        except KeyError:
            # pylint: disable=raise-missing-from
            raise TextpipeMissingModelException(f'No model for language "{lang}".')
        return model


class Language(Operation):
    """
    Extract the language from a text

    >>> from textpipe.doc import Doc
    >>> doc = Doc('Test sentence for testing text')
    >>> Language()(doc)
    'en'
    """

    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def __call__(self, doc, **kwargs):
        return doc.language


class CleanText(Operation):
    """
    Clean HTML and normalise punctuation.

    >>> from textpipe.doc import Doc
    >>> doc = Doc('“Please clean this piece… of text</b>„')
    >>> CleanText()(doc)
    '"Please clean this piece... of text"'
    """

    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def __call__(self, doc, **kwargs):
        return doc.clean


class Raw(Operation):
    """
    Extract the number of words from text

    >>> from textpipe.doc import Doc
    >>> doc = Doc('Test sentence for testing text')
    >>> Raw()(doc)
    'Test sentence for testing text'
    """

    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def __call__(self, doc, **kwargs):
        return doc.raw


class NWords(Operation):
    """
    Extract the number of words from text

    >>> from textpipe.doc import Doc
    >>> doc = Doc('Test sentence for testing text')
    >>> NWords()(doc)
    5
    """

    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def __call__(self, doc, **kwargs):
        return doc.nwords


class Words(Operation):
    """
    Extract words from text

    >>> from textpipe.doc import Doc
    >>> doc = Doc('Test sentence for testing text')
    >>> Words()(doc)
    [('Test', 0), ('sentence', 5), ('for', 14), ('testing', 18), ('text', 26)]
    """

    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def __call__(self, doc, **kwargs):
        return doc.words


class WordCounts(Operation):
    """
    Extract words with their counts

    >>> from pprint import pprint
    >>> from textpipe.doc import Doc
    >>> doc = Doc('Test sentence for testing vectorisation of a sentence.')
    >>> pprint(WordCounts()(doc), indent=2)
    { '.': 1,
      'Test': 1,
      'a': 1,
      'for': 1,
      'of': 1,
      'sentence': 2,
      'testing': 1,
      'vectorisation': 1}
    """

    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def __call__(self, doc, **kwargs):
        return doc.word_counts


class Complexity(Operation):
    """
    Determine the complexity of text using the Flesch
    reading ease test ranging from 0.0 - 100.0 with 0.0
    being the most difficult to read.

    >>> from textpipe.doc import Doc
    >>> doc = Doc('Test sentence for testing text')
    >>> Complexity()(doc)
    83.32000000000004
    """

    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def __call__(self, doc, **kwargs):
        return doc.complexity


class Sentences(Operation):
    """
    Extract sentences from text

    >>> from pprint import pprint
    >>> from textpipe.doc import Doc
    >>> doc = Doc('Test sentence for testing text. '
    ...           'And another one with, some, punctuation! And stuff.')
    >>> pprint(Sentences()(doc))
    [('Test sentence for testing text.', 0),
     ('And another one with, some, punctuation!', 32),
     ('And stuff.', 73)]
    """

    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def __call__(self, doc, **kwargs):
        return doc.sents


class NSentences(Operation):
    """
    Extract the number of sentences from text

    >>> from textpipe.doc import Doc
    >>> doc = Doc('Test sentence for testing text')
    >>> NSentences()(doc)
    1
    """

    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def __call__(self, doc, **kwargs):
        return doc.nsents


class Entities(Operation):
    """
    Extract a list of the named entities in text

    >>> from textpipe.doc import Doc
    >>> doc = Doc('Sentence for testing Google text')
    >>> Entities()(doc)
    [('Google', 'ORG')]
    """

    def __init__(self, model_mapping=None, ent_attributes=('text', 'label_'), **kwargs):
        self.kwargs = kwargs
        self.model_mapping = model_mapping
        self.ent_attributes = ent_attributes

    def __call__(self, doc, **kwargs):
        if not self.model_mapping:
            if not self.ent_attributes:
                return doc.ents
            return doc.find_ents(ent_attributes=self.ent_attributes)

        return doc.find_ents(model_name=self.get_model(doc), ent_attributes=self.ent_attributes)


class Sentiment(Operation):
    """
    Returns polarity score (-1 to 1) and a subjectivity score (0 to 1)

    Currently only English, Dutch, French and Italian supported

    >>> from textpipe.doc import Doc
    >>> doc = Doc('Een hele leuke test zin.')
    >>> Sentiment()(doc)
    (0.9599999999999999, 1.0)
    """

    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def __call__(self, doc, **kwargs):
        return doc.sentiment


class Keyterms(Operation):
    """
    Returns a list of up to 10 key terms extracted from the document. This
    works on any language the Doc can tokenize.

    >>> from pprint import pprint
    >>> from textpipe.doc import Doc
    >>> doc = Doc('Amsterdam is the awesome capital of the Netherlands.')
    >>> pprint(Keyterms()(doc))
    [('awesome capital', 0.2384595585785324),
     ('Netherlands', 0.1312376837867799),
     ('Amsterdam', 0.07452637881734389)]
    >>> pprint(Keyterms(n_terms=2)(doc))
    [('awesome capital', 0.2384595585785324), ('Netherlands', 0.1312376837867799)]
    >>> pprint(Keyterms(ranker='sgrank')(doc))
    [('awesome capital', 0.5638711013322963),
     ('Netherlands', 0.22636566128805719),
     ('Amsterdam', 0.20976323737964653)]
    """

    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def __call__(self, doc, **kwargs):
        return doc.extract_keyterms(**self.kwargs)


class MinHash(Operation):
    """
    Returns a list with integers, which is the minhash of the document.
    A minhash is a cheap way to compute a hash for finding similarity of documents.
    Source: https://ekzhu.github.io/datasketch/minhash.html

    >>> from textpipe.doc import Doc
    >>> doc = Doc('Sentence for computing the minhash')
    >>> doc.minhash[:5]
    [407326892, 814360600, 1099082245, 1176349439, 1735256]
    """

    def __init__(self, num_perm=128, **kwargs):
        self.kwargs = kwargs
        self.num_perm = num_perm

    def __call__(self, doc, **kwargs):
        return doc.find_minhash(num_perm=self.num_perm)


class WordVectors(Operation):
    """
    Extract the vectors of the words in a document.

    Returns a dict that maps each word to a dict with the following keys:
        'has_vector': True if the word has a vector
        'vector_norm': The vector norm of the word
        'is_oov': True if the word is out of vocabulary
        'vector': The vector corresponding to the word

    >>> from textpipe.doc import Doc
    >>> doc = Doc('Sentence for vectorization')
    >>> WordVectors()(doc)['Sentence']['has_vector']
    True
    """

    def __init__(self, model_mapping=None, **kwargs):
        self.model_mapping = model_mapping
        self.kwargs = kwargs

    def __call__(self, doc, **kwargs):
        if not self.model_mapping:
            return doc.word_vectors

        return doc.generate_word_vectors(self.get_model(doc))


class DocumentVector(Operation):
    """
    Extract the vector of the document.

    >>> from textpipe.doc import Doc
    >>> doc = Doc('Sentence for vectorization')
    >>> len(DocumentVector()(doc))
    96
    """

    def __init__(self, model_mapping=None, **kwargs):
        self.model_mapping = model_mapping
        self.kwargs = kwargs

    def __call__(self, doc, **kwargs):
        if not self.model_mapping:
            return doc.aggregate_word_vectors(**self.kwargs)

        return doc.aggregate_word_vectors(self.get_model(doc), **self.kwargs)


class GensimDocumentEmbedding(Operation):
    """
    Extract a document embedding vector derived from Gensim word embeddings
    """
    def __init__(self, model_mapping=None, lowercase=True,
                 max_lru_cache_size=1024, idf_weighting='naive', **kwargs):
        self.model_mapping = model_mapping
        self.lowercase = lowercase
        self.max_lru_cache_size = max_lru_cache_size
        self.idf_weighting = idf_weighting
        self.kwargs = kwargs

    def __call__(self, doc, **kwargs):
        return doc.generate_gensim_document_embedding(self.get_model(doc),
                                                      self.lowercase,
                                                      self.max_lru_cache_size,
                                                      self.idf_weighting,
                                                      **self.kwargs)


class GensimTextRank(Operation):
    """
    Extract a sentence-based summary for a document using TextRank implemented in Gensim

    >>> from pprint import pprint
    >>> from textpipe.doc import Doc
    >>> text = '''Rice Pudding - Poem by Alan Alexander Milne
    ... What is the matter with Mary Jane?
    ... She's crying with all her might and main,
    ... And she won't eat her dinner - rice pudding again -
    ... What is the matter with Mary Jane?
    ... What is the matter with Mary Jane?
    ... I've promised her dolls and a daisy-chain,
    ... And a book about animals - all in vain -
    ... What is the matter with Mary Jane?
    ... What is the matter with Mary Jane?
    ... She's perfectly well, and she hasn't a pain;
    ... But, look at her, now she's beginning again! -
    ... What is the matter with Mary Jane?
    ... What is the matter with Mary Jane?
    ... I've promised her sweets and a ride in the train,
    ... And I've begged her to stop for a bit and explain -
    ... What is the matter with Mary Jane?
    ... What is the matter with Mary Jane?
    ... She's perfectly well and she hasn't a pain,
    ... And it's lovely rice pudding for dinner again!
    ... What is the matter with Mary Jane?'''
    >>> doc = Doc(text)
    >>> pprint(GensimTextRank(ratio=0.2)(doc))
    ["She's crying with all her might and main, And she won't eat her dinner - "
     'rice pudding again - What is the matter with Mary Jane?',
     "She's perfectly well and she hasn't a pain, And it's lovely rice pudding for "
     'dinner again!']
    >>> pprint(GensimTextRank(word_count=20)(doc))
    ["She's crying with all her might and main, And she won't eat her dinner - "
     'rice pudding again - What is the matter with Mary Jane?']
    >>> GensimTextRank(word_count=10)(doc)
    []
    """

    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def __call__(self, doc, **kwargs):
        return doc.generate_textrank_summary(**self.kwargs)


class LeadSentences(Operation):
    """
    Extract the lead nsents sentences from a document

    >>> from textpipe.doc import Doc
    >>> text = '''Rice Pudding - Poem by Alan Alexander Milne.
    ... What is the matter with Mary Jane?
    ... She's crying with all her might and main,
    ... And she won't eat her dinner - rice pudding again.
    ... What is the matter with Mary Jane? '''
    >>> doc = Doc(text)
    >>> LeadSentences(nsents=2)(doc)
    ['Rice Pudding - Poem by Alan Alexander Milne.', 'What is the matter with Mary Jane?']
    """

    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def __call__(self, doc, **kwargs):
        return doc.extract_lead(**self.kwargs)


class Categories(Operation):
    """
    Extract the category probabilities of the document.

    >>> from textpipe.doc import Doc
    >>> doc = Doc('Sentence for categorization')
    >>> Categories()(doc)
    {}
    """

    def __init__(self, model_mapping=None, **kwargs):
        self.model_mapping = model_mapping
        self.kwargs = kwargs

    def __call__(self, doc, **kwargs):
        if not self.model_mapping:
            return doc.cats

        return doc.get_cats(self.get_model(doc), **self.kwargs)
