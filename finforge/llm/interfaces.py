"""Placeholder interfaces for future local Ollama-backed features."""

from __future__ import annotations

from typing import Protocol


class LocalNarrativeGenerator(Protocol):
    """Contract for future local-only narrative generation components."""

    def generate(self, prompt: str) -> str:
        """Generate text from a local model backend."""
