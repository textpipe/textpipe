"""
Testing for textpipe pipeline.py
"""

import tempfile

import spacy

from textpipe.pipeline import Pipeline

TEXT = 'Test sentence for testing'
ents_model_nl = spacy.blank('nl')
ents_model_en = spacy.blank('en')
model_path_nl = tempfile.mkdtemp()
model_path_en = tempfile.mkdtemp()
ents_model_nl.to_disk(model_path_nl)
ents_model_en.to_disk(model_path_en)
PIPELINE = [('Raw',), ('NWords',), ('Complexity',), ('CleanText',),
            ('Entities', {'model_mapping': {'nl': 'ents', 'en': 'other_identifier'}})]
PIPE = Pipeline(PIPELINE,
                models=[('ents', 'nl', model_path_nl), ('other_identifier', 'en', model_path_en)],
                allowed_languages=('en', 'nl'))


def test_load_custom_model():
    """
    The custom spacy language modules should be correctly loaded into the pipeline.
    """
    assert PIPE._spacy_nlps['nl']['ents'].lang == 'nl'
    assert PIPE._spacy_nlps['en']['other_identifier'].lang == 'en'


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
