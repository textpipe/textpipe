# textpipe: clean and extract metadata from text

`textpipe` is a Python package for converting raw text in to clean, readable text and
extracting metadata from that text. Its functionalities include transforming
raw text into readable text by removing HTML tags and extracting
metadata such as the number of words and named entities from the text.


## Features

- Clean raw text by removing `HTML` and other unreadable constructs
- Identify the language of text
- Extract the number of words, number of sentences, named entities from a text
- Calculate the complexity of a text
- Obtain text metadata by specifying a pipeline containing all desired elements

## Usage example

```python
>>> import textpipe 
>>> sample_text = 'Sample text! <!DOCTYPE>'
>>> doc = textpipe.Doc(sample_text)
>>> print(doc.clean_text)
'Sample text!'
>>> print(doc.language)
'en'
>>> print(doc.nwords)
2

>>> pipe = Pipeline(['clean_text', 'language', 'nwords'])
>>> print(pipe(sample_text))
("clean_text":'Sample text!', "language": 'en', "nwords": 2)
```
