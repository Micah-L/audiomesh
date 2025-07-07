"""Command line entry points for audiomesh services."""  # pragma: no cover

from __future__ import annotations


def discovery(args: list[str] | None = None) -> None:
    """Placeholder discovery service."""
    msg = "discovery service"
    if args is not None:
        msg = f"discovery service {args}"
    print(msg)


def audio_core(args: list[str] | None = None) -> None:
    """Placeholder audio core service."""
    msg = "audio core service"
    if args is not None:
        msg = f"audio core service {args}"
    print(msg)


def api(args: list[str] | None = None) -> None:
    """Placeholder API service."""
    print("api service" if args is None else f"api service {args}")
