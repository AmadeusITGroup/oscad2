import pytest
from webtest import TestApp

import oscad

BASE_SETTINGS = {
    'pyramid.default_locale_name': 'en',
    'available_locales': 'en de fr',
    'themes': 'oscad_theme_basic',
    'session.secret': 'test-secret',
}


@pytest.fixture
def make_app():
    # Pyramid installs asset overrides process-wide as ``oscad.__loader__``;
    # restore it so themes configured in one test do not leak into others.
    loader = oscad.__loader__

    def factory(**overrides):
        settings = dict(BASE_SETTINGS)
        settings.update(overrides)
        settings = {k: v for k, v in settings.items() if v is not None}
        return TestApp(oscad.main({}, **settings))
    yield factory
    oscad.__loader__ = loader


@pytest.fixture
def app(make_app):
    return make_app()
