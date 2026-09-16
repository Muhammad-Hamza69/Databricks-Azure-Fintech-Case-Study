"""
Patches the handful of files in this repo that hardcode values tied to a specific Databricks
deployment (workspace host, SQL warehouse id, Auto Loader job id) - every one of those changes
on a fresh `terraform apply`, since Terraform doesn't recreate a resource with the same
auto-generated id/hostname it had before. Run by deploy.sh right after `terraform apply`, with
the new values passed in as DBX_HOST_BARE / WAREHOUSE_ID / JOB_ID env vars.

Uses regex substitution (not exact string replace) so this keeps working on every future
redeploy, not just the first one - it doesn't need to know what the *previous* value was.
"""
import os
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

DBX_HOST_BARE = os.environ["DBX_HOST_BARE"]
WAREHOUSE_ID = os.environ["WAREHOUSE_ID"]
JOB_ID = os.environ["JOB_ID"]

HOST_RE = re.compile(r"adb-\d+\.\d+\.azuredatabricks\.net")
WAREHOUSE_PATH_RE = re.compile(r"warehouses/[0-9a-f]{16}")
WAREHOUSE_JSON_RE = re.compile(r'(\\?"warehouse_id\\?"\s*:\s*\\?")[0-9a-f]{16}(\\?")')
JOB_ID_RE = re.compile(r'(AUTOLOADER_JOB_ID = ")\d+(")')

PATCHES = {
    "dbt/profiles.yml": [
        (HOST_RE, DBX_HOST_BARE),
        (WAREHOUSE_PATH_RE, f"warehouses/{WAREHOUSE_ID}"),
    ],
    "streamlit_app/app.py": [
        (WAREHOUSE_PATH_RE, f"warehouses/{WAREHOUSE_ID}"),
    ],
    "infra/dbx_sql.sh": [
        (HOST_RE, DBX_HOST_BARE),
        (WAREHOUSE_JSON_RE, rf"\g<1>{WAREHOUSE_ID}\g<2>"),
    ],
    "run_pipeline.py": [
        (HOST_RE, DBX_HOST_BARE),
        (JOB_ID_RE, rf"\g<1>{JOB_ID}\g<2>"),
    ],
}


def main() -> None:
    for rel_path, patches in PATCHES.items():
        path = REPO_ROOT / rel_path
        text = path.read_text(encoding="utf-8")
        original = text
        for pattern, replacement in patches:
            text = pattern.sub(replacement, text)
        if text != original:
            path.write_text(text, encoding="utf-8")
            print(f"[patch_files] updated {rel_path}")
        else:
            print(f"[patch_files] WARNING: no change made to {rel_path} - pattern may not match")


if __name__ == "__main__":
    main()
