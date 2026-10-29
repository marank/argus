from types import SimpleNamespace

from django.db import models
from django.test.utils import isolate_apps

from apps.core.checks import uuid_primary_keys
from apps.core.models import NumberSequence, UUIDModel


def fake_app(name, *models_):
    return SimpleNamespace(name=name, get_models=lambda: list(models_))


def test_our_models_all_have_uuid_primary_keys():
    assert uuid_primary_keys() == []


@isolate_apps("apps.core")
def test_integer_primary_key_is_an_error():
    class Counter(models.Model):  # noqa: DJ008
        class Meta:
            app_label = "core"

    errors = uuid_primary_keys([fake_app("apps.core", Counter)])

    assert [error.id for error in errors] == ["core.E001"]


@isolate_apps("apps.core")
def test_uuid_models_and_third_party_apps_pass():
    class Thing(UUIDModel):
        class Meta:
            app_label = "core"

    class Legacy(models.Model):  # noqa: DJ008
        class Meta:
            app_label = "core"

    assert uuid_primary_keys([fake_app("apps.core", Thing), fake_app("thirdparty", Legacy)]) == []


def test_new_ids_are_uuid7():
    sequence = NumberSequence(code="t", name="T")

    assert sequence.id.version == 7
