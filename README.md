[![Build Status](https://travis-ci.com/textpipe/textpipe.svg?branch=master)](https://travis-ci.com/textpipe/textpipe)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/486c205789b7457f8665a8e4c7cb6246)](https://www.codacy.com/app/textpipe/textpipe?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=textpipe/textpipe&amp;utm_campaign=Badge_Grade)

# textpipe: clean and extract metadata from text

`textpipe` is a Python package for converting raw text in to clean, readable text and
extracting metadata from that text. Its functionalities include transforming
raw text into readable text by removing HTML tags and extracting
metadata such as the number of words and named entities from the text.


## Vision: the zen of textpipe

- Designed for use in production pipelines without adult supervision.
- Rechargeable batteries included: provide sane defaults and clear examples to adapt.
- A uniform interface with thin wrappers around state-of-the-art NLP packages.
- As language-agnostic as possible.
- Bring your own models.

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


## Contributing
See [CONTRIBUTING](CONTRIBUTING.md) for guidelines for contributors.
