import os
import signal
from pathlib import Path
from typing import Any

import pytest
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
