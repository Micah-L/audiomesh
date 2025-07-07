"""Command line entry points for audiomesh services."""

from __future__ import annotations


def discovery(args: list[str] | None = None) -> None:
    """Placeholder discovery service."""
    print("discovery service" if args is None else f"discovery service {args}")


def audio_core(args: list[str] | None = None) -> None:
    """Placeholder audio core service."""
    print("audio core service" if args is None else f"audio core service {args}")


def api(args: list[str] | None = None) -> None:
    """Placeholder API service."""
    print("api service" if args is None else f"api service {args}")
