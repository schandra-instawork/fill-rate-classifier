"""
Actions Package
Purpose: Generate actionable outputs from classified recommendations

This package transforms classified fill rate recommendations into
concrete actions like emails, agent tasks, and alerts.

Modules:
    action_generator: Main action generation logic
    templates: Email and task templates
"""

from .action_generator import (
    ActionGenerator,
    ActionType,
    EmailTemplate,
    AgentTask
)

__all__ = [
    "ActionGenerator",
    "ActionType", 
    "EmailTemplate",
    "AgentTask"
]