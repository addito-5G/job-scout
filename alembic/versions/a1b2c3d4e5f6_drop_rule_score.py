"""drop rule_score columns

Revision ID: a1b2c3d4e5f6
Revises: f8c485a61e10
Create Date: 2026-07-06
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "a1b2c3d4e5f6"
down_revision = "f8c485a61e10"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("vacancies") as batch_op:
        batch_op.drop_column("rule_score_reasons")
        batch_op.drop_column("rule_score")


def downgrade() -> None:
    with op.batch_alter_table("vacancies") as batch_op:
        batch_op.add_column(sa.Column("rule_score", sa.Integer(), nullable=False, server_default="0"))
        batch_op.add_column(sa.Column("rule_score_reasons", sa.Text(), nullable=True))
