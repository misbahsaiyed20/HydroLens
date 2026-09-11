# Alembic migrations (Sprint 7)

`Base.metadata.create_all()` (in `app/main.py`) still runs on every
startup for local development convenience — it's a no-op once tables
exist, so this is safe alongside Alembic. Alembic is the path for
*controlled* schema changes (adding/altering columns without touching
existing rows).

## Commands

```bash
# apply all pending migrations
alembic upgrade head

# create a new migration after changing a model
alembic revision --autogenerate -m "describe the change"

# roll back one step
alembic downgrade -1
```

## Existing (pre-Alembic) databases

If your database already has tables from `create_all()` (true for every
deployment through Sprint 6), do **not** run `alembic upgrade head` — it
will try to `CREATE TABLE` on tables that already exist. Instead run:

```bash
alembic stamp head
```

This marks the DB as already at the current revision without executing any
DDL, since the current schema already matches it. Every migration *after*
this one should be applied normally with `alembic upgrade head`.

Alembic's `DATABASE_URL` is read from the same environment variable /
`.env` file as the app itself (see `alembic/env.py`) — never hardcoded in
`alembic.ini`.
