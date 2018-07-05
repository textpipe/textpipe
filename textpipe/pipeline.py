"""
Obtain elements from a textpipe doc, by specifying a pipeline, in a dictionary.
"""

from textpipe.doc import Doc

import textpipe.operation

class Pipeline:
    """
    Create a pipeline instance based on the elements you would want from your text

    >>> pipe = Pipeline(['Raw', 'Nwords', 'CleanText'])
    >>> sorted(pipe('Test sentence <a=>').items())
    [('CleanText', 'Test sentence '), ('Nwords', 2), ('Raw', 'Test sentence <a=>')]
    """
    def __init__(self, operations, language=None, hint_language='en'):
        """
        Initialize a Pipeline instance

        Args:
        pipeline: list of elements to obtain from a textpipe doc
        language: 2-letter code for the language of the text
        hint_language: language you expect your text to be
        """
        self.operations = []
        # loop over pipeline operations and instantiate operation classes.
        for operation_name in operations:
            oper_cls = getattr(textpipe.operation, operation_name)
            # TODO: pass in config to operation constructor, i.e., oper_cls(config)
            self.operations.append(oper_cls())
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
        result_dict = dict([(oper.__class__.__name__, oper(doc)) for oper in self.operations])
        return result_dict
