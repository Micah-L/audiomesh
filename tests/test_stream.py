import os
import shutil
import signal
import subprocess
from typing import Optional

import pytest  # type: ignore

import audiomesh


def test_start_stream_runs_jacktrip(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = []

    class DummyProc:
        def __init__(
            self,
            cmd: list[str],
            stdout: Optional[int] = None,
            stderr: Optional[int] = None,
        ) -> None:
            calls.append((cmd, stdout, stderr))
            self.pid = 42

        def terminate(self) -> None:
            pass

        def wait(self, timeout: Optional[float] = None) -> None:
            pass

    monkeypatch.setattr(shutil, "which", lambda name: "/usr/bin/jacktrip")
    monkeypatch.setattr(subprocess, "Popen", DummyProc)

    pid = audiomesh.start_stream("192.168.1.2", "mysource")

    assert calls == [
        (
            ["jacktrip", "-C", "192.168.1.2", "--clientname", "mysource"],
            subprocess.DEVNULL,
            subprocess.DEVNULL,
        )
    ]
    assert pid == 42


def test_stop_stream_terminates_process(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events = []

    class DummyProc:
        def terminate(self) -> None:
            events.append("terminate")

        def wait(self, timeout: Optional[float] = None) -> None:
            events.append("wait")

    dummy = DummyProc()
    monkeypatch.setattr(audiomesh, "_PROCESSES", {99: dummy})

    audiomesh.stop_stream(99)

    assert events == ["terminate", "wait"]


def test_stop_stream_kills_on_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events = []

    class DummyProc:
        pid = 50

        def terminate(self) -> None:
            events.append("terminate")

        def wait(self, timeout: Optional[float] = None) -> None:
            raise subprocess.TimeoutExpired(
                cmd="jacktrip",
                timeout=timeout or 0.0,
            )

    dummy = DummyProc()
    monkeypatch.setattr(audiomesh, "_PROCESSES", {50: dummy})
    killed = []
    monkeypatch.setattr(os, "kill", lambda pid, sig: killed.append((pid, sig)))

    audiomesh.stop_stream(50)

    assert events == ["terminate"]
    assert killed == [(50, signal.SIGKILL)]


def test_start_stream_missing_jacktrip_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(shutil, "which", lambda name: None)

    with pytest.raises(audiomesh.JackError):
        audiomesh.start_stream("192.168.1.2", "mysource")


def test_stop_stream_unknown_pid_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(audiomesh, "_PROCESSES", {})

    with pytest.raises(audiomesh.JackError):
        audiomesh.stop_stream(123)