import subprocess
import shutil
import audiomesh


def test_start_stream_runs_jacktrip(monkeypatch):
    calls = []

    class DummyProc:
        def __init__(self, cmd):
            calls.append(cmd)
            self.pid = 42
        def terminate(self):
            pass
        def wait(self, timeout=None):
            pass

    monkeypatch.setattr(shutil, 'which', lambda name: '/usr/bin/jacktrip')
    monkeypatch.setattr(subprocess, 'Popen', DummyProc)

    pid = audiomesh.start_stream('192.168.1.2', 'mysource')

    assert calls == [['jacktrip', '-C', '192.168.1.2', '--clientname', 'mysource']]
    assert pid == 42


def test_stop_stream_terminates_process(monkeypatch):
    events = []

    class DummyProc:
        def terminate(self):
            events.append('terminate')
        def wait(self, timeout=None):
            events.append('wait')

    dummy = DummyProc()
    monkeypatch.setattr(audiomesh, '_PROCESSES', {99: dummy})

    audiomesh.stop_stream(99)

    assert events == ['terminate', 'wait']
