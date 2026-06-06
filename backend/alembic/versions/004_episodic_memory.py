"""Add episodic_memory table for CoALA layer 4."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "004_episodic_memory"
down_revision: str | None = "003_procedural_memory"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "episodic_memory",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("session_id", sa.String(length=64), nullable=False),
        sa.Column("lesson_type", sa.String(length=32), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("superseded_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "metadata",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["superseded_by"],
            ["episodic_memory.id"],
            name="fk_episodic_memory_superseded_by",
        ),
    )
    op.create_index("ix_episodic_memory_user_id", "episodic_memory", ["user_id"])
    op.create_index("ix_episodic_memory_session_id", "episodic_memory", ["session_id"])

    op.execute("ALTER TABLE episodic_memory ENABLE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY episodic_memory_user_isolation
        ON episodic_memory
        FOR ALL
        USING (user_id = current_setting('app.user_id', true))
        WITH CHECK (user_id = current_setting('app.user_id', true))
        """,
    )


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS episodic_memory_user_isolation ON episodic_memory")
    op.drop_index("ix_episodic_memory_session_id", table_name="episodic_memory")
    op.drop_index("ix_episodic_memory_user_id", table_name="episodic_memory")
    op.drop_table("episodic_memory")
