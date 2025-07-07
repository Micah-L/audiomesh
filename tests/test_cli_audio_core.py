import pytest  # type: ignore[import-not-found]
from click.testing import CliRunner

from audiomesh import cli


def test_help() -> None:
    runner = CliRunner()
    result = runner.invoke(cli.audio_core, ["--help"])
    assert result.exit_code == 0
    assert "start" in result.output
    assert "stop" in result.output


def test_start_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cli, "start_stream", lambda ip, name: 222)
    runner = CliRunner()
    result = runner.invoke(cli.audio_core, ["start", "127.0.0.1", "foo"])
    assert result.exit_code == 0
    assert result.output.strip() == "222"


def test_stop_success(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[int] = []

    def fake_stop(pid: int) -> None:
        calls.append(pid)

    monkeypatch.setattr(cli, "stop_stream", fake_stop)
    runner = CliRunner()
    result = runner.invoke(cli.audio_core, ["stop", "1234"])
    assert result.exit_code == 0
    assert calls == [1234]
    assert result.output.strip() == "stopped 1234"


def test_start_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(peer_ip: str, name: str) -> int:
        raise cli.JackError("boom")  # type: ignore[attr-defined]

    monkeypatch.setattr(cli, "start_stream", boom)
    runner = CliRunner()
    result = runner.invoke(cli.audio_core, ["start", "1.2.3.4", "foo"])
    assert result.exit_code == 1
    assert "boom" in result.output
