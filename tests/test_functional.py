import logging

import pytest
from pyramid.exceptions import ConfigurationError

import oscad
import oscad_data as data

DEFAULT_REQUEST = {
    'type': 'proapse',
    'state': 'unmodified',
    'context': 'independent',
    'recipient': '4yourself',
    'form': 'src',
    'ioaccess': 'onlyLocal',
    'license': 'Apache-2.0',
}


@pytest.mark.parametrize('path', [
    '/request', '/matrix', '/about', '/help', '/components',
    '/license/Apache-2.0', '/result/01/Apache-2.0-C1',
])
def test_pages_render(app, path):
    res = app.get(path)
    assert res.content_type == 'text/html'
    assert 'OSCAd' in res.text
    # Bootstrap 5 assets and markup are used.
    assert '/static/css/bootstrap.css' in res.text
    assert '/static/bootstrap/js/bootstrap.bundle.min.js' in res.text
    assert 'navbar-expand-sm' in res.text
    assert 'glyphicon' not in res.text
    assert 'jquery' not in res.text.lower()


def test_index_redirects_to_request(app):
    res = app.get('/', status=303)
    assert res.location.endswith('/request')


def test_request_page_lists_licenses(app):
    res = app.get('/request')
    for license in data.valid_licenses:
        assert 'value="%s"' % license in res.text
    assert 'data-bs-toggle="tooltip"' in res.text
    assert 'form-check-input' in res.text


@pytest.mark.parametrize('path, label', [
    ('/request', 'Question'),
    ('/matrix', 'Matrix Request'),
])
def test_scrollable_tables_are_keyboard_accessible(app, path, label):
    res = app.get(path)
    region = res.html.find(
        'div', attrs={'role': 'region', 'aria-label': label})
    assert region is not None
    assert 'table-responsive' in region.get('class', [])
    assert region.get('tabindex') == '0'
    assert region.find('table') is not None


@pytest.mark.parametrize('name', ['bootstrap', 'main', 'theme'])
def test_stylesheets_are_served(app, name):
    res = app.get('/static/css/%s.css' % name)
    assert res.content_type == 'text/css'


def test_theme_overrides_stylesheets(app):
    assert '#005EBB' in app.get('/static/css/bootstrap.css').text
    assert '.navbar-brands' in app.get('/static/css/theme.css').text


def test_bootstrap_javascript_is_served(app):
    res = app.get('/static/bootstrap/js/bootstrap.bundle.min.js')
    assert 'Bootstrap v5' in res.text


def test_bootstrap_location_setting(make_app):
    app = make_app(
        bootstrap_location='https://cdn.example.com/bootstrap@5/dist/')
    res = app.get('/request')
    assert ('https://cdn.example.com/bootstrap@5/dist/js/'
            'bootstrap.bundle.min.js') in res.text
    assert '/static/css/bootstrap.css' in res.text


def test_result_redirects_to_lsuc(app):
    res = app.post('/result', DEFAULT_REQUEST, status=303)
    assert '/result/' in res.location
    res = res.follow()
    assert 'Apache-2.0' in res.text


def test_result_by_osuc_number(app):
    res = app.post('/result', {'osuc': '01', 'license': 'MIT'}, status=303)
    assert res.location.endswith('/result/01/MIT-C1')


def test_result_as_json(app):
    res = app.post('/result.json', dict(DEFAULT_REQUEST, type='bogus'))
    assert res.json['ok'] is False
    assert 'invalid' in res.json['message']


def test_result_accept_json(app):
    res = app.get('/result/01/MIT-C1',
                  headers={'Accept': 'application/json'})
    assert res.content_type == 'application/json'
    assert res.json['osuc']


def test_invalid_combination_flashes_message(app):
    res = app.post('/result', dict(DEFAULT_REQUEST, type='bogus'),
                   headers={'Referer': 'http://localhost/request'},
                   status=303)
    res = res.follow()
    assert 'alert alert-info' in res.text
    assert 'invalid' in res.text


def test_missing_parameter(app):
    res = app.post('/result.json', {'osuc': '01'})
    assert res.json == {'ok': False, 'message': 'Missing parameter: license'}


