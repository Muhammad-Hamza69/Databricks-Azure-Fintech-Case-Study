#!/usr/bin/env bash
# Usage: dbx_sql.sh "SELECT ..."
export PATH="$PATH:/c/Users/hp/databricks-cli"
export DATABRICKS_HOST="https://adb-7405616477706025.5.azuredatabricks.net"
export DATABRICKS_AUTH_TYPE="azure-cli"
export MSYS_NO_PATHCONV=1
STMT=$(python -c "import json,sys; print(json.dumps(sys.argv[1]))" "$1")
databricks api post /api/2.0/sql/statements --json "{\"warehouse_id\": \"3ae0ca482ea10df2\", \"statement\": ${STMT}, \"wait_timeout\": \"30s\"}"
