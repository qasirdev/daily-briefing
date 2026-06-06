"""Add procedural_memory table for CoALA layer 3."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "003_procedural_memory"
down_revision: str | None = "002_semantic_memory_pgvector"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "procedural_memory",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("agent_id", sa.String(length=50), nullable=False),
        sa.Column("skill_key", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("definition", postgresql.JSONB(), nullable=False),
        sa.Column(
            "allowed_agents",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("success_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_procedural_memory_user_id", "procedural_memory", ["user_id"])
    op.create_unique_constraint(
        "uq_procedural_memory_user_agent_skill",
        "procedural_memory",
        ["user_id", "agent_id", "skill_key"],
    )

    op.execute("ALTER TABLE procedural_memory ENABLE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY procedural_memory_user_isolation
        ON procedural_memory
        FOR ALL
        USING (user_id = current_setting('app.user_id', true))
        WITH CHECK (user_id = current_setting('app.user_id', true))
        """,
    )


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS procedural_memory_user_isolation ON procedural_memory")
    op.drop_constraint("uq_procedural_memory_user_agent_skill", "procedural_memory", type_="unique")
    op.drop_index("ix_procedural_memory_user_id", table_name="procedural_memory")
    op.drop_table("procedural_memory")
