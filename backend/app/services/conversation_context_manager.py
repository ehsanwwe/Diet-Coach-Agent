"""
ConversationContextManager: prepares the final messages list for an AI call.

Respects OPENCLAW_CONTEXT_MAX_MESSAGES by pruning the oldest non-system messages.
"""
from __future__ import annotations

from app.services.prompt_builder import PromptData


class ConversationContextManager:
    def __init__(self, max_messages: int = 24) -> None:
        self._max_messages = max_messages

    def prepare(self, prompt: PromptData) -> list[dict[str, str]]:
        """Build the message list from a PromptData, respecting the context window."""
        messages = prompt.to_messages()
        return self._trim(messages)

    def _trim(self, messages: list[dict[str, str]]) -> list[dict[str, str]]:
        if len(messages) <= self._max_messages:
            return messages
        # Always keep system message; trim oldest non-system messages
        system_msgs = [m for m in messages if m.get("role") == "system"]
        non_system = [m for m in messages if m.get("role") != "system"]
        keep_count = max(1, self._max_messages - len(system_msgs))
        trimmed = non_system[-keep_count:]
        return system_msgs + trimmed
