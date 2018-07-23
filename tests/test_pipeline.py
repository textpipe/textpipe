"""
Testing for textpipe pipeline.py
"""

from textpipe.pipeline import Pipeline

TEXT = 'Test sentence for testing'
PIPELINE = ['Raw', 'NWords', 'Complexity', 'CleanText']
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

    PIPE.language = 'it'
    PIPE.save('test.pkl')

    p = Pipeline.load('test.pkl')

    assert p.language == PIPE.language
