from typing import Any

import pytest  # type: ignore[import-not-found]
from click.testing import CliRunner

from audiomesh import cli


class DummyServer:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def __call__(self, *args: Any, **kwargs: Any) -> None:
        self.calls.append({"args": args, "kwargs": kwargs})


def test_help() -> None:
    runner = CliRunner()
    result = runner.invoke(cli.cli, ["api", "--help"])
    assert result.exit_code == 0
    assert "--host" in result.output
    assert "--port" in result.output


def test_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    server = DummyServer()
    monkeypatch.setattr(cli, "uvicorn", type("U", (), {"run": server}))
    runner = CliRunner()
    result = runner.invoke(cli.cli, ["api"])
    assert result.exit_code == 0
    args = server.calls[0]["args"]
    assert args[0] == "audiomesh.api:app"
    call = server.calls[0]["kwargs"]
    assert call["host"] == cli.API_HOST  # type: ignore[attr-defined]
    assert call["port"] == cli.API_PORT  # type: ignore[attr-defined]


def test_override(monkeypatch: pytest.MonkeyPatch) -> None:
    server = DummyServer()
    monkeypatch.setattr(cli, "uvicorn", type("U", (), {"run": server}))
    runner = CliRunner()
    result = runner.invoke(cli.cli, ["api", "--host", "0.0.0.0", "--port", "8000"])
    assert result.exit_code == 0
    call = server.calls[0]["kwargs"]
    assert call["host"] == "0.0.0.0"
    assert call["port"] == 8000
