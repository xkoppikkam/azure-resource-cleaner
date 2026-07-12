# Azure Resource Cleaner

This repository runs a safe, read-only Azure resource scan for one selected resource group and generates a report. It does not delete anything yet.

## What it does

The Python code:

* reads the target subscription and resource group from environment variables or workflow inputs
* lists resources in that resource group
* marks only explicitly tagged resources as cleanup candidates
* skips resources that are managed by something else
* writes JSON and Markdown reports into `reports/`

## Where the report goes

Every workflow run creates two report files in `reports/` and uploads them as a GitHub Actions artifact named `azure-resource-cleaner-report`.

The workflow also prints the local report path and the final destination in the step output.

## Required Azure setup

Use GitHub Secrets for:

* `ARM_CLIENT_ID`
* `ARM_CLIENT_SECRET`
* `ARM_TENANT_ID`
* `ARM_SUBSCRIPTION_ID`

## Local run

```bash
pip install -r requirements.txt
python -m src.cleaner --subscription-id <subscription-id> --resource-group <resource-group>
```

## Notes

This version is dry-run only. No delete action is performed.
