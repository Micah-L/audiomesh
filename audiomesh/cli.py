"""Command line interface for audiomesh services."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import signal
import sys
import time
from pathlib import Path
from typing import Any, Callable, Dict

import click
from tabulate import tabulate

from discovery.listener import Listener

from . import JackError, start_stream, stop_stream


def _clean_stale_pid(pid_path: Path) -> None:
    if not pid_path.exists():
        return
    try:
        existing_pid = int(pid_path.read_text())
        os.kill(existing_pid, 0)
        click.echo("discovery already running", err=True)
        sys.exit(1)
    except (ProcessLookupError, ValueError, PermissionError):
        pid_path.unlink(missing_ok=True)


def _fork_daemon(pid_path: Path) -> bool:
    try:
        pid = os.fork()
    except OSError as exc:  # pragma: no cover - os.fork error
        click.echo(f"fork failed: {exc}", err=True)
        sys.exit(1)
    if pid:
        pid_path.write_text(str(pid))
        return True
    os.setsid()
    with open(os.devnull, "rb", buffering=0) as devnull:
        os.dup2(devnull.fileno(), sys.stdin.fileno())
    with open(os.devnull, "ab", buffering=0) as devnull:
        os.dup2(devnull.fileno(), sys.stdout.fileno())
        os.dup2(devnull.fileno(), sys.stderr.fileno())
    return False


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
@click.option(
    "--pid-file",
    type=click.Path(path_type=str),
    default="~/.audiomesh/discovery.pid",
    help="PID file path",
)
@click.option("--verbose", is_flag=True, help="Enable debug output")
def start(
    interface: str,
    timeout: float,
    outfmt: str,
    daemon: bool,
    pid_file: Path,
    verbose: bool,
) -> None:
    """Start peer discovery."""

    pid_path = Path(os.path.expanduser(str(pid_file)))
    os.makedirs(pid_path.parent, exist_ok=True)

    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    _clean_stale_pid(pid_path)

    if daemon and _fork_daemon(pid_path):
        return

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
@click.option(
    "--pid-file",
    type=click.Path(path_type=str),
    default="~/.audiomesh/discovery.pid",
    help="PID file path",
)
def stop(pid_file: Path) -> None:
    """Stop backgrounded discovery."""

    pid_path = Path(os.path.expanduser(str(pid_file)))
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


@click.group()
def audio_core() -> None:
    """Commands for managing jacktrip network streams."""


@audio_core.command(name="start")
@click.argument("peer_ip")
@click.argument("client_name")
def start_session(peer_ip: str, client_name: str) -> None:
    """Launch a jacktrip session and print its PID."""
    try:
        pid = start_stream(peer_ip, client_name)
    except JackError as exc:
        click.echo(str(exc), err=True)
        sys.exit(1)
    click.echo(str(pid))


@audio_core.command(name="stop")
@click.argument("pid", type=int)
def stop_session(pid: int) -> None:
    """Terminate a running jacktrip session."""
    try:
        stop_stream(pid)
    except JackError as exc:
        click.echo(str(exc), err=True)
        sys.exit(1)
    click.echo(f"stopped {pid}")


def api(args: list[str] | None = None) -> None:  # pragma: no cover
    """Placeholder API service."""
    print("api service" if args is None else f"api service {args}")
