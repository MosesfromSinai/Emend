"""add jd_url to applications

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-03

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("applications", sa.Column("jd_url", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("applications", "jd_url")
