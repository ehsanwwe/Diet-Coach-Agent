"""Agent tool abstractions."""
from __future__ import annotations
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class AgentExecutionContext:
    db: Any
    user: Any
    locale: str
    nutrition_memory: Any
    chat_session_id: str
    request_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])


@dataclass
class AgentToolResult:
    tool_name: str
    success: bool
    user_visible_summary: str
    data: dict[str, Any] | None = None
    error: str | None = None
    requires_followup: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class AgentTool(ABC):
    name: str = ""
    description: str = ""
    input_schema: dict[str, Any] = {}
    requires_confirmation: bool = False

    @abstractmethod
    def execute(self, context: AgentExecutionContext, arguments: dict[str, Any]) -> AgentToolResult: ...
