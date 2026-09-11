"""add authentication fields to users

Adds `password_hash` and `role` to the existing `users` table for the
authentication feature. Both are added in a backward-compatible way:

- `password_hash` is nullable — any pre-existing row (created before auth
  existed) simply has no password and cannot log in; it is not deleted or
  reassigned.
- `role` is added NOT NULL with server_default='CITIZEN' so existing rows
  are backfilled to CITIZEN in the same migration, then the server default
  is dropped so future inserts must set it explicitly via the ORM (the
  User model already defaults new Python-side objects to CITIZEN too).

Existing reports, observations, verification events, and the nullable
Report.user_id relationship are untouched by this migration.

Revision ID: a1c9f3d2b7e4
Revises: e829fbc64e49
Create Date: 2026-08-30 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a1c9f3d2b7e4'
down_revision: Union[str, Sequence[str], None] = 'e829fbc64e49'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('password_hash', sa.String(length=255), nullable=True))
    op.add_column(
        'users',
        sa.Column(
            'role',
            sa.Enum('CITIZEN', 'REVIEWER', name='userrole'),
            nullable=False,
            server_default='CITIZEN',
        ),
    )
    # Drop the server default after backfilling existing rows — the app
    # (Python-side User model default) owns the default going forward.
    # Wrapped in batch mode: a bare `op.alter_column(server_default=None)`
    # emits a raw `ALTER TABLE ... ALTER COLUMN ... DROP DEFAULT`, which
    # SQLite's ALTER TABLE doesn't support at all (verified: fails with
    # "near ALTER: syntax error" on SQLite). Postgres supports the bare
    # form fine, but batch mode is the standard Alembic pattern for a
    # migration that needs to work on both — it's a correctness fix, not
    # a behavior change for Postgres.
    with op.batch_alter_table('users') as batch_op:
        batch_op.alter_column('role', server_default=None)


def downgrade() -> None:
    op.drop_column('users', 'role')
    op.drop_column('users', 'password_hash')
    sa.Enum(name='userrole').drop(op.get_bind(), checkfirst=True)
