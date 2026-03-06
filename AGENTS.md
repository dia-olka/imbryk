<!-- nx configuration start-->
<!-- Leave the start & end comments to automatically receive updates. -->

# Local Development

## Database (ingestion-api)

Local default is **SQLite** (`apps/ingestion-api/imbryk.db`). Production uses PostgreSQL.

- Initialise or reset: `cd apps/ingestion-api && rm -f imbryk.db && uv run alembic upgrade head`
- `no such table` error at runtime = DB file is missing or stale → delete and re-run migrations.

## Alembic migration rules (SQLite + PostgreSQL compatibility)

- **Never** use `op.execute("ALTER TABLE ... ALTER COLUMN ...")` — PostgreSQL-only syntax.
- Any operation that **modifies an existing column** (rename, change default/type, add/drop constraint) **must** be wrapped in `with op.batch_alter_table("table_name") as batch_op:`.
- `op.add_column` (adding a brand-new column) does **not** need batch mode.
- Example:
  ```python
  # WRONG
  op.execute("ALTER TABLE prompts ALTER COLUMN status SET DEFAULT 'quoted'")

  # CORRECT
  with op.batch_alter_table("prompts") as batch_op:
      batch_op.alter_column("status", server_default="quoted")
  ```

# General Guidelines for working with Nx

- For navigating/exploring the workspace, invoke the `nx-workspace` skill first - it has patterns for querying projects, targets, and dependencies
- When running tasks (for example build, lint, test, e2e, etc.), always prefer running the task through `nx` (i.e. `nx run`, `nx run-many`, `nx affected`) instead of using the underlying tooling directly
- Prefix nx commands with the workspace's package manager (e.g., `pnpm nx build`, `npm exec nx test`) - avoids using globally installed CLI
- You have access to the Nx MCP server and its tools, use them to help the user
- For Nx plugin best practices, check `node_modules/@nx/<plugin>/PLUGIN.md`. Not all plugins have this file - proceed without it if unavailable.
- NEVER guess CLI flags - always check nx_docs or `--help` first when unsure

## Scaffolding & Generators

- For scaffolding tasks (creating apps, libs, project structure, setup), ALWAYS invoke the `nx-generate` skill FIRST before exploring or calling MCP tools

## When to use nx_docs

- USE for: advanced config options, unfamiliar flags, migration guides, plugin configuration, edge cases
- DON'T USE for: basic generator syntax (`nx g @nx/react:app`), standard commands, things you already know
- The `nx-generate` skill handles generator discovery internally - don't call nx_docs just to look up generator syntax

<!-- nx configuration end-->
