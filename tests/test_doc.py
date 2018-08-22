"""
Testing for textpipe doc.py
"""
import tempfile

import spacy

from textpipe.doc import Doc

TEXT_1 = """<p><b>Text mining</b>, also referred to as <i><b>text data mining</b></i>, roughly
equivalent to <b>text analytics</b>, is the process of deriving high-quality <a href="/wiki/Information"
title="Information">information</a> from <a href="/wiki/Plain_text" title="Plain text">text</a>.
High-quality information is typically derived through the devising of patterns and trends through means
such as <a href="/wiki/Pattern_recognition" title="Pattern recognition">statistical pattern learning</a>.
Text mining usually involves the process of structuring the input text (usually parsing, along with the
addition of some derived linguistic features and the removal of others, and subsequent insertion into a
<a href="/wiki/Database" title="Database">database</a>), deriving patterns within the
<a href="/wiki/Structured_data" class="mw-redirect" title="Structured data">structured data</a>, and
finally evaluation and interpretation of the output. Google is a company named Google.
"""

TEXT_2 = """<p><b>Textmining</b>, ook wel <i>textdatamining</i>, verwijst naar het proces om met
allerhande<a href="/wiki/Informatietechnologie" title="Informatietechnologie">ICT</a>-technieken 
waardevolle informatie te halen uit grote hoeveelheden tekstmateriaal. Met deze technieken wordt 
gepoogd patronen en tendensen te ontwaren. Concreet gaat men teksten softwarematig structureren 
en ontleden, transformeren, vervolgens inbrengen in databanken, en ten slotte evalueren en 
interpreteren. Philips is een bedrijf genaamd Philips.</p>
"""

TEXT_3 = ''

TEXT_4 = """this is a paragraph 
this is a paragraph
"""

TEXT_5 = """Mark Zuckerberg is sinds de oprichting van Facebook de directeur van het bedrijf."""

ents_model = spacy.blank('nl')
custom_spacy_nlps = {'nl': {'ents': ents_model}}

DOC_1 = Doc(TEXT_1)
DOC_2 = Doc(TEXT_2)
DOC_3 = Doc(TEXT_3)
DOC_4 = Doc(TEXT_4)
DOC_5 = Doc(TEXT_5, spacy_nlps=custom_spacy_nlps)


def test_load_custom_model():
    """
    The custom spacy language modules should be correctly loaded into the doc.
    """
    assert DOC_5.language == 'nl'
    assert sorted(DOC_5.find_ents()) == sorted([('Mark Zuckerberg', 'PER'), ('Facebook', 'MISC')])
    assert DOC_5.find_ents({'nl': 'ents'}) == []


def test_nwords_nsents():
    assert DOC_1.nwords == 95
    assert DOC_2.nwords == 54
    assert DOC_3.nwords == 0
    assert DOC_1.nsents == 4
    assert DOC_2.nsents == 4
    assert DOC_3.nsents == 0


def test_entities():
    assert DOC_1.ents.sort() == ['Google'].sort()
    assert DOC_2.ents.sort() == ['Textmining', 'Concreet', 'Philips'].sort()
    assert DOC_3.ents == []


def test_complexity():
    assert DOC_1.complexity == 30.464548969072155
    assert DOC_2.complexity == 17.652500000000003
    assert DOC_3.complexity == 100


def test_clean():
    assert len(TEXT_1) >= len(DOC_1.clean)
    assert len(TEXT_2) >= len(DOC_2.clean)
    assert len(TEXT_3) >= len(DOC_3.clean)


def test_clean_newlines():
    assert ' '.join(TEXT_4.split()) == DOC_4.clean


def test_language():
    assert DOC_1.language == 'en'
    assert DOC_2.language == 'nl'
    assert DOC_3.language == 'un'
