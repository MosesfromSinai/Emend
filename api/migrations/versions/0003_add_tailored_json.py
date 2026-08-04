"""add tailored json to resume_versions

Revision ID: 0003
Revises: 0002
Create Date: 2026-08-03

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

JSONVariant = sa.JSON().with_variant(JSONB(), "postgresql")


def upgrade() -> None:
    op.add_column("resume_versions", sa.Column("tailored", JSONVariant, nullable=True))


def downgrade() -> None:
    op.drop_column("resume_versions", "tailored")
