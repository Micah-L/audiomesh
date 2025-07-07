"""Command line interface for audiomesh services."""

from __future__ import annotations

import asyncio
import json
import os
import signal
import sys
import time
from pathlib import Path
from typing import Any, Callable, Dict

import click
from tabulate import tabulate

from discovery.listener import Listener


@click.group()
def discovery() -> None:
    """Manage LAN peer discovery."""


@discovery.command()
@click.option("--interface", default="0.0.0.0", help="NIC IP to bind to")
@click.option("--timeout", default=10.0, type=float, help="Peer expiry (s)")
@click.option(
    "--format",
    "outfmt",
    default="table",
    type=click.Choice(["table", "json"]),
    help="Output format",
)
@click.option("--daemon/--no-daemon", default=False, help="Run backgrounded")
@click.option("--pid-file", default="~/.audiomesh/discovery.pid", help="PID file path")
def start(
    interface: str,
    timeout: float,
    outfmt: str,
    daemon: bool,
    pid_file: str,
) -> None:
    """Start peer discovery."""

    pid_path = Path(os.path.expanduser(pid_file))
    os.makedirs(pid_path.parent, exist_ok=True)

    if daemon:
        pid = os.fork()
        if pid:
            pid_path.write_text(str(pid))
            return
        os.setsid()

    try:
        asyncio.run(_serve(interface, timeout, outfmt, pid_path, daemon))
    except OSError as exc:
        click.echo(f"error: {exc}", err=True)
        if daemon and pid_path.exists():
            pid_path.unlink()
        sys.exit(1)


def _format_table(peers: Dict[str, Dict[str, Any]]) -> str:
    rows = []
    now = time.time()
    for nid, data in peers.items():
        rows.append([nid, data["ip"], data["port"], f"{now - data['ts']:.1f}s ago"])
    if not rows:
        return "no peers"
    return tabulate(rows, headers=["ID", "IP", "PORT", "LAST SEEN"])


def _announcement_handler(
    peers: Dict[str, Dict[str, Any]], outfmt: str
) -> Callable[[bytes, str, int, int], None]:
    def handler(node_id: bytes, ip: str, port: int, ts: int) -> None:
        nid = node_id.hex()
        peers[nid] = {"ip": ip, "port": port, "ts": time.time()}
        if outfmt == "json":
            click.echo(
                json.dumps(
                    {
                        "event": "added",
                        "id": nid,
                        "ip": ip,
                        "port": port,
                        "ts": ts,
                    }
                )
            )
        else:
            click.echo(_format_table(peers))

    return handler


def _remove_handler(
    peers: Dict[str, Dict[str, Any]], outfmt: str
) -> Callable[[bytes], None]:
    def handler(node_id: bytes) -> None:
        nid = node_id.hex()
        peers.pop(nid, None)
        if outfmt == "json":
            click.echo(json.dumps({"event": "removed", "id": nid}))
        else:
            click.echo(_format_table(peers))

    return handler


async def _serve(
    interface: str,
    timeout: float,
    outfmt: str,
    pid_path: Path,
    daemon: bool,
) -> None:
    peers: Dict[str, Dict[str, Any]] = {}
    listener = Listener(
        _announcement_handler(peers, outfmt),
        interface_ip=interface,
        timeout=timeout,
        on_removed=_remove_handler(peers, outfmt),
    )
    await listener.start()

    stop_event = asyncio.Event()

    def _handle(sig: int, frame: Any) -> None:  # pragma: no cover - signal
        stop_event.set()

    signal.signal(signal.SIGINT, _handle)
    signal.signal(signal.SIGTERM, _handle)

    await stop_event.wait()
    await listener.stop()
    if daemon:
        pid_path.unlink(missing_ok=True)


@discovery.command()
@click.option("--pid-file", default="~/.audiomesh/discovery.pid", help="PID file path")
def stop(pid_file: str) -> None:
    """Stop backgrounded discovery."""

    pid_path = Path(os.path.expanduser(pid_file))
    if not pid_path.exists():
        click.echo("discovery not running", err=True)
        sys.exit(1)

    try:
        pid = int(pid_path.read_text())
    except ValueError:
        click.echo("invalid pid file", err=True)
        sys.exit(1)

    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        click.echo("process not found", err=True)
        pid_path.unlink(missing_ok=True)
        sys.exit(1)

    pid_path.unlink(missing_ok=True)


def audio_core(args: list[str] | None = None) -> None:  # pragma: no cover
    """Placeholder audio core service."""
    msg = "audio core service"
    if args is not None:
        msg = f"audio core service {args}"
    print(msg)


def api(args: list[str] | None = None) -> None:  # pragma: no cover
    """Placeholder API service."""
    print("api service" if args is None else f"api service {args}")
