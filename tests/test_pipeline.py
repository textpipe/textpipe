"""
Testing for textpipe pipeline.py
"""

import tempfile

from textpipe.pipeline import Pipeline

TEXT = 'Test sentence for testing'
PIPELINE = [('Raw',), ('NWords',), ('Complexity',), ('CleanText',)]
PIPE = Pipeline(PIPELINE)


def test_return_dict():
    """
    The returned dictionary should have the same length as the pipeline
    """
    assert len(PIPE(TEXT)) == len(PIPELINE)


def test_load_save():
    """
    The property of saves model should be the same as the loaded model after serialization.
    """
    with tempfile.NamedTemporaryFile() as fp:
        PIPE.language = 'it'
        PIPE.save(fp.name)

        p = Pipeline.load(fp.name)

    assert p.language == PIPE.language
