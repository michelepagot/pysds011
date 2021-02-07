============
Contributing
============

Contributions are welcome, and they are greatly appreciated! Every
little bit helps, and credit will always be given.

Bug reports
===========

When `reporting a bug <https://github.com/michelepagot/pysds011/issues>`_ please include:

    * All known details about used dust sensor (vendor, model, revision, sn when available)
    * Environment informations: Operating system name and version, python version where you are using the module or the cli.
    * Detailed steps to reproduce the bug indicating your expected behaviour

Documentation improvements
==========================

pysds011 could always use more documentation, whether as part of the
official pysds011 docs or in docstrings.

In order to build the documentation locally

1. Create once a developement environment (here a Windows procedure, but linux one is almost the same)::

    virtualenv venv_doc
    venv_doc\Script\activate.bat
    pip install -r docs\requirements.txt


2. Build the documentation::

    cd docs
    make clean
    make html
    start _build\html\index.html

Feature requests and feedback
=============================

The best way to send feedback is to file an issue at https://github.com/michelepagot/pysds011/issues.

If you are proposing a feature:

* Explain in detail how it would work.
* Keep the scope as narrow as possible, to make it easier to implement.
* Remember that this is a volunteer-driven project, and that code contributions are welcome :)

Development
===========

GIT machinery
-------------

This repo uses `main` in place of `master` as primary branch name.
This repo uses `git flow`, so developement mostly take place on `develope` branch.
To set up `pysds011` for local development:

1. Fork `pysds011 <https://github.com/michelepagot/pysds011>`_
   (look for the "Fork" button).
2. Clone your fork locally::

    git clone git@github.com:yourfork/pysds011.git

3. Create a branch for local development (maybe from `develope` branch)::

    git checkout -b name-of-your-bugfix-or-feature

   Now you can make your changes locally.

4. When you're done making changes and run all :ref:`tests<Run unit testing>` and checks.

5. Commit your changes and push your branch to GitHub::

    git add .
    git commit -m "Your detailed description of your changes."
    git push origin name-of-your-bugfix-or-feature

6. Submit a pull request through the GitHub website.

Pull Request Guidelines
-----------------------

If you need some code review or feedback while you're developing the code just make the pull request.

For merging, you should:

1. Include passing tests (``tox`` will come soon) [1]_.
2. Update documentation when there's new API, functionality etc.
3. Add a note to ``CHANGELOG.rst`` about the changes.
4. Add yourself to ``AUTHORS.rst``.

.. [1] If you don't have all the necessary python versions available locally you can rely on Travis - it will
       `run the tests <https://travis-ci.com/michelepagot/pysds011/pull_requests>`_ for each change you add in the pull request.

       It will be slower though ...

Run unit testing
----------------
.. `Run unit testing`

This project uses pytest. Tests are in `tests/` folder. This project is `virtualenv` friendly. To create the test environment, run once::

  virtualenv venv
  source venv/bin/activate
  pip install -e .
  pip install -r tests/requirements.txt


To run tests::

    pytest tests/
