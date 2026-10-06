# Database migrations

Every change to the database's structure — a new table, column, constraint, or
index — is a migration: a numbered file in `versions/` with an `upgrade()` that
makes the change and a `downgrade()` that undoes it. Alembic records which one
the database is on in its `alembic_version` table, and applies whatever comes
after.

For adding or changing a model end to end, the `add-db-model` skill walks the
whole workflow. This file is the reference.

## Commands

| Task | Command |
|---|---|
| Start the local database | `docker compose up -d db` |
| See which migration the database is on | `make migrate-status` |
| Create a migration from model changes | `make migration m="add submissions table"` |
| Apply every pending migration | `make migrate` |
| Undo the most recent migration | `uv run alembic downgrade -1` |
| Check models and database match | `uv run alembic check` |
| See the SQL without running it | `uv run alembic upgrade head --sql` |

## The workflow

1. **Change the model** in `app/<feature>/models.py`. If it's a new models
   file, add its import to the top of `env.py` — otherwise Alembic can't see
   the table, and reads that as "this table was deleted".
2. **Generate**: `make migration m="what changed"`. It's formatted
   automatically.
3. **Read the generated file before applying it.** Autogenerate compares
   structure, not intent, so check:
   - `down_revision` points at the previous migration
   - every constraint has a name (`pk_…`, `uq_…`, `fk_…`, `ix_…`)
   - `downgrade()` exactly reverses `upgrade()`
   - **no unexpected `drop_table` or `drop_column`** — that means a missing
     `env.py` import, or a rename
   - **a rename shows up as drop + add, which destroys the data** — rewrite it
     as `op.alter_column(..., new_column_name=...)`
   - anything that must transform existing data is written by hand
4. **Apply**: `make migrate`.
5. **Test**: `make check` rebuilds a separate test database from every
   migration, checks the models match (`alembic check`), checks the migrations
   reverse, and runs the model tests.

## Rules

- **Migrations never run automatically** — not on app startup, not in the
  container's start command. Two instances starting together would both try
  to apply the same migration, and a half-applied schema can't be safely
  retried. Applying one is always a deliberate command.
- **Never edit a migration once it has been applied anywhere** (another
  machine, a deployed database). Write a new one instead. Editing an
  *unapplied* draft is fine — or delete it and regenerate.
- **The database URL comes from `app.config.settings`**, never `alembic.ini`,
  so no password is ever committed.
- **In production**, the image ships Alembic and this folder, so migrations
  run as a one-off job using the same image — before the new version starts
  serving. Exactly where that step sits in the deploy pipeline is decided when
  the deploy pipeline is built.

## When something goes wrong

- **A very long traceback ending in `Connection refused`** — the database
  isn't running. Every Alembic command except `--sql` needs it:
  `docker compose up -d db`.
- **A generated migration wants to drop a table you still have** — its models
  file isn't imported at the top of `env.py`.
- **`alembic check` reports differences you didn't expect** — a model changed
  without a migration. Run `make migration m="..."` and review the result.

## Files here

- `env.py` — connects Alembic to the app: which database, and which models
  (the import list at the top). Runs on every Alembic command.
- `script.py.mako` — the template each new migration is filled in from.
- `versions/` — the migrations, linked into a chain by `down_revision`.
