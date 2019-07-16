"""
Wrappers around classes of external libraries used in Doc class.
"""

import bz2
import pickle
from functools import lru_cache

import numpy as np
from gensim.models.keyedvectors import KeyedVectors
from redis import Redis
from redis.exceptions import RedisError
from tqdm import tqdm


class RedisKeyedVectorException(Exception):
    """ Raised when RedisKeyedVectors class fails"""
    pass


class RedisKeyedVectors(KeyedVectors):
    """
    Class to imitate gensim's KeyedVectors, but instead getting the vectors from the memory,
    the vectors will be retrieved from a redis db.
    Based on https://engineering.talentpair.com/serving-word-vectors-for-distributed-computations-c5065cbaa02f
    """

    def __init__(self, host, port, db=0, key='', max_lru_cache_size=1024):
        self.word_vec = lru_cache(maxsize=max_lru_cache_size)(self.word_vec)
        self.syn0 = []
        self.syn0norm = None
        self.index2word = []
        self.key = f'w2v_{key}'

        try:
            self._redis = Redis(host, port, db)
        except RedisError as e:
            raise RedisKeyedVectorException(f'The connection to Redis failed while trying to '
                                            f'initiate the client. Redis error message: {e}')

    @classmethod
    def load_word2vec_format(cls, **kwargs):
        raise NotImplementedError(
            "You can't load a word model that way. It needs to pre-loaded into redis")

    def save(self, *args, **kwargs):
        raise NotImplementedError("You can't write back to Redis that way.")

    def save_word2vec_format(self, **kwargs):
        raise NotImplementedError("You can't write back to Redis that way.")

    def word_vec(self, word):
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
                raise KeyError(f'Key {cache_entry} does not exist in cache')
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
            return self.word_vec(words)
        return np.vstack([self.word_vec(word) for word in words])

    def __contains__(self, word):
        """ build in method to quickly check whether a word is available in redis """
        return self._redis.hexists(self.key, word)

    def load_keyed_vectors_into_redis(self, model_path):
        """ This function loops over all available words in the loaded word2vec keyed vectors model
        and loads them into the redis instance.
        """
        model = KeyedVectors.load(model_path, mmap='r')
        try:
            for word in tqdm(list(model.vocab.keys())):
                idf_normalized_vector = model[word] / model.vocab[word].count
                self._redis.hset(self.key, word,
                                 bz2.compress(pickle.dumps(idf_normalized_vector)))
            self._redis.hset(self.key, '__EXISTS', '')
        except RedisError as e:
            raise RedisKeyedVectorException(f'RedisError while trying to load model {model} '
                                            f'into redis: {e}')
        del model

    @property
    def exists(self):
        return bool(self._redis.hexists(self.key, '__EXISTS'))
