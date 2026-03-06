# Project Documentation

- **ARCHITECTURE.md** — full system design, data flow, project descriptions, infrastructure, and key design decisions. Read this first to understand how Imbryk works.
- **PLAN.md** — phased production release plan with task checklists and open questions. Check this for current progress and next steps.

# Local Development

## Database

The ingestion-api defaults to **SQLite** locally (`apps/ingestion-api/imbryk.db`) and uses **PostgreSQL** in production.

- The `DATABASE_URL` env var selects the engine. When unset, `sqlite:///./imbryk.db` is used.
- The local SQLite DB is **not committed** — it must be created on first checkout by running migrations.
- To initialise or reset the local DB:
  ```sh
  # from apps/ingestion-api/
  rm -f imbryk.db
  uv run alembic upgrade head
  ```
- If you see `no such table` errors when running the API locally, the DB file is missing or stale — delete it and re-run the command above.

## Alembic migrations — SQLite compatibility rules

All migrations run against **both SQLite (local) and PostgreSQL (production)**. SQLite does not support most `ALTER TABLE` sub-commands, so follow these rules whenever writing a new migration:

| Operation | WRONG (PostgreSQL-only) | CORRECT (both dialects) |
|---|---|---|
| Change column default | `op.execute("ALTER TABLE t ALTER COLUMN c SET DEFAULT 'v'")` | `with op.batch_alter_table("t") as b: b.alter_column("c", server_default="v")` |
| Rename column | `op.alter_column("t", "old", new_column_name="new")` bare | wrap in `with op.batch_alter_table("t") as b: b.alter_column(...)` |
| Add/drop constraint | bare `op.create_unique_constraint(...)` | wrap in `batch_alter_table` |

**Rule of thumb:** any DDL that modifies an existing column (rename, change type, change default, add/drop constraint) must be wrapped in `with op.batch_alter_table("table_name") as batch_op: ...`. Adding a new column with `op.add_column` is fine bare.

# UI Guidelines

- **Mobile-first design** — all components and layouts must be designed for small screens first, then enhanced for larger viewports via progressive media queries.
- **Accessibility (WCAG 2.2 AA minimum)** — semantic HTML, ARIA landmarks, skip links, visible focus indicators, sufficient colour contrast (4.5:1 text, 3:1 UI), keyboard navigability, and screen reader compatibility are non-negotiable requirements for every UI component.

<!-- nx configuration start-->
<!-- Leave the start & end comments to automatically receive updates. -->

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
