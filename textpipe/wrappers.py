"""
Wrappers around classes of external libraries used in Doc class.
"""

import pickle
from functools import lru_cache
from urllib.parse import urlparse

import numpy as np
from gensim.models.keyedvectors import KeyedVectors
from redis import Redis
from redis.exceptions import RedisError
from tqdm import tqdm


class RedisKeyedVectorException(Exception):
    """ Raised when RedisKeyedVectors class fails"""


class RedisKeyedVectors:
    """
    Class to imitate gensim's KeyedVectors, but instead getting the vectors from the memory,
    the vectors will be retrieved from a redis db.
    Based on https://engineering.talentpair.com/serving-word-vectors-
    for-distributed-computations-c5065cbaa02f
    """

    def __init__(self, uri, key='', max_lru_cache_size=1024, idf_weighting='naive'):
        self.word_vec = lru_cache(maxsize=max_lru_cache_size)(self.word_vec)
        self.key = f'w2v_{key}'
        self.idf_weighting = idf_weighting

        try:
            host, port, database = self._parse_uri(uri)
            self._redis = Redis(host, port, database)
        except RedisError as exception:
            # pylint: disable=raise-missing-from
            raise RedisKeyedVectorException(f'The connection to Redis failed while trying to '
                                            f'initiate the client. Redis error message: '
                                            f'{exception}')

    def word_vec(self, word):  # pylint: disable=E0202
        """
        This method is mimicking the word_vec method from the Gensim KeyedVector class. Instead of
        looking it up from an in memory dict, it
        - requests the value from the redis instance, where the key is a combination between
        an optional word vector model key and the word itself
        - decompresses it
        - and finally unpickles it

        :param word: string

        :returns: numpy array of dim of the word vector model (for Google: 300, 1)
        """

        try:
            cache_entry = self._redis.hget(self.key, word)
            if not cache_entry:
                raise KeyError(f'Key {word} does not exist in cache')
            return pickle.loads(cache_entry)
        except RedisError as exception:
            # pylint: disable=raise-missing-from
            raise RedisKeyedVectorException(f'The connection to Redis failed while trying to '
                                            f'retrieve a word vector. Redis error message: '
                                            f'{exception}')
        except TypeError:
            return None

    def __getitem__(self, words):
        """
        Returns numpy array for single word or vstack for multiple words
        """
        if isinstance(words, str):
            return self.word_vec(words)
        return np.vstack([self.word_vec(word) for word in words])

    def __contains__(self, word):
        """
        build in method to quickly check whether a word is available in redis
        """
        return self._redis.hexists(self.key, word)

    def load_keyed_vectors_into_redis(self, model_path, idf_weighting='naive'):
        """
        This function loops over all available words in the loaded word2vec keyed vectors model
        and loads them into the redis instance.
        """
        model = KeyedVectors.load(model_path, mmap='r')
        nr_train_tokens = sum(token_vocab.count for token_vocab in model.vocab.values())
        self.idf_weighting = idf_weighting
        try:
            for word in tqdm(list(model.vocab.keys())):
                if self.idf_weighting == 'naive':
                    idf = model.vocab[word].count
                elif self.idf_weighting == 'log':
                    idf = np.log(nr_train_tokens / (model.vocab[word].count + 1)) + 1
                else:
                    raise ValueError(f'idf_weighting "{self.idf_weighting}" not available; use '
                                     f'"naive" or "log"')
                idf_normalized_vector = model[word] / idf
                self._redis.hset(self.key, word, pickle.dumps(idf_normalized_vector))
        except RedisError as exception:
            # pylint: disable=raise-missing-from
            raise RedisKeyedVectorException(f'RedisError while trying to load model {model} '
                                            f'into redis: {exception}')
        del model

    @property
    def exists(self):
        """
        Indicates whether the key exists.
        """
        return bool(self._redis.exists(self.key))

    @staticmethod
    def _parse_uri(uri):
        parsed = urlparse(uri)
        try:
            host = parsed.hostname
            port = parsed.port
            database = int(parsed.path.replace('/', '')) or 0
        except (AttributeError, ValueError):
            # pylint: disable=raise-missing-from
            raise RedisKeyedVectorException(f'Invalid redis URI: {uri}')
        return host, port, database
