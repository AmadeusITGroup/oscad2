OSCAd 2.0: Open Source Compliance Advisor
=========================================

OSCAd is written in the Python programming language and uses the `Pyramid Web
Framework <https://docs.pylonsproject.org/projects/pyramid/en/latest/>`_
and `Jinja2 Engine <https://jinja.palletsprojects.com/>`_ for templating.
Translations are based on gettext message catalogs. Translations in the
templates are done with the in the templates integrated i18n facilities.
In normal Python code `translationstring <http://docs.pylonsproject.org/projects/translationstring/en/latest/>`_
is used.

OSCAd supports CPython 3.12, 3.13 and 3.14.

Stylesheets are built from SCSS with `Dart Sass <https://sass-lang.com/dart-sass/>`_
and `Bootstrap 5 <https://getbootstrap.com/>`_. Node.js is only needed to
rebuild them; the compiled CSS is committed to the repository and shipped in the
Python package.

History
-------

OSCAd is an interactive version of the
`Open Source License Compendium (OSLiC) <https://github.com/dtag-dbu/oslic>`_.
It has been created to allow anyone to make sure they comply with the licenses
of Open Source components they are using.

This software is the successor to the original OSCAd application written by
Karsten Reincke from the Deutsche Telekom.
You can find the original software on https://github.com/dtag-dbu/oscad.
We thank Mr. Reincke and the Deutsche Telekom for allowing us to be part of a
great community and for entrusting us with further development of OSCAd.
The Deutsche Telekom will continue to maintain and develop the OSLiC document.

Installation
------------

* Create and activate a virtual environment and install OSCAd

.. code-block:: bash

    $ cd $OSCAD_DIR
    $ python3 -m venv .venv
    $ source .venv/bin/activate
    $ pip install -r dev-requirements.txt
    $ pip install -e ".[serve,test,lint]"

  ``requirements.txt`` (runtime and ``waitress``) and ``dev-requirements.txt``
  (all extras) pin tested versions. They are generated from ``pyproject.toml``:

.. code-block:: bash

    $ uv pip compile pyproject.toml --universal --python-version 3.12 --upgrade \
        --extra serve -o requirements.txt
    $ uv pip compile pyproject.toml --universal --python-version 3.12 --upgrade \
        --extra serve --extra test --extra lint --extra translate \
        -o dev-requirements.txt

* Start the application with the development configuration

.. code-block:: bash

    $ pserve development.ini

* Visit http://localhost:6543 in your browser

Configuration
-------------

``session.secret`` signs the session cookie and is required. If it is not set in
the ini file, OSCAd reads it from the ``OSCAD_SESSION_SECRET`` environment
variable and refuses to start when neither is set. ``development.ini`` contains
an insecure development-only value; never reuse it in production.

``bootstrap_location`` optionally serves the Bootstrap JavaScript bundle from a
CDN (see ``production.ini``). The settings ``scss.asset_path`` and
``jquery_location`` are no longer used and are ignored with a warning.

Pyramid/setuptools limitation
-----------------------------

Pyramid 2.1 requires runtime ``setuptools<82``, which is affected by
`CVE-2026-59890 <https://osv.dev/vulnerability/PYSEC-2026-3447>`_ (macOS
source-distribution exclusion handling) and
`GHSA-xmj3-9gf7-h52w <https://osv.dev/vulnerability/GHSA-xmj3-9gf7-h52w>`_
(legacy wheel-to-egg installation on Windows). These concern packaging
operations rather than normal OSCAd request handling. Use isolated builds,
which require setuptools 84.1 or later, and do not install untrusted packages.
Revisit the runtime bound when Pyramid supports a fixed setuptools release; see
`Pyramid issue 3731 <https://github.com/Pylons/pyramid/issues/3731>`_. OSCAd
tracks this limitation in
`OSCAd issue 17 <https://github.com/AmadeusITGroup/oscad2/issues/17>`_.

Isolated builds do not remove the affected setuptools package from the runtime
environment or eliminate dependency-audit findings. Do not override Pyramid's
version bound or uninstall setuptools from that environment. When a compatible
Pyramid release becomes available, update the dependency locks, rerun the
dependency audit, and verify theme overrides, translations, sessions, JSON
responses and deployment under URL prefixes.

