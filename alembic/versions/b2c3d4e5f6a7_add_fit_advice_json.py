"""add fit_advice_json to vacancy_matches

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-07-06
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "b2c3d4e5f6a7"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("vacancy_matches") as batch_op:
        batch_op.add_column(sa.Column("fit_advice_json", sa.Text(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("vacancy_matches") as batch_op:
        batch_op.drop_column("fit_advice_json")
