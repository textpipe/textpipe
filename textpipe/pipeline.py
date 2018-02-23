"""
Obtain elements from a textpipe doc, by specifying a pipeline, in a dictionary.
"""

from textpipe.textpipe.doc import Doc


class Pipeline:
    """
    Create a pipeline instance based on the elements you would want from your text

    >>> pipe = Pipeline(['raw', 'nwords', 'clean_text'])
    >>> pipe('Test sentence <a=>')
    {'raw': 'Test sentence <a=>', 'nwords': 2, 'clean_text': 'Test sentence '}
    """
    def __init__(self, pipeline):
        """
        Initialize a Pipeline instance

        Args:
        pipeline: list of elements to obtain from a textpipe doc
        """
        self.pipeline = pipeline

    def __call__(self, raw):
        """
        Apply the pipeline to raw text. A dictionary containing the requested elements as keys
        and their content is returned

        Args:
        raw: incoming, unedited text
        """
        doc = Doc(raw)
        result_dict = dict(zip(self.pipeline, [doc.__getattribute__(x) for x in self.pipeline]))
        return result_dict
