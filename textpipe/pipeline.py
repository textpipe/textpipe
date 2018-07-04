"""
Obtain elements from a textpipe doc, by specifying a pipeline, in a dictionary.
"""

from textpipe.doc import Doc
import json


class Pipeline:
    """
    Create a pipeline instance based on the elements you would want from your text

    >>> pipe = Pipeline(['raw', 'nwords', 'clean_text'])
    >>> sorted(pipe('Test sentence <a=>').items())
    [('clean_text', 'Test sentence '), ('nwords', 2), ('raw', 'Test sentence <a=>')]
    """
    def __init__(self, **kwargs):
        """
        Initialize a Pipeline instance

        Args:
        pipeline: list of elements to obtain from a textpipe doc
        language: 2-letter code for the language of the text
        hint_language: language you expect your text to be
        """
        self.pipeline = kwargs.get('pipeline', None)
        self.language = kwargs.get('language', None)
        self.hint_language = kwargs.get('hint_language', None)



    def __call__(self, raw):
        """
        Apply the pipeline to raw text. A dictionary containing the requested elements as keys
        and their content is returned

        Args:
        raw: incoming, unedited text
        """
        doc = Doc(raw, language=self.language, hint_language=self.hint_language)
        result_dict = dict(zip(self.pipeline, [doc.__getattribute__(x) for x in self.pipeline]))
        return result_dict

    def save(self, filename):
        """
        Serializes the pipeline to file (using pickle)

        Args:
        filename: location of where to serialize pipeline
        """

        with open(filename, 'w') as json_file:
            json.dump(self.__dict__, json_file)

    @staticmethod
    def load(filename):
        """
        Loads pipeline from serialized file

        Args:
        filename: location of pickled Pipeline object
        """

        with open(filename, 'r') as json_file:  # initialize
            return Pipeline(**json.load(json_file))
