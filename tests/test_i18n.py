from babel.messages.catalog import Catalog
from babel.messages.mofile import write_mo

from oscad_i18n import make_localizer


def test_locale_fallback_plural_and_interpolation(tmp_path):
    for locale, messages in [
        ('de', [('hello', 'Hallo'), ('region', 'Allgemein'),
                (('file', 'files'), ('Datei', 'Dateien')),
                ('Hello %(name)s', 'Hallo %(name)s')]),
        ('de_DE', [('region', 'Regional')]),
    ]:
        directory = tmp_path / locale / 'LC_MESSAGES'
        directory.mkdir(parents=True)
        catalog = Catalog(locale=locale, domain='oscad')
        for message, translation in messages:
            catalog.add(message, translation)
        with (directory / 'oscad.mo').open('wb') as output:
            write_mo(output, catalog)

    localizer = make_localizer('de_DE', [str(tmp_path)], domain='oscad')
    assert localizer.gettext('hello') == 'Hallo'
    assert localizer.gettext('region') == 'Regional'
    assert localizer.gettext('missing') == 'missing'
    assert localizer.ngettext('file', 'files', 2) == 'Dateien'
    assert localizer.gettext('Hello %(name)s', name='Ada') == 'Hallo Ada'
