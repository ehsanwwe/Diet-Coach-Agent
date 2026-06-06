"""Convert AgentTool registry to OpenAI function tool spec format."""
from __future__ import annotations
from typing import Any


def build_openai_specs(registry: dict[str, Any]) -> list[dict]:
    return [
        {"type": "function", "function": {"name": t.name, "description": t.description, "parameters": t.input_schema}}
        for t in registry.values()
    ]
