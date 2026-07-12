from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from .config import CleanerConfig
from .orphan_detector import CleanupCandidate, SkippedResource


def _timestamp() -> str:
	return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def write_report(
	config: CleanerConfig,
	resources: list[object],
	candidates: list[CleanupCandidate],
	skipped: list[SkippedResource],
) -> tuple[Path, Path]:
	report_dir = config.ensure_report_dir()
	stem = f"azure-resource-cleaner-{config.resource_group}-{_timestamp()}"
	json_path = report_dir / f"{stem}.json"
	md_path = report_dir / f"{stem}.md"

	payload = {
		"generated_at": datetime.now(timezone.utc).isoformat(),
		"subscription_id": config.subscription_id,
		"resource_group": config.resource_group,
		"dry_run": config.dry_run,
		"total_resources": len(resources),
		"candidate_count": len(candidates),
		"skipped_count": len(skipped),
		"candidates": [candidate.to_dict() for candidate in candidates],
		"skipped": [item.to_dict() for item in skipped],
	}

	json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")

	type_counts = Counter(candidate.resource.type for candidate in candidates)
	lines = [
		"# Azure Resource Cleaner Report",
		"",
		f"- Generated at: {payload['generated_at']}",
		f"- Subscription: {config.subscription_id}",
		f"- Resource group: {config.resource_group}",
		f"- Dry run: {config.dry_run}",
		f"- Total resources scanned: {len(resources)}",
		f"- Cleanup candidates: {len(candidates)}",
		f"- Skipped resources: {len(skipped)}",
		f"- JSON report: {json_path}",
		f"- Markdown report: {md_path}",
		"",
		"## Candidate types",
	]

	if type_counts:
		for resource_type, count in sorted(type_counts.items(), key=lambda item: (-item[1], item[0])):
			lines.append(f"- {resource_type}: {count}")
	else:
		lines.append("- None")

	lines.extend(["", "## Candidates"])
	if candidates:
		for candidate in candidates:
			lines.append(f"- {candidate.resource.name} ({candidate.resource.type}) - {', '.join(candidate.reasons)}")
	else:
		lines.append("- None")

	lines.extend(["", "## Skipped resources"])
	if skipped:
		for item in skipped:
			lines.append(f"- {item.resource.name} ({item.resource.type}) - {item.reason}")
	else:
		lines.append("- None")

	md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
	return json_path, md_path
