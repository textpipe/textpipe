"""
Testing for textpipe pipeline.py
"""

import tempfile
import pytest
import spacy

from textpipe.pipeline import Pipeline

TEXT = 'Test sentence for testing'
ents_model_nl = spacy.blank('nl')
ents_model_en = spacy.blank('en')
model_path_nl = tempfile.mkdtemp()
model_path_en = tempfile.mkdtemp()
ents_model_nl.to_disk(model_path_nl)
ents_model_en.to_disk(model_path_en)

STEPS = [('Raw',), ('NWords',), ('Complexity',), ('CleanText',),
         ('Entities', {'model_mapping': {'nl': 'ents', 'en': 'other_identifier'}})]

PIPELINE_DEF_KWARGS = dict(models=[('ents', 'nl', model_path_nl),
                                   ('other_identifier', 'en', model_path_en)])

PIPE = Pipeline(STEPS, **PIPELINE_DEF_KWARGS)


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
    assert len(PIPE(TEXT)) == len(STEPS)


def test_load_save():
    """
    The property of saves model should be the same as the loaded model after serialization.
    """
    with tempfile.NamedTemporaryFile() as fp:
        PIPE.language = 'it'
        PIPE.save(fp.name)

        p = Pipeline.load(fp.name)

    assert p.language == PIPE.language


def test_step_definitions_defaulted_properly():
    """
    Steps are structured properly
    :return:
    """
    test_pipe = Pipeline([('Raw',)])

    assert test_pipe.steps[0] == ('Raw', {})


def test_steps_definitions():
    """
    Steps are structured properly
    :return:
    """
    test_pipe = Pipeline(STEPS)

    assert test_pipe.steps[0] == ('Raw', {})
    assert test_pipe.steps[-1] == STEPS[-1]


def test_register_operation():
    """
    The most simple way to extend the pipeline operations is by passing a
    function with proper arguments.
    :return:
    """
    test_pipe = Pipeline(STEPS, models=[('ents', 'nl', model_path_nl), ('other_identifier', 'en', model_path_en)])

    def custom_op(doc, **kwargs):
        return kwargs

    test_pipe.register_operation('CUSTOM_STEP', custom_op)
    assert len(test_pipe._operations) == len(STEPS) + 1


def test_register_op_with_extending_steps_works():
    """
    Calling the custom pipeline operation with an argument should yield the same
    arguments passed back as a result
    :return:
    """
    test_pipe = Pipeline(STEPS, **PIPELINE_DEF_KWARGS)

    def custom_op(doc, context=None, settings=None, **kwargs):
        return settings

    custom_argument = {'argument': 1}
    test_pipe.register_operation('CUSTOM_STEP', custom_op)
    test_pipe.steps.append(('CUSTOM_STEP', custom_argument))

    results = test_pipe(TEXT)

    assert results['CUSTOM_STEP'] == custom_argument


def test_context_data_passed_between_steps():
    """
    Calling the custom pipeline operation with an argument should yield the same
    arguments passed back as a result
    :return:
    """
    test_pipe = Pipeline([], **PIPELINE_DEF_KWARGS)

    def custom_op(doc, context=None, settings=None, **kwargs):
        return 1

    def custom_op2(doc, context=None, settings=None, **kwargs):
        return context

    custom_argument = {'argument': 1}
    test_pipe.register_operation('CUSTOM_STEP', custom_op)
    test_pipe.register_operation('CUSTOM_STEP2', custom_op2)
    test_pipe.steps.append(('CUSTOM_STEP', custom_argument))
    test_pipe.steps.append(('CUSTOM_STEP2', custom_argument))

    results = test_pipe(TEXT)

    assert results['CUSTOM_STEP2']['CUSTOM_STEP'] ==  results['CUSTOM_STEP']


def test_register_not_existing_step_should_throw_exception():
    """
    Checking the condition where we have not yet register the custom
    step, but we try to initialize with the Pipeline entry which we expect to fail
    since the init method will try to load the operation dynamically from the textpipe.operations
    :return:
    """
    custom_steps = STEPS.copy()

    custom_steps.append(('CUSTOM_STEP2', lambda x: None))

    with pytest.raises(AttributeError) as ae:
        test_pipe = Pipeline(custom_steps, **PIPELINE_DEF_KWARGS)
        print(ae.value)
        # somehow placing the following assert statement in the with statement
        # fails to assert, thus moved out of the context of the with
    assert "has no attribute 'CUSTOM_STEP2'" in str(ae.value)
