"""
Testing for textpipe doc.py
"""
from textpipe.doc import Doc

TEXT_1 = """<p><b>Text mining</b>, also referred to as <i><b>text data mining</b></i>, roughly equivalent
to <b>text analytics</b>, is the process of deriving high-quality <a href="/wiki/Information"
title="Information">information</a> from <a href="/wiki/Plain_text" title="Plain text">text</a>.
High-quality information is typically derived through the devising of patterns and trends through means
such as <a href="/wiki/Pattern_recognition" title="Pattern recognition">statistical pattern learning</a>.
Text mining usually involves the process of structuring the input text (usually parsing, along with the
addition of some derived linguistic features and the removal of others, and subsequent insertion into a
<a href="/wiki/Database" title="Database">database</a>), deriving patterns within the
<a href="/wiki/Structured_data" class="mw-redirect" title="Structured data">structured data</a>, and
finally evaluation and interpretation of the output. Google is a company.
"""

TEXT_2 = """<p><b>Textmining</b>, ook wel <i>textdatamining</i>, verwijst naar het proces om met allerhande 
<a href="/wiki/Informatietechnologie" title="Informatietechnologie">ICT</a>-technieken waardevolle informatie te 
halen uit grote hoeveelheden tekstmateriaal. Met deze technieken wordt gepoogd patronen en tendensen te ontwaren. 
Concreet gaat men teksten softwarematig structureren en ontleden, transformeren, vervolgens inbrengen in databanken, 
en ten slotte evalueren en interpreteren. Philips is een bedrijf. </p>
"""

TEXT_3 = ''

DOC_1 = Doc(TEXT_1)
DOC_2 = Doc(TEXT_2)
DOC_3 = Doc(TEXT_3)


def test_nwords_nsents():
    assert DOC_1.nwords == 85
    assert DOC_2.nwords == 53
    assert DOC_3.nwords == 0
    assert DOC_1.nsents == 4
    assert DOC_2.nsents == 4
    assert DOC_3.nsents == 0


def test_entities():
    assert DOC_1.ents == ['Google']
    assert DOC_2.ents == ['Textmining', 'Concreet', 'Philips']
    assert DOC_3.ents == []


def test_complexity():
    assert DOC_1.complexity == 25.50742977528091
    assert DOC_2.complexity == 0.43250000000003297
    assert DOC_3.complexity == 100


def test_clean_text():
    assert len(TEXT_1) >= len(DOC_1.clean_text)
    assert len(TEXT_2) >= len(DOC_2.clean_text)
    assert len(TEXT_3) >= len(DOC_3.clean_text)


def test_language():
    assert DOC_1.language == 'en'
    assert DOC_2.language == 'nl'
    assert DOC_3.language == 'un'
