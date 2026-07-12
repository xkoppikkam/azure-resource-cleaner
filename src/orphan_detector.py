from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from .config import CleanerConfig
from .inventory import ResourceRecord


def _normalize(value: str) -> str:
	return value.strip().lower()


def _parse_datetime(value: str | None) -> datetime | None:
	if not value:
		return None
	normalized = value.strip().replace("Z", "+00:00")
	try:
		parsed = datetime.fromisoformat(normalized)
	except ValueError:
		return None
	if parsed.tzinfo is None:
		return parsed.replace(tzinfo=timezone.utc)
	return parsed.astimezone(timezone.utc)


@dataclass(slots=True)
class CleanupCandidate:
	resource: ResourceRecord
	reasons: tuple[str, ...]

	def to_dict(self) -> dict[str, object]:
		return {
			"resource": self.resource.to_dict(),
			"reasons": list(self.reasons),
		}


@dataclass(slots=True)
class SkippedResource:
	resource: ResourceRecord
	reason: str

	def to_dict(self) -> dict[str, object]:
		return {
			"resource": self.resource.to_dict(),
			"reason": self.reason,
		}


def evaluate_resources(
	resources: list[ResourceRecord],
	config: CleanerConfig,
	now: datetime | None = None,
) -> tuple[list[CleanupCandidate], list[SkippedResource]]:
	now = now or datetime.now(timezone.utc)
	cutoff = now - timedelta(days=config.stale_after_days)

	candidates: list[CleanupCandidate] = []
	skipped: list[SkippedResource] = []

	for resource in resources:
		if resource.managed_by:
			skipped.append(SkippedResource(resource, f"managed by {resource.managed_by}"))
			continue

		tags = {_normalize(key): str(value).strip() for key, value in resource.tags.items()}
		cleanup_flag = tags.get(_normalize(config.cleanup_tag))
		if cleanup_flag is None or cleanup_flag.lower() != config.cleanup_tag_value.lower():
			skipped.append(SkippedResource(resource, f"missing {config.cleanup_tag}={config.cleanup_tag_value}"))
			continue

		reasons: list[str] = []

		expires_at = _parse_datetime(tags.get(_normalize(config.expires_tag)))
		if expires_at is not None and expires_at <= now:
			reasons.append(f"expired at {expires_at.isoformat()}")

		created_at = _parse_datetime(tags.get(_normalize(config.created_tag)))
		if created_at is not None and created_at <= cutoff:
			reasons.append(f"older than {config.stale_after_days} days")

		if reasons:
			candidates.append(CleanupCandidate(resource, tuple(reasons)))
		else:
			skipped.append(SkippedResource(resource, "not stale or expired"))

	return candidates, skipped
