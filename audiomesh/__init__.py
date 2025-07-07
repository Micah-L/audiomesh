"""AudioMesh core functions for JACK network streaming."""

from __future__ import annotations

import os
import shutil
import signal
import subprocess
from typing import Dict


class JackError(RuntimeError):
    """Raised when JACK interaction fails or a required tool is missing."""


_PROCESSES: Dict[int, subprocess.Popen[bytes]] = {}


def start_stream(peer_ip: str, source_name: str) -> int:
    """Start a JACK network stream using ``jacktrip``.

    Parameters
    ----------
    peer_ip:
        Address of the remote JACK peer.
    source_name:
        Name for the local JACK client.

    Returns
    -------
    int
        PID of the launched ``jacktrip`` process.
    """

    if shutil.which("jacktrip") is None:
        raise JackError("jacktrip not installed")

    cmd = ["jacktrip", "-C", peer_ip, "--clientname", source_name]
    try:
        proc = subprocess.Popen(
            cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
    except OSError as exc:
        raise JackError(f"failed to launch jacktrip: {exc}") from exc
    _PROCESSES[proc.pid] = proc
    return proc.pid


def stop_stream(pid: int) -> None:
    """Stop a JACK network stream previously started with :func:`start_stream`."""

    proc = _PROCESSES.pop(pid, None)
    if proc is None:
        raise JackError(f"unknown stream {pid}")

    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        os.kill(proc.pid, signal.SIGKILL)


__all__ = ["start_stream", "stop_stream", "JackError"]
