"""Multi-agent node registry."""

from backend.agents.calendar.node import calendar_agent_node
from backend.agents.critic.node import critic_agent_node
from backend.agents.focus.node import focus_agent_node
from backend.agents.orchestrator.node import orchestrator_present_node, orchestrator_route_node
from backend.agents.task.node import task_agent_node

__all__ = [
    "calendar_agent_node",
    "critic_agent_node",
    "focus_agent_node",
    "orchestrator_present_node",
    "orchestrator_route_node",
    "task_agent_node",
]
