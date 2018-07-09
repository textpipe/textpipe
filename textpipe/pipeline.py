"""
Obtain elements from a textpipe doc, by specifying a pipeline, in a dictionary.
"""
import json

from textpipe.doc import Doc
import textpipe.operation


class Pipeline:
    """
    Create a pipeline instance based on the elements you would want from your text

    >>> pipe = Pipeline(['Raw', 'Nwords', 'CleanText'])
    >>> sorted(pipe('Test sentence <a=>').items())
    [('CleanText', 'Test sentence '), ('Nwords', 2), ('Raw', 'Test sentence <a=>')]
    """
    def __init__(self, operations, language=None, hint_language=None):
        """
        Initialize a Pipeline instance

        Args:
        pipeline: list of elements to obtain from a textpipe doc
        language: 2-letter code for the language of the text
        hint_language: language you expect your text to be
        """
        self.operations = operations
        self.language = language
        self.hint_language = hint_language
        self._operations = []
        # loop over pipeline operations and instantiate operation classes.
        for operation_name in operations:
            oper_cls = getattr(textpipe.operation, operation_name)
            # TODO: pass in config to operation constructor, i.e., oper_cls(config)
            self._operations.append(oper_cls())

    def __call__(self, raw):
        """
        Apply the pipeline to raw text. A dictionary containing the requested elements as keys
        and their content is returned

        Args:
        raw: incoming, unedited text
        """
        doc = Doc(raw, language=self.language, hint_language=self.hint_language)
        result_dict = dict([(oper.__class__.__name__, oper(doc)) for oper in self._operations])
        return result_dict

    def save(self, filename):
        """
        Serializes the pipeline to file (using json)

        Args:
        filename: location of where to serialize pipeline

        >>> filename = "test.json"
        >>> Pipeline(['Nsents', 'CleanText']).save(filename)
        >>> sorted(json.load(open(filename)).items())
        [('hint_language', None), ('language', None), ('operations', ['Nsents', 'CleanText'])]
        """
        with open(filename, 'w') as json_file:
            # serialize all public attrs
            serialize = dict(filter(lambda i: not i[0].startswith('_'), self.__dict__.items()))
            json.dump(serialize, json_file)

    @staticmethod
    def load(filename):
        """
        Loads pipeline from serialized file

        Args:
        filename: location of serialized Pipeline object

        >>> filename = "test.json"
        >>> Pipeline(['Nsents', 'CleanText']).save(filename)
        >>> p = Pipeline.load(filename)
        >>> public_flds = dict(filter(lambda i: not i[0].startswith('_'), p.__dict__.items()))
        >>> sorted(public_flds.items())
        [('hint_language', None), ('language', None), ('operations', ['Nsents', 'CleanText'])]
        """
        with open(filename, 'r') as json_file:
            return Pipeline(**json.load(json_file))

