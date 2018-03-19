"""
Obtain elements from a textpipe doc, by specifying a pipeline, in a dictionary.
"""

from textpipe.doc import Doc


class Pipeline:
    """
    Create a pipeline instance based on the elements you would want from your text

    >>> pipe = Pipeline(['raw', 'nwords', 'clean_text'])
    >>> sorted(pipe('Test sentence <a=>').items())
    [('clean_text', 'Test sentence '), ('nwords', 2), ('raw', 'Test sentence <a=>')]
    """
    def __init__(self, pipeline, language=None, hint_language='en'):
        """
        Initialize a Pipeline instance

        Args:
        pipeline: list of elements to obtain from a textpipe doc
        """
        self.pipeline = pipeline
        self.language = language
        self.hint_language = hint_language

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
