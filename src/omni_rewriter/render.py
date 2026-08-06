"""Public rendering boundary for H3 prompt models."""

from typing import Protocol, runtime_checkable


@runtime_checkable
class H3Renderable(Protocol):
    """Structural interface usable by agents and transport adapters."""

    def render(self) -> str: ...


def render_h3_prompt(value: H3Renderable) -> str:
    """Render any supported output model without coupling to its concrete type."""

    return value.render()
