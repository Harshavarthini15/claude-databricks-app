---
name: databricks-app-builder
description: Build, fix and deploy Databricks Apps correctly. Use whenever the user asks to create, build, debug, fix, update or deploy a Databricks App (app.py / app.yaml / requirements.txt), including dashboards that read Databricks tables through a SQL warehouse.
---

# Databricks App Builder

Follow these rules whenever you build, fix or deploy a Databricks App.

## 1. Required files (repo root)

| File | Purpose |
|------|---------|
| `app.py` | The app entry point |
| `app.yaml` | Tells Databricks how to start the app and which env vars to set |
| `requirements.txt` | Python dependencies (installed automatically on deploy) |

## 2. Framework

Use **Python Dash + Plotly** by default, unless the user asks for something else.

## 3. Host and port

The app must listen on `0.0.0.0` and the port Databricks provides:

```python
import os
port = int(os.getenv("DATABRICKS_APP_PORT", "8000"))
app.run(host="0.0.0.0", port=port, debug=False)
```

## 4. Authentication

- Use `databricks-sdk`. `WorkspaceClient()` / `Config()` pick up the app's **service principal** credentials automatically.
- **Never** hard-code tokens, passwords, hostnames or secrets in code or `app.yaml`.
- Grant the app's service principal only what it needs (e.g. `CAN USE` on the warehouse, `SELECT` on tables).

```python
from databricks.sdk import WorkspaceClient
w = WorkspaceClient()  # no token needed inside a Databricks App
```

## 5. Reading tables

Use `databricks-sql-connector` against the SQL warehouse attached as an **app resource**. Read the warehouse ID from an env var set in `app.yaml` — never hard-code IDs.

`app.yaml`:

```yaml
command: ["python", "app.py"]
env:
  - name: DATABRICKS_WAREHOUSE_ID
    valueFrom: sql-warehouse   # resource key of the SQL warehouse attached to the app
```

`app.py`:

```python
import os
from databricks import sql
from databricks.sdk.core import Config

cfg = Config()  # app service principal

def run_query(query: str):
    warehouse_id = os.environ["DATABRICKS_WAREHOUSE_ID"]
    with sql.connect(
        server_hostname=cfg.host,
        http_path=f"/sql/1.0/warehouses/{warehouse_id}",
        credentials_provider=lambda: cfg.authenticate,
    ) as conn, conn.cursor() as cur:
        cur.execute(query)
        return cur.fetchall_arrow().to_pandas()
```

`requirements.txt`:

```
dash
plotly
pandas
databricks-sdk
databricks-sql-connector
```

Handle query errors gracefully in the UI (show a message instead of crashing).

## 6. Deploy

1. **GitHub** – commit and push the app files.
2. **Databricks Git folder** – in Workspace, create/open a Git folder linked to the repo and **Pull** the latest commit.
3. **Apps** – Compute → Apps → create (or open) the app; add the SQL warehouse under **Resources** with key `sql-warehouse` (permission: *Can use*).
4. **Deploy** – click **Deploy**, choose the Git folder path as the source, then check the **Logs** tab for startup errors.

## 7. Pre-push checklist

- [ ] `app.py`, `app.yaml`, `requirements.txt` are present at the app root
- [ ] `app.yaml` has `command: ["python", "app.py"]`
- [ ] App runs on `0.0.0.0` and `DATABRICKS_APP_PORT` (default 8000), `debug=False`
- [ ] No tokens, passwords, hostnames or warehouse IDs hard-coded
- [ ] Warehouse ID comes from an env var set via `valueFrom` in `app.yaml`
- [ ] Every imported package is listed in `requirements.txt`
- [ ] `python -m py_compile app.py` passes
