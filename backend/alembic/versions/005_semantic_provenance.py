"""Add semantic memory provenance and quarantine columns."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "005_semantic_provenance"
down_revision: str | None = "004_episodic_memory"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "semantic_memory",
        sa.Column(
            "source_trust",
            sa.String(length=16),
            nullable=False,
            server_default="internal",
        ),
    )
    op.add_column(
        "semantic_memory",
        sa.Column(
            "content_hash",
            sa.String(length=64),
            nullable=False,
            server_default="",
        ),
    )
    op.add_column(
        "semantic_memory",
        sa.Column(
            "quarantined",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )


def downgrade() -> None:
    op.drop_column("semantic_memory", "quarantined")
    op.drop_column("semantic_memory", "content_hash")
    op.drop_column("semantic_memory", "source_trust")
