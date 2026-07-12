from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import json
import subprocess


@dataclass(slots=True)
class ResourceRecord:
	id: str
	name: str
	type: str
	location: str | None
	resource_group: str | None
	api_version: str | None
	tags: dict[str, str] = field(default_factory=dict)
	managed_by: str | None = None
	kind: str | None = None
	extra: dict[str, Any] = field(default_factory=dict)

	def to_dict(self) -> dict[str, Any]:
		return {
			"id": self.id,
			"name": self.name,
			"type": self.type,
			"location": self.location,
			"resource_group": self.resource_group,
			"api_version": self.api_version,
			"tags": dict(self.tags),
			"managed_by": self.managed_by,
			"kind": self.kind,
			"extra": dict(self.extra),
		}


def _resource_group_from_id(resource_id: str | None) -> str | None:
	if not resource_id or "/resourceGroups/" not in resource_id:
		return None
	suffix = resource_id.split("/resourceGroups/", 1)[1]
	return suffix.split("/", 1)[0]


def list_resources(subscription_id: str, resource_group: str) -> list[ResourceRecord]:
	command = [
		"az",
		"resource",
		"list",
		"--subscription",
		subscription_id,
		"--resource-group",
		resource_group,
		"--output",
		"json",
	]
	completed = subprocess.run(command, check=True, capture_output=True, text=True)
	items = json.loads(completed.stdout or "[]")

	records: list[ResourceRecord] = []
	for item in items:
		records.append(
			ResourceRecord(
				id=item.get("id", ""),
				name=item.get("name", ""),
				type=item.get("type", ""),
				location=item.get("location"),
				resource_group=item.get("resourceGroup") or _resource_group_from_id(item.get("id")),
				api_version=item.get("apiVersion"),
				tags={str(key): str(value) for key, value in dict(item.get("tags") or {}).items()},
				managed_by=item.get("managedBy"),
				kind=item.get("kind"),
				extra={
					"identity": item.get("identity"),
					"sku": item.get("sku"),
					"plan": item.get("plan"),
				},
			)
		)

	return records
