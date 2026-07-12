from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Sequence

from .config import CleanerConfig
from .inventory import list_resources
from .orphan_detector import evaluate_resources
from .report import write_report


def _build_parser() -> argparse.ArgumentParser:
	parser = argparse.ArgumentParser(description="Dry-run Azure resource cleaner")
	parser.add_argument("--subscription-id", help="Azure subscription ID")
	parser.add_argument("--resource-group", help="Resource group to inspect")
	parser.add_argument("--report-dir", help="Directory to store generated reports")
	parser.add_argument("--stale-after-days", type=int, help="Treat resources older than this as stale if tagged")
	return parser


def _load_config(args: argparse.Namespace) -> CleanerConfig:
	env = dict(os.environ)
	if args.subscription_id:
		env["AZURE_SUBSCRIPTION_ID"] = args.subscription_id
	if args.resource_group:
		env["RESOURCE_GROUP"] = args.resource_group
	if args.report_dir:
		env["REPORT_DIR"] = args.report_dir
	if args.stale_after_days is not None:
		env["STALE_AFTER_DAYS"] = str(args.stale_after_days)
	return CleanerConfig.from_env(env)


def main(argv: Sequence[str] | None = None) -> int:
	parser = _build_parser()
	args = parser.parse_args(argv)
	config = _load_config(args)

	resources = list_resources(config.subscription_id, config.resource_group)
	candidates, skipped = evaluate_resources(resources, config)
	json_path, md_path = write_report(config, resources, candidates, skipped)

	print(f"Resources scanned: {len(resources)}")
	print(f"Cleanup candidates: {len(candidates)}")
	print(f"Skipped resources: {len(skipped)}")
	print(f"JSON report: {json_path}")
	print(f"Markdown report: {md_path}")
	print(f"Report destination: {config.report_dir.resolve()}")
	print("No delete action will be performed in this workflow.")
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
