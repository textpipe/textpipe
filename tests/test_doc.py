"""
Testing for textpipe doc.py
"""
from textpipe.textpipe.doc import Doc

TEXT_1 = """Textmining, ook wel textdatamining, verwijst naar het proces om met allerhande ICT-technieken waardevolle 
informatie te halen uit grote hoeveelheden tekstmateriaal. Met deze technieken wordt gepoogd patronen en tendensen 
te ontwaren. Concreet gaat men teksten softwarematig structureren en ontleden, transformeren, vervolgens inbrengen 
in databanken, en ten slotte evalueren en interpreteren.Textmining is verwant aan tekstanalyse; de termen worden 
vaak door elkaar gebruikt
"""

TEXT_2 = """Text mining, also referred to as text data mining, roughly equivalent to text analytics, is the process 
of deriving high-quality information from text. High-quality information is typically derived through the devising 
of patterns and trends through means such as statistical pattern learning. Text mining usually involves the process 
of structuring the input text (usually parsing, along with the addition of some derived linguistic features and the 
removal of others, and subsequent insertion into a database), deriving patterns within the structured data, and finally 
evaluation and interpretation of the output. 'High quality' in text mining usually refers to some combination of 
relevance, novelty, and interestingness. Typical text mining tasks include text categorization, text clustering, 
concept/entity extraction, production of granular taxonomies, sentiment analysis, document summarization, and entity 
relation modeling (i.e., learning relations between named entities).
"""

DOC_1 = Doc(TEXT_1)
DOC_2 = Doc(TEXT_2)


def test_none_text():
    doc = Doc(' ')
    assert doc.clean_text == ''


def test_nwords_nsents():
    assert DOC_1.nwords == 100
    assert DOC_2.nwords == 100
    assert DOC_1.nwords == 100
    assert DOC_2.nsents == 100

def test_entities():
    assert DOC_1.ents == ('',)
    assert DOC_2.ents == ('',)

def test_complexity():
    assert DOC_1.complexity == 0
    assert DOC_2.complexity == 0
