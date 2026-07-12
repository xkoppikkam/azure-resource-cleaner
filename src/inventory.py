from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from azure.identity import AzureCliCredential
from azure.mgmt.resource import ResourceManagementClient


def _resource_group_from_id(resource_id: str | None) -> str | None:
	if not resource_id or "/resourceGroups/" not in resource_id:
		return None
	suffix = resource_id.split("/resourceGroups/", 1)[1]
	return suffix.split("/", 1)[0]


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


def list_resources(subscription_id: str, resource_group: str) -> list[ResourceRecord]:
	credential = AzureCliCredential()
	client = ResourceManagementClient(credential, subscription_id)

	records: list[ResourceRecord] = []
	for resource in client.resources.list_by_resource_group(resource_group):
		records.append(
			ResourceRecord(
				id=resource.id,
				name=resource.name,
				type=resource.type,
				location=getattr(resource, "location", None),
				resource_group=_resource_group_from_id(resource.id),
				api_version=getattr(resource, "api_version", None),
				tags={str(key): str(value) for key, value in dict(getattr(resource, "tags", {}) or {}).items()},
				managed_by=getattr(resource, "managed_by", None),
				kind=getattr(resource, "kind", None),
				extra={
					"identity": getattr(resource, "identity", None),
					"sku": getattr(resource, "sku", None),
					"plan": getattr(resource, "plan", None),
				},
			)
		)

	return records
