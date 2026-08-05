"""add source_facts snapshot to resume_versions

Revision ID: 0004
Revises: 0003
Create Date: 2026-08-05

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

JSONVariant = sa.JSON().with_variant(JSONB(), "postgresql")


def upgrade() -> None:
    op.add_column("resume_versions", sa.Column("source_facts", JSONVariant, nullable=True))


def downgrade() -> None:
    op.drop_column("resume_versions", "source_facts")
