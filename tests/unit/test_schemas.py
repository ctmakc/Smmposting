"""Tests for API schemas."""

import uuid

from apps.api.schemas.brand import BrandCreate, BrandUpdate
from apps.api.schemas.policy import PolicyCreate, PolicyUpdate


class TestBrandSchemas:
    def test_brand_create_defaults(self):
        brand = BrandCreate(name="Test Brand")
        assert brand.name == "Test Brand"
        assert brand.timezone == "UTC"
        assert brand.default_locale == "en"
        assert brand.niches == []
        assert brand.platforms_enabled == []

    def test_brand_create_full(self):
        brand = BrandCreate(
            name="My Brand",
            timezone="Europe/Moscow",
            default_locale="ru",
            niches=["tech", "ai"],
            platforms_enabled=["tiktok", "youtube"],
        )
        assert brand.niches == ["tech", "ai"]

    def test_brand_update_partial(self):
        update = BrandUpdate(name="New Name")
        dumped = update.model_dump(exclude_unset=True)
        assert dumped == {"name": "New Name"}

    def test_brand_update_empty(self):
        update = BrandUpdate()
        dumped = update.model_dump(exclude_unset=True)
        assert dumped == {}


class TestPolicySchemas:
    def test_policy_create_defaults(self):
        brand_id = uuid.uuid4()
        policy = PolicyCreate(brand_id=brand_id)
        assert policy.brand_id == brand_id
        assert policy.risk_threshold_auto_publish == 50
        assert policy.forbidden_topics == []

    def test_policy_update_partial(self):
        update = PolicyUpdate(risk_threshold_auto_publish=75)
        dumped = update.model_dump(exclude_unset=True)
        assert dumped == {"risk_threshold_auto_publish": 75}
