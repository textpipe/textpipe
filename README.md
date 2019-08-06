[![Build Status](https://travis-ci.com/textpipe/textpipe.svg?branch=master)](https://travis-ci.com/textpipe/textpipe)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/486c205789b7457f8665a8e4c7cb6246)](https://www.codacy.com/app/textpipe/textpipe?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=textpipe/textpipe&amp;utm_campaign=Badge_Grade)

# textpipe: clean and extract metadata from text

<img align="right" src="https://avatars3.githubusercontent.com/u/40492530?s=400&u=c65c2c8274cbdcd05b1942d1963d7aa2800e6d7f&v=4" height="140" width="140"/>

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
  - Obtain sentiment (polarity and a subjectivity score)
  - Generates word counts
  - Computes minhash for cheap similarity estimation of documents

## Usage example

```python
>>> from textpipe import doc, pipeline
>>> sample_text = 'Sample text! <!DOCTYPE>'
>>> document = doc.Doc(sample_text)
>>> print(document.clean)
'Sample text!'
>>> print(document.language)
'en'
>>> print(document.nwords)
2

>>> pipe = pipeline.Pipeline(['CleanText', 'NWords'])
>>> print(pipe(sample_text))
{'CleanText': 'Sample text!', 'NWords': 2}
```

In order to extend the existing Textpipe operations with your own proprietary operations;

```python
test_pipe = pipeline.Pipeline(['CleanText', 'NWords'])
def custom_op(doc, context=None, settings=None, **kwargs):
    return 1

custom_argument = {'argument' :1 }
test_pipe.register_operation('CUSTOM_STEP', custom_op)
test_pipe.steps.append(('CUSTOM_STEP', custom_argument ))

```

## Contributing

See [CONTRIBUTING](CONTRIBUTING.md) for guidelines for contributors.

## Changes
0.11.5
  - Raise TextpipeMissingModelException instead of KeyError
  
0.11.4
  - Bumps spaCy and datasketch dependencies

0.11.1 
  - Replaces codacy with pylint on CI
  - Fixes pylint issues

0.11.0
  - Adds wrapper around Gensim keyed vectors to construct document embeddings from Redis cache

0.9.0
  - Adds functionality to compute document embeddings using a Gensim word2vec model 

0.8.6
  - Removes non standard utf chars before detecting language

0.8.5
  - Bump spaCy to 2.1.3

0.8.4
  - Fix broken install command

0.8.3
  - Fix broken install command

0.8.2
  - Fix copy-paste error in word vector aggregation ([#118](https://github.com/textpipe/textpipe/issues/118))

0.8.1
  - Fixes bugs in several operations that didn't accept kwargs

0.8.0
  - Bumps Spacy to 2.1

0.7.2
  - Pins Spacy and Pattern versions (with pinned lxml)

0.7.0
  - change operation's registry from list to dict
  - global pipeline data is available across operations via the `context` kwarg
  - load custom operations using `register_operation` in pipeline
  - custom steps (operations) with arguments
