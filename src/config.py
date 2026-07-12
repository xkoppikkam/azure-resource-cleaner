from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping


def _env_bool(value: str | None, default: bool = False) -> bool:
	if value is None:
		return default
	return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(value: str | None, default: int) -> int:
	if value is None or value.strip() == "":
		return default
	return int(value)


@dataclass(slots=True)
class CleanerConfig:
	subscription_id: str
	resource_group: str
	report_dir: Path = Path("reports")
	dry_run: bool = True
	stale_after_days: int = 30
	cleanup_tag: str = "cleanup"
	cleanup_tag_value: str = "true"
	expires_tag: str = "cleanup_after"
	created_tag: str = "created_at"

	@classmethod
	def from_env(cls, env: Mapping[str, str] | None = None) -> "CleanerConfig":
		env = env or os.environ
		subscription_id = env.get("AZURE_SUBSCRIPTION_ID") or env.get("ARM_SUBSCRIPTION_ID")
		resource_group = env.get("RESOURCE_GROUP") or env.get("TARGET_RESOURCE_GROUP")

		if not subscription_id:
			raise ValueError("AZURE_SUBSCRIPTION_ID is required")
		if not resource_group:
			raise ValueError("RESOURCE_GROUP is required")

		return cls(
			subscription_id=subscription_id,
			resource_group=resource_group,
			report_dir=Path(env.get("REPORT_DIR", "reports")),
			dry_run=_env_bool(env.get("DRY_RUN"), True),
			stale_after_days=_env_int(env.get("STALE_AFTER_DAYS"), 30),
			cleanup_tag=env.get("CLEANUP_TAG", "cleanup"),
			cleanup_tag_value=env.get("CLEANUP_TAG_VALUE", "true"),
			expires_tag=env.get("EXPIRES_TAG", "cleanup_after"),
			created_tag=env.get("CREATED_TAG", "created_at"),
		)

	def ensure_report_dir(self) -> Path:
		self.report_dir.mkdir(parents=True, exist_ok=True)
		return self.report_dir
