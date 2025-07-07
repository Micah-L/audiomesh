import json
import os
import signal
from pathlib import Path
from typing import Any

import pytest  # type: ignore[import-not-found]
from click.testing import CliRunner

from audiomesh import cli


class DummyEvent:
    async def wait(self) -> None:
        return

    def set(self) -> None:  # pragma: no cover - interface
        pass


def test_start_invokes_listener(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: dict[str, Any] = {}

    class DummyListener:
        def __init__(
            self,
            handler: Any,
            *,
            interface_ip: str,
            timeout: float,
            on_removed: Any | None = None,
        ) -> None:
            calls["args"] = (interface_ip, timeout)
            self.handler = handler
            self.on_removed = on_removed

        async def start(self) -> None:
            calls["started"] = True
            self.handler(b"a" * 16, "1.1.1.1", 5000, 1)
            if self.on_removed:
                self.on_removed(b"a" * 16)

        async def stop(self) -> None:
            calls["stopped"] = True

    monkeypatch.setattr(cli, "Listener", DummyListener)
    asyncio_mod: Any = cli.asyncio  # type: ignore[attr-defined]
    monkeypatch.setattr(asyncio_mod, "Event", lambda: DummyEvent())

    def fake_run(coro: Any) -> None:
        import asyncio

        loop = asyncio.new_event_loop()
        loop.run_until_complete(coro)

    monkeypatch.setattr(asyncio_mod, "run", fake_run)
    monkeypatch.setattr(signal, "signal", lambda *a, **k: None)

    runner = CliRunner()
    result = runner.invoke(
        cli.discovery,
        [
            "start",
            "--interface",
            "1.2.3.4",
            "--timeout",
            "5",
            "--format",
            "json",
        ],
    )
    assert result.exit_code == 0
    assert calls["args"] == ("1.2.3.4", 5.0)
    assert calls.get("started")
    assert '"event": "added"' in result.output
    assert '"event": "removed"' in result.output


def test_start_daemon_json(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: dict[str, Any] = {}

    class DummyListener:
        def __init__(
            self,
            handler: Any,
            *,
            interface_ip: str,
            timeout: float,
            on_removed: Any | None = None,
        ) -> None:
            self.handler = handler
            self.on_removed = on_removed

        async def start(self) -> None:
            self.handler(b"x" * 16, "2.2.2.2", 6000, 1)
            if self.on_removed:
                self.on_removed(b"x" * 16)

        async def stop(self) -> None:
            calls["stopped"] = True

    monkeypatch.setattr(cli, "Listener", DummyListener)
    asyncio_mod: Any = cli.asyncio  # type: ignore[attr-defined]
    monkeypatch.setattr(asyncio_mod, "Event", lambda: DummyEvent())

    def fake_run(coro: Any) -> None:
        import asyncio

        loop = asyncio.new_event_loop()
        loop.run_until_complete(coro)

    monkeypatch.setattr(asyncio_mod, "run", fake_run)
    monkeypatch.setattr(signal, "signal", lambda *a, **k: None)
    monkeypatch.setattr(cli, "_fork_daemon", lambda p: False)

    runner = CliRunner()
    result = runner.invoke(
        cli.discovery,
        ["start", "--daemon", "--format", "json"],
    )
    assert result.exit_code == 0
    data = [json.loads(line) for line in result.output.strip().splitlines()]
    assert data[0]["event"] == "added"
    assert data[1]["event"] == "removed"


def test_stop_kills_process(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    pid_file = tmp_path / "d.pid"
    pid_file.write_text("123")
    killed = []
    monkeypatch.setattr(os, "kill", lambda pid, sig: killed.append((pid, sig)))
    runner = CliRunner()
    result = runner.invoke(
        cli.discovery,
        ["stop", "--pid-file", str(pid_file)],
    )
    assert result.exit_code == 0
    assert killed == [(123, signal.SIGTERM)]
    assert not pid_file.exists()


def test_stop_missing_file(tmp_path: Path) -> None:
    pid_file = tmp_path / "missing.pid"
    runner = CliRunner()
    result = runner.invoke(
        cli.discovery,
        ["stop", "--pid-file", str(pid_file)],
    )
    assert result.exit_code == 1
    assert "not running" in result.output


def test_start_stale_pid(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    pid_file = tmp_path / "d.pid"
    pid_file.write_text("123")

    def fake_kill(pid: int, sig: int) -> None:
        assert sig == 0
        raise ProcessLookupError()

    monkeypatch.setattr(os, "kill", fake_kill)
    monkeypatch.setattr(os, "fork", lambda: 1)
    monkeypatch.setattr(os, "setsid", lambda: None)

    runner = CliRunner()
    result = runner.invoke(
        cli.discovery,
        ["start", "--daemon", "--pid-file", str(pid_file)],
    )
    assert result.exit_code == 0
    assert pid_file.read_text() == "1"


def test_audio_core_start(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cli, "start_stream", lambda ip, name: 111)
    runner = CliRunner()
    result = runner.invoke(cli.audio_core, ["start", "1.2.3.4", "foo"])
    assert result.exit_code == 0
    assert result.output.strip() == "111"


def test_audio_core_stop_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(pid: int) -> None:
        raise cli.JackError("bad pid")  # type: ignore[attr-defined]

    monkeypatch.setattr(cli, "stop_stream", boom)
    runner = CliRunner()
    result = runner.invoke(cli.audio_core, ["stop", "7"])
    assert result.exit_code == 1
    assert "bad pid" in result.output
