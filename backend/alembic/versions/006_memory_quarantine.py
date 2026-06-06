"""Add quarantine metadata to semantic memory and quarantine columns to episodic memory."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "006_memory_quarantine"
down_revision: str | None = "005_semantic_provenance"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "semantic_memory",
        sa.Column("quarantine_reason", sa.String(length=200), nullable=True),
    )
    op.add_column(
        "semantic_memory",
        sa.Column("quarantined_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.add_column(
        "episodic_memory",
        sa.Column(
            "quarantined",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.add_column(
        "episodic_memory",
        sa.Column("quarantine_reason", sa.String(length=200), nullable=True),
    )
    op.add_column(
        "episodic_memory",
        sa.Column("quarantined_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("episodic_memory", "quarantined_at")
    op.drop_column("episodic_memory", "quarantine_reason")
    op.drop_column("episodic_memory", "quarantined")
    op.drop_column("semantic_memory", "quarantined_at")
    op.drop_column("semantic_memory", "quarantine_reason")
