# Contributing
Textpipe is open source, everyone is free to contribute.
But please follow the guidelines below.

## Guidelines
### Code of conduct
Please follow our [code our conduct](CODEOFCONDUCT.md).

### Coding Conventions
All code (except for deployment scripts) is in Python 3.6.
We follow the [Google Python Style Guide](https://github.com/google/styleguide/blob/gh-pages/pyguide.md) which means that we check for style using `pylint` and enforce compliance without warnings and errors.
We use Codacy to check Pull Requests (PRs). PRs need to pass checks before they can be merged to master.

### Testing
All (new) methods and functions have to be unittested using Python `doctests`. Integration tests can be added in the `tests` folder. Current tests use `pytest`.

### Branching Conventions
We use the git flow convention: `feature/<id>/<small-description>`.

### Reviewing
All changes (not matter how minor) to master are made through Pull Requests (PRs).
All PRs are reviewed by at least one reviewer.
If you know that someone may have an opinion on your change, make sure this person reviewed your code before merging.

### CI/CD
We run a Continues Integration (CI) pipeline on [Travis](Travis). Travis continuously runs `script/test`, which in turn runs all tests in the `tests` folder and all `doctests`.
This needs to pass before a PR can be merged to master.

Our Continues Deployment (CD) setup publishes our changes to [PyPi](https://pypi.org/project/textpipe/).

### Communication
We use [Slack](https://textpipe.slack.com/signup) for communication.

## How to contribute

The preferred workflow for contributing to textpipe is to clone the
[GitHub repository](https://github.com/textpipe/textpipe), develop on a branch and make a Pull Request.

Steps:

  1. Create an issue of what you are going to do at [https://github.com/textpipe/textpipe/issues](https://github.com/textpipe/textpipe/issues).

  2. Clone the [repository](https://github.com/textpipe/textpipe)
     ```bash
     $ git clone git@github.com:textpipe/textpipe.git
     $ cd textpipe
     ```

  3. Create a ``feature`` branch to hold your development changes:

     ```bash
     $ git checkout -b {feature|fix}/<issue-id>/<feature-name>
     ```

     Always use a ``feature`` branch. It's good practice to never work on the ``master`` branch!

  4. Develop the feature on your feature branch.

  5. Add yourself to the list of [contributors](CONTRIBUTORS.md).

  6. Add changed files using ``git add`` and then ``git commit`` files:

     ```bash
     $ git add modified_files
     $ git commit
     ```
     to record your changes in Git, then push the changes to your GitHub account with:

     ```bash
     $ git push -u origin {feature|fix}/<issue-id>/<feature-name>
     ```

       * **Be descriptive in your commit messages. Start with a verb in the present tense.**
       * **Group commit changes that belong together.**

  7. Browse to [https://github.com/textpipe/textpipe](https://github.com/textpipe/textpipe) and follow instructions to create Pull Request.
     Make sure you add reviewers to your PR. Your code should be reviewed by at least 1 person and by everyone in the wider contributing team  you know could have an opinion on your change.

  8. Optionally use [Slack](https://textpipe.slack.com/signup) to advertise your PR.

  9. Once your PR is approved and passes all tests, use the `rebase and merge` option.

(If any of the above seems like magic to you, please look up the
[Git documentation](https://git-scm.com/documentation) on the web, or ask a friend or another contributor for help.)