Deployment
----------

Run ``pserve production.ini`` (``waitress``, from the ``serve`` extra) behind a
reverse proxy, or use ``wsgi.py`` with mod_wsgi or any other WSGI server.

Tests
-----

* Run the test suite with ``pytest``
* Check code style with ``flake8``
* Run all supported Python versions, flake8 and coverage with ``tox``

Stylesheets
-----------

SCSS sources live in ``oscad/assets/scss`` and in each theme's ``assets/scss``.
After changing them or updating Bootstrap, rebuild and commit the generated
files:

.. code-block:: bash

    $ npm ci
    $ npm run build

``npm run check`` fails if the committed CSS, the Bootstrap JavaScript bundle
or the Bootstrap licence files are out of date; CI runs it on every change.

Translations
------------

To translate the application have a look at the ``locale`` directory in the
packages, most notably ``oscad/locale``.

The translation workflow is a standard gettext workflow using
`Babel <https://babel.pocoo.org/>`_ (installed by the ``translate`` extra or
``dev-requirements.txt``).

First extract translatable messages from the templates and code. This updates
the global translations template ``oscad/locale/oscad.pot``:

.. code-block:: bash

    $ pybabel extract -F babel.cfg -k translate \
        --add-comments=TRANSLATORS: -o oscad/locale/oscad.pot .

Then update all existing language catalogs, or only a single one:

.. code-block:: bash

    $ pybabel update -i oscad/locale/oscad.pot -D oscad -d oscad/locale

    # or
    $ pybabel update -i oscad/locale/oscad.pot -D oscad -d oscad/locale -l fr

Edit the catalogs in ``oscad/locale/<lang>/LC_MESSAGES/`` with your favourite
gettext editor, then compile them:

.. code-block:: bash

    $ pybabel compile -D oscad -d oscad/locale

New languages are created with:

.. code-block:: bash

    $ pybabel init -i oscad/locale/oscad.pot -D oscad -d oscad/locale -l es


Theming
-------

There are several ways to customize the appearance of the application via
themes.
A theme consists of a normal python module containing a set of static assets,
template (-snippets) or translations.
One theme is directly bundled with the application.
It is located in the directory ``oscad_theme_basic/``.
To be recognized as a python module it has to contain a file ``__init__.py``
which can be empty.

Builtin templates and static assets can be overridden shipping a resource of the
same name and type in a theme.
For possible ways of customization look for places in the code where templates
are loaded either via a template renderer or via template inclusion.
When overriding translations make sure to use the correct gettext domain.

As themes are normal packages they don't have to be in the applications source
tree to be used.
Just install them into your virtualenv or put them on ``sys.path``.

Themes are activated with the configuration directive ``themes``. The plural
form indicates, that it's possible to configure multiple cascading themes.
The value of the configuration directive is a whitespace delimited list of
theme names which should be importable.
Otherwise an exception is thrown at startup.

Theme stylesheets
~~~~~~~~~~~~~~~~~

A theme can customise the stylesheets by shipping ``assets/scss/_variables.scss``
(Bootstrap variable overrides such as ``$primary``) and
``assets/scss/theme.scss``. ``npm run build`` compiles them for the bundled
themes into the theme's ``static/css/`` directory, which overrides the base
stylesheets. External themes have to ship their compiled CSS in
``static/css/bootstrap.css`` and ``static/css/theme.css``.

Upgrading from older versions
-----------------------------

* Python 2 and Python < 3.12 are no longer supported.
* Stylesheets are precompiled; the ``/scss`` route, pyScss and
  ``scss.asset_path`` are gone.
* Bootstrap 3 and jQuery were replaced by Bootstrap 5. Custom theme templates
  using Bootstrap 3 classes (``panel``, ``col-md-offset-*``, ``glyphicon``,
  ``data-toggle``) must be migrated.
* ``session.secret`` (or ``OSCAD_SESSION_SECRET``) is now mandatory.
* Packaging uses ``pyproject.toml``; ``setup.py`` and ``fabfile.py`` were
  removed.
