import subprocess
import sys
import unittest
from pathlib import Path
from zipfile import ZipFile

from pyramid import testing
from pyramid.httpexceptions import HTTPSeeOther
from pyramid.i18n import make_localizer, TranslationStringFactory

import oscad_data as data
from oscad.models import OSUC


tsf = TranslationStringFactory('oscad')


class DummyRequest(testing.DummyRequest):
    localizer = make_localizer('en', 'oscad:locale')

    def translate(self, *args, **kwargs):
        return self.localizer.translate(tsf(*args, **kwargs))


class UnitTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

        import oscad.views
        self.views = oscad.views

    def tearDown(self):
        testing.tearDown()

    def test_imprint(self):
        request = DummyRequest()
        response = self.views.imprint(request)
        assert response == {}

    def test_change_language(self):
        request = DummyRequest()
        request.cookies['_LOCALE_'] = 'de'
        request.matchdict['lang'] = 'en'

        response = self.views.change_language(request)

        assert isinstance(response, HTTPSeeOther)
        assert '_LOCALE_=en' in response.headers['Set-Cookie']
        assert 'Path=/' in response.headers['Set-Cookie']


def test_data_is_loaded():
    assert data.valid_licenses == sorted(data.licenses)
    assert 'Apache-2.0' in data.valid_licenses
    for details in data.license_details.values():
        assert details['text'].strip()


def test_license_texts_load_without_case_only_alias(tmp_path):
    source = Path(data.__file__).parent
    archive = tmp_path / 'oscad_data.zip'
    with ZipFile(archive, 'w') as package:
        package.write(source / '__init__.py', 'oscad_data/__init__.py')
        for path in (source / 'data').glob('*.yml'):
            package.write(path, 'oscad_data/data/' + path.name)
        for details in data.license_details.values():
            name = details['licensedb_id'] + '.txt'
            package.write(source / 'data' / 'texts' / name,
                          'oscad_data/data/texts/' + name)

    subprocess.run(
        [sys.executable, '-c',
         'import sys; sys.path.insert(0, sys.argv[1]); '
         'import oscad_data; '
         'assert oscad_data.license_details["ZLIB"]["text"]',
         str(archive)],
        cwd=tmp_path, check=True,
    )


def test_every_matrix_osuc_resolves_for_every_license():
    numbers = [row[-1].strip() for row in data.license_matrix()]
    assert numbers
    for number in numbers:
        osuc = OSUC.from_number(number)
        assert osuc is not None, number
        for license in data.valid_licenses:
            assert osuc.get_lsuc(license) is not None, (number, license)
