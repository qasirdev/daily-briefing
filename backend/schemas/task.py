"""Task row model for agent validation."""

from typing import Literal

from pydantic import BaseModel, ConfigDict


class TaskRecord(BaseModel):
    """Validated task row from PostgreSQL MCP."""

    model_config = ConfigDict(strict=True)

    id: str
    title: str
    priority: Literal["high", "medium", "low"] = "medium"
    due_date: str | None = None
    status: str = "pending"

    @classmethod
    def from_row(cls, row: dict[str, object]) -> "TaskRecord | None":
        try:
            priority = str(row.get("priority", "medium"))
            if priority not in {"high", "medium", "low"}:
                priority = "medium"
            return cls(
                id=str(row["id"]),
                title=str(row.get("title", "")),
                priority=priority,  # type: ignore[arg-type]
                due_date=str(row["due_date"]) if row.get("due_date") else None,
                status=str(row.get("status", "pending")),
            )
        except (KeyError, ValueError):
            return None
