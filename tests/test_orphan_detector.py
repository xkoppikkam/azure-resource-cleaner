from __future__ import annotations

from datetime import datetime, timezone
import unittest

from src.config import CleanerConfig
from src.inventory import ResourceRecord
from src.orphan_detector import evaluate_resources


class EvaluateResourcesTests(unittest.TestCase):
    def test_skips_managed_resources_and_selects_expired_tagged_resource(self) -> None:
        config = CleanerConfig(
            subscription_id="sub-123",
            resource_group="rg-1",
            dry_run=True,
        )
        resources = [
            ResourceRecord(
                id="/subscriptions/sub-123/resourceGroups/rg-1/providers/Microsoft.Storage/storageAccounts/demo",
                name="demo",
                type="Microsoft.Storage/storageAccounts",
                location="westeurope",
                resource_group="rg-1",
                api_version="2023-01-01",
                tags={"cleanup": "true", "cleanup_after": "2024-01-01T00:00:00Z"},
            ),
            ResourceRecord(
                id="/subscriptions/sub-123/resourceGroups/rg-1/providers/Microsoft.Web/sites/managed",
                name="managed",
                type="Microsoft.Web/sites",
                location="westeurope",
                resource_group="rg-1",
                api_version="2023-01-01",
                tags={"cleanup": "true"},
                managed_by="/subscriptions/sub-123/resourceGroups/rg-1/providers/Microsoft.Web/serverfarms/app-plan",
            ),
        ]

        candidates, skipped = evaluate_resources(
            resources,
            config,
            now=datetime(2024, 1, 2, tzinfo=timezone.utc),
        )

        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0].resource.name, "demo")
        self.assertEqual(len(skipped), 1)
        self.assertIn("managed by", skipped[0].reason)


if __name__ == "__main__":
    unittest.main()