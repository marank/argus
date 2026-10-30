from apps.accounts.permissions import RESOURCES, ResourceKey
from apps.core.features import FLAGS, FeatureKey, ModuleKey
from apps.core.notifications import EVENTS, NotificationEvent


def test_every_flag_is_listed_once():
    assert sorted(flag.key for flag in FLAGS) == sorted([*ModuleKey, *FeatureKey])


def test_every_notification_event_is_listed_once():
    assert sorted(event.key for event in EVENTS) == sorted(NotificationEvent)


def test_every_area_is_listed_once():
    assert sorted(resource.key for resource in RESOURCES) == sorted(ResourceKey)
