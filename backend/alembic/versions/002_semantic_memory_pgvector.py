"""Add pgvector extension and semantic_memory table."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

revision: str = "002_semantic_memory_pgvector"
down_revision: str | None = "001_initial_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "semantic_memory",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(1536), nullable=False),
        sa.Column("source_type", sa.String(length=32), nullable=False),
        sa.Column("source_id", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_semantic_memory_user_id", "semantic_memory", ["user_id"])
    op.execute(
        """
        CREATE INDEX semantic_memory_embedding_idx
        ON semantic_memory
        USING hnsw (embedding vector_cosine_ops)
        """,
    )

    op.execute("ALTER TABLE semantic_memory ENABLE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY semantic_memory_user_isolation
        ON semantic_memory
        FOR ALL
        USING (user_id = current_setting('app.user_id', true))
        WITH CHECK (user_id = current_setting('app.user_id', true))
        """,
    )


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS semantic_memory_user_isolation ON semantic_memory")
    op.execute("DROP INDEX IF EXISTS semantic_memory_embedding_idx")
    op.drop_index("ix_semantic_memory_user_id", table_name="semantic_memory")
    op.drop_table("semantic_memory")
