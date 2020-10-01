"""
Clean text, make it readable and obtain metadata from it.
"""

import functools
import re
import unicodedata
from collections import Counter
from urllib.parse import urlparse

import cld2
import numpy
import spacy
import spacy.matcher
import textacy
import textacy.ke
import textacy.text_utils
from bs4 import BeautifulSoup
from datasketch import MinHash
from gensim.models.keyedvectors import KeyedVectors
from gensim.summarization.summarizer import summarize

from textpipe.data.emoji import EMOJI_TO_UNICODE_NAME, EMOJI_TO_SENTIMENT
from textpipe.wrappers import RedisKeyedVectors
from textpipe.util import getattr_


class TextpipeMissingModelException(Exception):
    """Raised when the requested model is missing"""


class RedisIDFWeightingMismatchException(Exception):
    """Raised when an idf weighting scheme is specified that does not match the specified weighting
    scheme in RedisKeyedVector"""


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

    # pylint: disable=too-many-instance-attributes
    # pylint: disable=too-many-arguments
    # pylint: disable=too-many-public-methods

    def __init__(self,
                 raw,
                 language=None,
                 hint_language='en',
                 spacy_nlps=None,
                 gensim_vectors=None):
        self.raw = raw
        self._language = language
        self.hint_language = hint_language
        self._spacy_nlps = spacy_nlps if spacy_nlps is not None else dict()
        self._gensim_vectors = gensim_vectors if gensim_vectors is not None else dict()
        self.is_detected_language = language is None
        self._is_reliable_language = True if language else None
        self._text_stats = {}
        self.nr_train_tokens = 0

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

        >>> from textpipe.doc import Doc
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

        none_utf_chars_removed = ''.join([l for l in self.clean
                                          if unicodedata.category(l)[0] not in {'M', 'C'}])
        is_reliable, _, best_guesses = cld2.detect(none_utf_chars_removed,
                                                   hintLanguage=hint_language,
                                                   bestEffort=True)

        if not best_guesses or len(best_guesses[0]) != 4 or best_guesses[0][1] == 'un':
            return False, 'un'

        return is_reliable, best_guesses[0][1]

    @property
    def _spacy_doc(self):
        """
        Loads the default spacy doc or creates one if necessary

        >>> from textpipe.doc import Doc
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
            if lang not in self._spacy_nlps:
                self._spacy_nlps[lang] = {}
            self._spacy_nlps[lang][None] = self._get_default_nlp(lang)
        if model_name not in self._spacy_nlps[lang] and model_name is not None:
            raise TextpipeMissingModelException(f'Custom model {model_name} '
                                                f'is missing.')
        nlp = self._spacy_nlps[lang][model_name]
        doc = nlp(self.clean_text())
        return doc

    @staticmethod
    @functools.lru_cache()
    def _get_default_nlp(lang):
        """
        Loads the spacy default language module for the Doc's language
        """
        try:
            return spacy.load('{}_core_{}_sm'.format(lang, 'web' if lang == 'en' else 'news'))
        except IOError:
            # pylint: disable=raise-missing-from
            raise TextpipeMissingModelException(f'Default model for language "{lang}" '
                                                f'is not available.')

    @property
    def clean(self):
        """
        Cleaned text with sensible defaults.

        >>> from textpipe.doc import Doc
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

        >>> from textpipe.doc import Doc
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

        >>> from textpipe.doc import Doc
        >>> doc = Doc('Sentence for testing Google text')
        >>> doc.ents
        [('Google', 'ORG')]
        """
        return self.find_ents()

    @functools.lru_cache()
    def find_ents(self, model_name=None, ent_attributes=('text', 'label_')):
        """
        Extract a list of the named entities in text, with the possibility of using a custom model.

        >>> from textpipe.doc import Doc
        >>> doc = Doc('Sentence for testing Google text')
        >>> doc.find_ents()
        [('Google', 'ORG')]
        """
        lang = self.language if self.is_reliable_language else self.hint_language
        return list({tuple(getattr_(ent, attr) for attr in ent_attributes)
                     for ent in self._load_spacy_doc(lang, model_name).ents})

    def match(self, matcher):
        """
        Run a SpaCy matcher over the cleaned content

        >>> import spacy.matcher
        >>> from textpipe.doc import Doc
        >>> matcher = spacy.matcher.Matcher(spacy.lang.en.English().vocab)
        >>> matcher.add('HASHTAG', None, [{'ORTH': '#'}, {'IS_ASCII': True}])
        >>> Doc('Test with #hashtag').match(matcher)
        [('#hashtag', 'HASHTAG')]
        """
        return [(self._spacy_doc[start:end].text, matcher.vocab.strings[match_id])
                for match_id, start, end in matcher(self._spacy_doc)]

    @property
    def emojis(self):
        """
        Emojis detected using SpaCy matcher over the cleaned content, with unicode name and
        sentiment score.

        >>> from pprint import pprint
        >>> from textpipe.doc import Doc
        >>> pprint(Doc('Test with emoji 😀 😋 ').emojis)
        [('😀', 'GRINNING FACE', 0.571753986332574),
         ('😋', 'FACE SAVOURING DELICIOUS FOOD', 0.6335149863760218)]
        """
        detected_emojis = []
        matcher = spacy.matcher.Matcher(self._spacy_doc.vocab)
        for emoji, unicode_name in EMOJI_TO_UNICODE_NAME.items():
            matcher.add(unicode_name, None, [{'ORTH': emoji}])

        for emoji, unicode_name in self.match(matcher):
            detected_emojis.append((emoji, unicode_name, EMOJI_TO_SENTIMENT[emoji]))

        return detected_emojis

    @property
    def nsents(self):
        """
        Extract the number of sentences from text

        >>> from textpipe.doc import Doc
        >>> doc = Doc('Test sentence for testing text. And another sentence for testing!')
        >>> doc.nsents
        2
        """
        return len(list(self._spacy_doc.sents))

    @property
    def sents(self):
        """
        Extract the text and character offset (begin) of sentences from text

        >>> from pprint import pprint
        >>> from textpipe.doc import Doc
        >>> doc = Doc('Test sentence for testing text. '
        ...           'And another one with, some, punctuation! And stuff.')
        >>> pprint(doc.sents)
        [('Test sentence for testing text.', 0),
         ('And another one with, some, punctuation!', 32),
         ('And stuff.', 73)]
        """

        return [(span.text, span.start_char) for span in self._spacy_doc.sents]

    @property
    def nwords(self):
        """
        Extract the number of words from text

        >>> from textpipe.doc import Doc
        >>> doc = Doc('Test sentence for testing text')
        >>> doc.nwords
        5
        """
        return len(self.words)

    @property
    def words(self):
        """
        Extract the text and character offset (begin) of words from text

        >>> from textpipe.doc import Doc
        >>> doc = Doc('Test sentence for testing text.')
        >>> doc.words
        [('Test', 0), ('sentence', 5), ('for', 14), ('testing', 18), ('text', 26), ('.', 30)]
        """

        return [(token.text, token.idx) for token in self._spacy_doc]

    @property
    def word_counts(self):
        """
        Extract words with their counts

        >>> from pprint import pprint
        >>> from textpipe.doc import Doc
        >>> pprint(Doc('Test sentence for testing vectorisation of a sentence.').word_counts)
        {'.': 1,
         'Test': 1,
         'a': 1,
         'for': 1,
         'of': 1,
         'sentence': 2,
         'testing': 1,
         'vectorisation': 1}
        """

        return dict(Counter(word for word, _ in self.words))

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
            self._text_stats = textacy.TextStats(self._spacy_doc)
        if self._text_stats.n_syllables == 0:
            return 100
        return self._text_stats.flesch_reading_ease

    @property
    def sentiment(self):
        """
        Returns polarity score (-1 to 1) and a subjectivity score (0 to 1)

        Currently only English, Dutch, French and Italian supported

        >>> from textpipe.doc import Doc
        >>> doc = Doc('Dit is een leuke zin.')
        >>> doc.sentiment
        (0.6, 0.9666666666666667)
        """

        if self.language == 'en':
            from pattern.text.en import sentiment as sentiment_en  # pylint: disable=import-outside-toplevel
            return sentiment_en(self.clean)

        if self.language == 'nl':
            from pattern.text.nl import sentiment as sentiment_nl  # pylint: disable=import-outside-toplevel
            return sentiment_nl(self.clean)

        if self.language == 'fr':
            from pattern.text.fr import sentiment as sentiment_fr  # pylint: disable=import-outside-toplevel
            return sentiment_fr(self.clean)

        if self.language == 'it':
            from pattern.text.it import sentiment as sentiment_it  # pylint: disable=import-outside-toplevel
            return sentiment_it(self.clean)

        raise TextpipeMissingModelException(f'No sentiment model for {self.language}')

    @functools.lru_cache()
    def extract_keyterms(self, ranker='textrank', n_terms=10, **kwargs):
        """
        Extract and rank key terms in the document by proxying to
        `textacy.keyterms`. Returns a list of (term, score) tuples. Depending
        on the ranking algorithm used, terms can consist of multiple words.

        Available rankers are TextRank (textrank), SingleRank (singlerank) and
        SGRank ('sgrank').

        >>> from pprint import pprint
        >>> from textpipe.doc import Doc
        >>> doc = Doc('Amsterdam is the awesome capital of the Netherlands.')
        >>> pprint(doc.extract_keyterms(n_terms=3))
        [('awesome capital', 0.2384595585785324),
         ('Netherlands', 0.1312376837867799),
         ('Amsterdam', 0.07452637881734389)]
        >>> pprint(doc.extract_keyterms(ranker='sgrank'))
        [('awesome capital', 0.5638711013322963),
         ('Netherlands', 0.22636566128805719),
         ('Amsterdam', 0.20976323737964653)]
        >>> pprint(doc.extract_keyterms(ranker='sgrank', ngrams=(1, )))
        [('Netherlands', 0.40349153868348353),
         ('capital', 0.29176091721189235),
         ('awesome', 0.18150539145949696),
         ('Amsterdam', 0.12324215264512725)]
        """
        if self.nwords < 1:
            return []
        rankers = ['textrank', 'sgrank', 'scake', 'yake']
        if ranker not in rankers:
            raise ValueError(f'ranker "{ranker}" not available; use one '
                             f'of {rankers}')
        ranking_fn = getattr(textacy.ke, ranker)
        return ranking_fn(self._spacy_doc, topn=n_terms, **kwargs)

    @property
    def keyterms(self):
        """
        Return textranked keyterms for the document.

        >>> from pprint import pprint
        >>> from textpipe.doc import Doc
        >>> doc = Doc('Amsterdam is the awesome capital of the Netherlands.')
        >>> pprint(doc.extract_keyterms(n_terms=3))
        [('awesome capital', 0.2384595585785324),
         ('Netherlands', 0.1312376837867799),
         ('Amsterdam', 0.07452637881734389)]
        """
        return self.extract_keyterms()

    @property
    def minhash(self):
        """
        A cheap way to compute a hash for finding similarity of docs
        Source: https://ekzhu.github.io/datasketch/minhash.html

        >>> from textpipe.doc import Doc
        >>> doc = Doc('Sentence for computing the minhash')
        >>> doc.minhash[:5]
        [407326892, 814360600, 1099082245, 1176349439, 1735256]
        """
        return self.find_minhash()

    @functools.lru_cache()
    def find_minhash(self, num_perm=128):
        """
        Compute minhash, cached.
        """
        words = self.words
        doc_hash = MinHash(num_perm=num_perm)
        for word, _ in words:
            doc_hash.update(word.encode('utf8'))
        return list(doc_hash.digest())

    def similarity(self, other_doc, metric='jaccard', hash_method='minhash'):
        """
        Computes similarity for two documents.
        Only minhash Jaccard similarity is implemented.

        >>> from textpipe.doc import Doc
        >>> doc1 = Doc('Sentence for computing the minhash')
        >>> doc2 = Doc('Sentence for computing the similarity')
        >>> doc1.similarity(doc2)
        0.7265625
        """
        if hash_method == 'minhash' and metric == 'jaccard':
            hash1 = MinHash(hashvalues=self.minhash)
            hash2 = MinHash(hashvalues=other_doc.minhash)
            return hash1.jaccard(hash2)

        raise NotImplementedError(f'Metric/hash method combination {metric}'
                                  f'/{hash_method} is not implemented as similarity metric')

    @property
    def word_vectors(self):
        """
        Returns word embeddings for the words in the document.
        """
        return self.generate_word_vectors()

    @functools.lru_cache()
    def generate_word_vectors(self, model_name=None):
        """
        Returns word embeddings for the words in the document.
        The default spacy models don't have "true" word vectors
        but only context-sensitive tensors that are within the document.

        Returns:
        A dictionary mapping words from the document to a dict with the
        corresponding values of the following variables:

        has vector: Does the token have a vector representation?
        vector norm: The L2 norm of the token's vector (the square root of the
                    sum of the values squared)
        OOV: Out-of-vocabulary (This variable always gets the value True since
                                there are no vectors included in the model)
        vector: The vector representation of the word

        >>> from textpipe.doc import Doc
        >>> doc = Doc('Test sentence')
        >>> doc.word_vectors['Test']['is_oov']
        True
        >>> len(doc.word_vectors['Test']['vector'])
        96
        >>> doc.word_vectors['Test']['vector_norm'] == doc.word_vectors['sentence']['vector_norm']
        False
        """
        lang = self.language if self.is_reliable_language else self.hint_language
        return {token.text: {'has_vector': token.has_vector,
                             'vector_norm': token.vector_norm,
                             'is_oov': token.is_oov,
                             'vector': token.vector.tolist()}
                for token in self._load_spacy_doc(lang, model_name)}

    @property
    def doc_vector(self):
        """
        Returns document embeddings based on the words in the document.

        >>> import numpy
        >>> from textpipe.doc import Doc
        >>> numpy.array_equiv(Doc('a b').doc_vector, Doc('a b').doc_vector)
        True
        >>> numpy.array_equiv(Doc('a b').doc_vector, Doc('a a b').doc_vector)
        False
        """
        return self.aggregate_word_vectors()

    @functools.lru_cache()
    def aggregate_word_vectors(self,
                               model_name=None,
                               aggregation='mean',
                               normalize=False,
                               exclude_oov=False):
        """
        Returns document embeddings based on the words in the document.

        >>> import numpy
        >>> from textpipe.doc import Doc
        >>> doc1 = Doc('a b')
        >>> doc2 = Doc('a a b')
        >>> numpy.array_equiv(doc1.aggregate_word_vectors(), doc1.aggregate_word_vectors())
        True
        >>> numpy.array_equiv(doc1.aggregate_word_vectors(), doc2.aggregate_word_vectors())
        False
        >>> numpy.array_equiv(doc1.aggregate_word_vectors(aggregation='mean'),
        ...                   doc2.aggregate_word_vectors(aggregation='sum'))
        False
        >>> numpy.array_equiv(doc1.aggregate_word_vectors(aggregation='mean'),
        ...                   doc2.aggregate_word_vectors(aggregation='var'))
        False
        >>> numpy.array_equiv(doc1.aggregate_word_vectors(aggregation='sum'),
        ...                   doc2.aggregate_word_vectors(aggregation='var'))
        False
        >>> doc = Doc('sentence with an out of vector word lsseofn')
        >>> len(doc.aggregate_word_vectors())
        96
        >>> numpy.array_equiv(doc.aggregate_word_vectors(exclude_oov=False),
        ...                   doc.aggregate_word_vectors(exclude_oov=True))
        False
        """
        lang = self.language if self.is_reliable_language else self.hint_language
        tokens = [token for token in self._load_spacy_doc(lang, model_name)
                  if not exclude_oov or not token.is_oov]
        vectors = [token.vector / token.vector_norm if normalize else token.vector
                   for token in tokens]

        if aggregation == 'mean':
            return numpy.mean(vectors, axis=0).tolist()

        if aggregation == 'sum':
            return numpy.sum(vectors, axis=0).tolist()

        if aggregation == 'var':
            return numpy.var(vectors, axis=0).tolist()

        raise NotImplementedError(f'Aggregation method {aggregation} is not implemented.')

    def _load_gensim_word2vec_model(self,
                                    model_uri=None,
                                    max_lru_cache_size=1024):
        """
        Loads pre-trained Gensim word2vec keyed vector model from either local or Redis

        >>> from textpipe.doc import Doc
        >>> model = Doc('')._load_gensim_word2vec_model('tests/models/gensim_test_nl.kv')
        >>> type(model)
        <class 'gensim.models.keyedvectors.Word2VecKeyedVectors'>
        """
        lang = self.language if self.is_reliable_language else self.hint_language
        if not self._gensim_vectors or lang not in self._gensim_vectors:
            if urlparse(model_uri).scheme == 'redis':
                vectors = RedisKeyedVectors(model_uri,
                                            lang,
                                            max_lru_cache_size)
                if not vectors.exists:
                    raise TextpipeMissingModelException(f'Redis does not contain a model '
                                                        f'for language {lang}. The model '
                                                        f'needs to be loaded before use '
                                                        f'(see load_keyed_vectors_into_redis).')
            elif model_uri:
                try:
                    vectors = KeyedVectors.load(model_uri, mmap='r')
                    self.nr_train_tokens = sum(token_vocab.count for token_vocab in
                                               vectors.vocab.values())
                except FileNotFoundError:
                    # pylint: disable=raise-missing-from
                    raise TextpipeMissingModelException(
                        f'Gensim keyed vector file {model_uri} is not available.')
            else:
                raise TextpipeMissingModelException(
                    'Either specify model filename or redis URI')
            self._gensim_vectors[lang] = vectors
        return self._gensim_vectors[lang]

    @functools.lru_cache()
    def generate_gensim_document_embedding(self,
                                           model_uri=None,
                                           lowercase=True,
                                           max_lru_cache_size=1024,
                                           idf_weighting='naive'):
        """
        Returns document embeddings generated with Gensim word2vec model.
        idf_weighting scheme can be 'naive' or 'log'

        >>> import numpy
        >>> from textpipe.doc import Doc
        >>> doc1 = Doc('textmining is verwant aan tekstanalyse')
        >>> doc2 = Doc('textmining is verwant aan textmining')
        >>> doc3 = Doc('tekstanalyse is verwant aan textmining')
        >>> test_model_file = 'tests/models/gensim_test_nl.kv'
        >>> numpy.allclose(doc1.generate_gensim_document_embedding(model_uri=test_model_file), \
                           doc2.generate_gensim_document_embedding(model_uri=test_model_file))
        False
        >>> numpy.allclose(doc1.generate_gensim_document_embedding(model_uri=test_model_file), \
                           doc3.generate_gensim_document_embedding(model_uri=test_model_file))
        True
        """
        if not model_uri:
            raise TextpipeMissingModelException('No Gensim keyed vector location specified.')

        model = self._load_gensim_word2vec_model(model_uri,
                                                 max_lru_cache_size)

        if lowercase:
            prepared_word_counts = [(word.lower(), count)
                                    for word, count in self.word_counts.items()
                                    if word.lower() in model]
        else:
            prepared_word_counts = [(word, count) for word, count in self.word_counts.items()
                                    if word in model]

        if not prepared_word_counts:
            return []

        if isinstance(model, RedisKeyedVectors):
            # For redis, the word vectors are already divided by the idf when a word2vec model
            # was loaded (see RedisKeyedVectors.load_keyed_vectors_into_redis)
            if model.idf_weighting != idf_weighting:
                raise RedisIDFWeightingMismatchException(f'The specified document embedding idf '
                                                         f'weighting "{idf_weighting}" does not '
                                                         f'match weighting in RedisKeyedVector "'
                                                         f'{model.idf_weighting}"')
            vectors = [model[word] * count
                       for word, count in prepared_word_counts]
        else:
            vectors = []
            for word, count in prepared_word_counts:
                if idf_weighting == 'naive':
                    idf = model.vocab[word].count
                elif idf_weighting == 'log':
                    idf = (numpy.log(self.nr_train_tokens / (model.vocab[word].count + 1)) + 1)
                else:
                    raise ValueError(f'idf_weighting "{idf_weighting}" not available; use '
                                     f'"naive" or "log"')

                vectors.append(model[word] * (count / idf))
        return list(sum(vectors))

    @functools.lru_cache()
    def generate_textrank_summary(self, ratio=0.2, word_count=None):
        """
        returns a textrank summary of the document (extractive summary) generated with gensim
        returns an empty summary if the text could not be compressed
        if both ratio and word_count are provided, ratio is ignored
        """
        try:
            return summarize(self._spacy_doc.text, ratio=ratio, word_count=word_count, split=True)
        except ValueError:
            return []

    @property
    def summary(self):
        """
        returns a textrank summary of the document (extractive summary)

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
        >>> document = Doc(text)
        >>> pprint(document.summary)
        ["She's crying with all her might and main, And she won't eat her dinner - "
         'rice pudding again - What is the matter with Mary Jane?',
         "She's perfectly well and she hasn't a pain, And it's lovely rice pudding for "
         'dinner again!']
        >>> document = Doc('just 1 sentence.')
        >>> document.summary
        []
        """
        return self.generate_textrank_summary()

    def extract_lead(self, nsents=3):
        """
        returns the lead-3 sentences (text only) of the document
        if the text is smaller than the requested N, return full text

        >>> from pprint import pprint
        >>> from textpipe.doc import Doc
        >>> text = '''Rice Pudding - Poem by Alan Alexander Milne.
        ... What is the matter with Mary Jane?
        ... She's crying with all her might and main,
        ... And she won't eat her dinner - rice pudding again.
        ... What is the matter with Mary Jane? '''
        >>> document = Doc(text)
        >>> pprint(document.extract_lead())
        ['Rice Pudding - Poem by Alan Alexander Milne.',
         'What is the matter with Mary Jane?',
         "She's crying with all her might and main, And she won't eat her dinner - "
         'rice pudding again.']
        """
        return [s[0] for s in self.sents[:nsents]]

    @property
    def cats(self):
        """
        A dict of categories and their probability in the text.

        >>> from textpipe.doc import Doc
        >>> doc = Doc('Sentence for testing text categorization')
        >>> doc.cats
        {}
        """
        return self.get_cats()

    @functools.lru_cache()
    def get_cats(self, model_name=None):
        """
        Extract a dict of categories and their probability in the text, with the possibility
        of using a custom model.

        >>> from textpipe.doc import Doc
        >>> doc = Doc('Sentence for testing text categorization')
        >>> doc.get_cats()
        {}
        """
        lang = self.language if self.is_reliable_language else self.hint_language
        return self._load_spacy_doc(lang, model_name).cats
