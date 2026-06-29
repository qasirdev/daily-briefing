"""Consensus routing and evaluation (v2.0.0 spec path).

Evaluation logic lives in ``backend.agents.consensus.node``; graph routing
in ``backend.graph.builder``. This module re-exports the public API so
callers and documentation can use the spec-defined import path.
"""

from backend.agents.consensus.node import consensus_evaluator_node
from backend.graph.builder import route_consensus

__all__ = ["consensus_evaluator_node", "route_consensus"]
