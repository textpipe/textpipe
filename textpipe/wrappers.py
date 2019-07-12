"""
Wrappers around classes of external libraries used in Doc class.
"""

import bz2
import numpy as np
import pickle
import tqdm
from functools import lru_cache

from gensim.models.keyedvectors import KeyedVectors
from redis import Redis
from redis.exceptions import RedisError


class RedisKeyedVectorException(Exception):
    """ Raised when something while loading"""
    pass


class RedisKeyedVectors(KeyedVectors):
    """
    Class to imitate gensim's KeyedVectors, but instead getting the vectors from the memory,
    the vectors will be retrieved from a redis db.
    Based on https://engineering.talentpair.com/serving-word-vectors-for-distributed-computations-c5065cbaa02f
    """

    def __init__(self, host, port, db, key='', max_lru_cache_size=1024):
        # TODO: does this work?
        # TODO: use lang as prefix?
        # TODO: throw error if given model does not exist (instead of returning empty vectors)
        # TODO: add .vocab.count handling to wrapper
        self._word_vec = lru_cache(maxsize=max_lru_cache_size)(self._word_vec)
        self.syn0 = []
        self.syn0norm = None
        self.check_vocab_len()
        self.index2word = []

        try:
            self._redis = Redis(host, port, db)
        except RedisError as e:
            raise RedisKeyedVectorException(f'The connection to Redis failed while trying to '
                                            f'initiate the client. Redis error message: {e}')

        # Optional prefix key for redis entries; the Doc class assumes this to be the language code
        self.key = key

    @classmethod
    def load_word2vec_format(cls, **kwargs):
        raise NotImplementedError(
            "You can't load a word model that way. It needs to pre-loaded into redis")

    def save(self, *args, **kwargs):
        raise NotImplementedError("You can't write back to Redis that way.")

    def save_word2vec_format(self, **kwargs):
        raise NotImplementedError("You can't write back to Redis that way.")

    def _word_vec(self, word):
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
            cache_entry = self._redis.get(word)
            if not cache_entry:
                return None
            return pickle.loads(bz2.decompress(cache_entry))
        except RedisError as e:
            raise RedisKeyedVectorException(f'The connection to Redis failed while trying to '
                                            f'retrieve a word vector. Redis error message: {e}')
        except TypeError:
            return None

    def __getitem__(self, words):
        """
        returns numpy array for single word or vstack for multiple words
        """
        if isinstance(words, str):
            return self._word_vec(words)
        return np.vstack([self._word_vec(word) for word in words])

    def __contains__(self, word):
        """ build in method to quickly check whether a word is available in redis """
        return self._redis_client.exists(word)

    def load_keyed_vectors_into_redis(self, model):
        """ This function loops over all available words in the loaded word2vec keyed vectors model
        and loads them into the redis instance.
        """
        try:
            for word in tqdm(list(model.vocab.keys())):
                self._redis.set(f'{self.key}{word}', bz2.compress(pickle.dumps(model[word])))
        except RedisError as e:
            raise RedisKeyedVectorException(f'RedisError while trying to load model {model} '
                                            f'into redis: {e}')