def test_unknown_lsuc_is_404(app):
    app.get('/result/01/Nope-C1', status=404)


@pytest.mark.parametrize('lang, expected', [
    ('de', 'Neue Anfrage'),
    ('fr', 'Nouvelle demande'),
    ('en', 'New Request'),
])
def test_locales(app, lang, expected):
    app.set_cookie('_LOCALE_', lang)
    res = app.get('/request')
    assert '<html lang="%s">' % lang in res.text
    assert expected in res.text


@pytest.mark.parametrize('lang, navigation, toggle, icons', [
    ('de', 'Hauptnavigation', 'Navigation ein- oder ausblenden', 'Symbole'),
    ('fr', 'Navigation principale', 'Afficher ou masquer la navigation',
     'Icônes'),
])
def test_new_labels_are_translated(app, lang, navigation, toggle, icons):
    app.set_cookie('_LOCALE_', lang)
    res = app.get('/components')
    assert 'aria-label="%s"' % navigation in res.text
    assert 'aria-label="%s"' % toggle in res.text
    assert icons in res.text


@pytest.mark.parametrize('theme, primary', [
    ('', '#0d6efd'),
    ('oscad_theme_basic', '#005EBB'),
    ('oscad_theme_amadeus', '#005EBB'),
])
def test_theme_assets_under_application_prefix(make_app, theme, primary):
    app = make_app(themes=theme)
    app.extra_environ['SCRIPT_NAME'] = '/oscad'
    page = app.get('/request')
    assert '/oscad/static/css/bootstrap.css' in page.text
    assert '/oscad/static/bootstrap/js/bootstrap.bundle.min.js' in page.text
    assert primary in app.get('/static/css/bootstrap.css').text
    assert app.get('/static/css/theme.css').content_type == 'text/css'
    assert 'Bootstrap v5' in app.get(
        '/static/bootstrap/js/bootstrap.bundle.min.js').text


def test_change_language_rejects_foreign_redirect(app):
    app.get('/language/de', {'next': 'http://evil.example.com/'}, status=403)


def test_translation_downloads(app):
    res = app.get('/translations/de')
    assert res.content_type == 'application/x-gettext'
    assert 'msgid' in res.text
    app.get('/translations/xx', status=404)
    assert 'msgid' in app.get('/translations/oscad.pot').text


def test_session_secret_is_required(make_app, monkeypatch):
    monkeypatch.delenv(oscad.SESSION_SECRET_ENV, raising=False)
    with pytest.raises(ConfigurationError):
        make_app(**{'session.secret': None})
    with pytest.raises(ConfigurationError):
        make_app(**{'session.secret': '  '})


def test_session_secret_from_environment(make_app, monkeypatch):
    monkeypatch.setenv(oscad.SESSION_SECRET_ENV, 'from-env')
    make_app(**{'session.secret': None}).get('/request')


def test_removed_settings_warn(make_app, caplog):
    with caplog.at_level(logging.WARNING, logger='oscad'):
        make_app(**{'scss.asset_path': 'oscad:assets/scss/'})
    assert 'scss.asset_path' in caplog.text


def test_theme_template_override(make_app, tmp_path, monkeypatch):
    theme = tmp_path / 'oscad_test_theme'
    templates = theme / 'templates' / 'oscad'
    templates.mkdir(parents=True)
    (theme / '__init__.py').write_text('')
    (templates / 'headerbar.jinja2').write_text('<p>test-headerbar</p>')
    (templates / 'imprint.jinja2').write_text(
        "{% extends 'base.jinja2' %}{% block content %}test-imprint"
        "{% endblock %}")
    monkeypatch.syspath_prepend(str(tmp_path))

    app = make_app(themes='oscad_test_theme')
    res = app.get('/request')
    assert 'test-headerbar' in res.text
    # The imprint link only appears when a theme provides the template.
    assert '/imprint' in res.text
    assert 'test-imprint' in app.get('/imprint').text


def test_imprint_link_hidden_without_template(app):
    assert '/imprint' not in app.get('/request').text


def test_invalid_license_as_json(app):
    res = app.post('/result.json', dict(DEFAULT_REQUEST, license='Nope'))
    assert res.json['ok'] is False
    assert 'Nope' in res.json['message']
