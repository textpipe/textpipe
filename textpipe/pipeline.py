"""
Obtain elements from a textpipe doc, by specifying a pipeline, in a dictionary.
"""
import json

from textpipe.doc import Doc
import textpipe.operation


class Pipeline:
    """
    Create a pipeline instance based on the elements you would want from your text

    >>> pipe = Pipeline([('Raw',), ('NWords',), ('CleanText',)])
    >>> sorted(pipe('Test sentence <a=>').items())
    [('CleanText', 'Test sentence'), ('NWords', 2), ('Raw', 'Test sentence <a=>')]
    """
    def __init__(self, operations, language=None, hint_language=None, **kwargs):
        """
        Initialize a Pipeline instance

        Args:
        operations: list of (operation_name, operation_kwargs)-tuples
        pipeline: list of elements to obtain from a textpipe doc
        language: 2-letter code for the language of the text
        hint_language: language you expect your text to be
        """
        self.operations = operations
        self.language = language
        self.hint_language = hint_language
        self.kwargs = kwargs
        self._operations = []
        # loop over pipeline operations and instantiate operation classes.
        for oper_tuple in operations:
            oper_name = oper_tuple[0]
            oper_kwargs = oper_tuple[1] if len(oper_tuple) > 1 else {}
            oper_cls = getattr(textpipe.operation, oper_name)
            # todo: pass in config to operation constructor, i.e., oper_cls(config)
            self._operations.append(oper_cls(**oper_kwargs))

    def __call__(self, raw):
        """
        Apply the pipeline to raw text. A dictionary containing the requested elements as keys
        and their content is returned

        Args:
        raw: incoming, unedited text
        """
        doc = Doc(raw, language=self.language, hint_language=self.hint_language)
        result_dict = {oper.__class__.__name__: oper(doc) for oper in self._operations}
        return result_dict

    def save(self, filename):
        """ # pylint: disable=line-too-long
        Serializes the pipeline to file (using json)

        Args:
        filename: location of where to serialize pipeline

        >>> filename = "test.json"
        >>> Pipeline([('NSentences',), ('CleanText',)]).save(filename)
        >>> sorted(json.load(open(filename)).items())
        [('hint_language', None), ('kwargs', {}), ('language', None), ('operations', [['NSentences'], ['CleanText']])]
        """
        with open(filename, 'w') as json_file:
            # serialize all public attrs
            serialize = {k: v for k, v in self.__dict__.items() if not k.startswith('_')}
            json.dump(serialize, json_file)

    @staticmethod
    def load(filename):
        """ # pylint: disable=line-too-long
        Loads pipeline from serialized file

        Args:
        filename: location of serialized Pipeline object

        >>> filename = "test.json"
        >>> Pipeline([('NSentences',), ('CleanText',)]).save(filename)
        >>> p = Pipeline.load(filename)
        >>> public_flds = dict(filter(lambda i: not i[0].startswith('_'), p.__dict__.items()))
        >>> sorted(public_flds.items())
        [('hint_language', None), ('kwargs', {}), ('language', None), ('operations', [['NSentences'], ['CleanText']])]
        """
        with open(filename, 'r') as json_file:
            dict_representation = json.load(json_file)
            return Pipeline.from_dict(dict_representation)

    @staticmethod
    def from_dict(dict_representation):
        """ # pylint: disable=line-too-long
        Loads pipeline from dictionary

        Args:
        dict_representation: A dictionary used to instantiate a pipeline object
        >>> d = {'operations': [('NSentences',), ('CleanText',)], 'language': 'it', 'hint_language': None, 'kwargs': {'other': 'args'}}
        >>> p = Pipeline.from_dict(d)
        >>> public_flds = dict(filter(lambda i: not i[0].startswith('_'), p.__dict__.items()))
        >>> sorted(public_flds.items())
        [('hint_language', None), ('kwargs', {'other': 'args'}), ('language', 'it'), ('operations', [('NSentences',), ('CleanText',)])]
        """
        kwargs = dict_representation.pop('kwargs', None)
        if kwargs:
            dict_representation.update(**kwargs)

        return Pipeline(**dict_representation)
