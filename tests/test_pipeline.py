"""
Testing for textpipe pipeline.py
"""

from textpipe.pipeline import Pipeline

TEXT = 'Test sentence for testing'
PIPELINE = ['Raw', 'Nwords', 'Complexity', 'CleanText']
PIPE = Pipeline(PIPELINE)


def test_return_dict():
    """
    The returned dictionary should have the same length as the pipeline
    """
    assert len(PIPE(TEXT)) == len(PIPELINE)
