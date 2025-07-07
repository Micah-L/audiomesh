import asyncio
import socket
from typing import Any, List

import pytest  # type: ignore

from discovery import listener as discovery_listener
from discovery.announcer import MULTICAST_GROUP, Announcer
from discovery.exceptions import PeerTimeoutError
from discovery.listener import Listener, ListenerProtocol
from discovery.protocol import pack_announcement


class DummyTransport:
    def __init__(self) -> None:
        self.sent: List[tuple[bytes, Any]] = []

    def sendto(self, data: bytes, addr: Any) -> None:
        self.sent.append((data, addr))

    def close(self) -> None:  # pragma: no cover - used by stop
        pass


class DummySocket:
    def __init__(self) -> None:
        self.opts: List[tuple[int, int, Any]] = []
        self.bound: Any = None

    def setsockopt(self, level: int, optname: int, value: Any) -> None:
        self.opts.append((level, optname, value))

    def bind(self, addr: Any) -> None:
        self.bound = addr

    def close(self) -> None:  # pragma: no cover - interface requirement
        pass


class DummyLoop:
    def __init__(self) -> None:
        self.transport = DummyTransport()

    async def create_datagram_endpoint(
        self: Any, *args: Any, **kwargs: Any
    ) -> tuple[DummyTransport, None]:
        return self.transport, None

    def time(self) -> float:
        return 1.0


def test_announcer_sends_packet(monkeypatch: pytest.MonkeyPatch) -> None:
    async def runner() -> None:
        loop = DummyLoop()
        sock = DummySocket()

        monkeypatch.setattr(asyncio, "get_event_loop", lambda: loop)
        monkeypatch.setattr(socket, "socket", lambda *a, **k: sock)

        ann = Announcer(b"a" * 16, 5001, interval=0.01)
        await ann.start()
        await asyncio.sleep(0.02)
        assert loop.transport.sent
        assert (socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 1) in sock.opts

    asyncio.run(runner())


def test_listener_protocol_calls_handler() -> None:
    events = []

    def handler(node_id: bytes, ip: str, port: int, ts: int) -> None:
        events.append((node_id, ip, port, ts))

    proto = ListenerProtocol(handler)
    pkt = pack_announcement(b"b" * 16, 10, 99)
    proto.datagram_received(pkt, ("1.2.3.4", 0))
    assert events == [(b"b" * 16, "1.2.3.4", 10, 99)]

    events.clear()
    proto.datagram_received(b"bad", ("1.2.3.4", 0))
    assert events == []


def test_listener_start(monkeypatch: pytest.MonkeyPatch) -> None:
    endpoint_called = []

    async def create_datagram_endpoint(
        self: Any, *args: Any, **kwargs: Any
    ) -> tuple[DummyTransport, None]:
        endpoint_called.append(True)
        return DummyTransport(), None

    class FakeSocketModule:
        AF_INET = socket.AF_INET
        SOCK_DGRAM = socket.SOCK_DGRAM
        SOL_SOCKET = socket.SOL_SOCKET
        SO_REUSEADDR = socket.SO_REUSEADDR
        IPPROTO_IP = socket.IPPROTO_IP
        IP_ADD_MEMBERSHIP = socket.IP_ADD_MEMBERSHIP
        IP_MULTICAST_LOOP = socket.IP_MULTICAST_LOOP

        sock = DummySocket()

        @staticmethod
        def inet_aton(addr: str) -> bytes:  # pragma: no cover - simple passthrough
            return socket.inet_aton(addr)

        @staticmethod
        def socket(*args: Any, **kwargs: Any) -> DummySocket:
            return FakeSocketModule.sock

    loop = asyncio.new_event_loop()
    monkeypatch.setattr(loop, "create_datagram_endpoint", create_datagram_endpoint)
    monkeypatch.setattr(discovery_listener, "socket", FakeSocketModule)
    asyncio.set_event_loop(loop)

    async def runner() -> None:
        listener = Listener(lambda *_: None)
        await listener.start()
        await listener.stop()

    loop.run_until_complete(runner())
    assert endpoint_called
    assert (
        socket.IPPROTO_IP,
        socket.IP_MULTICAST_LOOP,
        0,
    ) in FakeSocketModule.sock.opts
    membership = (
        socket.IPPROTO_IP,
        socket.IP_ADD_MEMBERSHIP,
        socket.inet_aton(MULTICAST_GROUP) + socket.inet_aton("0.0.0.0"),
    )
    assert membership in FakeSocketModule.sock.opts


def test_listener_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    timeouts: List[PeerTimeoutError] = []

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    listener = Listener(
        lambda *_: None,
        timeout=0.01,
        on_timeout=lambda e: timeouts.append(e),
    )
    listener._loop = loop
    listener._last_seen[b"x" * 16] = loop.time() - 0.02

    async def runner() -> None:
        task = asyncio.create_task(listener._cleanup_loop())
        await asyncio.sleep(0.02)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    loop.run_until_complete(runner())
    assert timeouts


def test_listener_removes_peer(monkeypatch: pytest.MonkeyPatch) -> None:
    removed: List[bytes] = []

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    listener = Listener(
        lambda *_: None,
        timeout=0.01,
        on_removed=lambda nid: removed.append(nid),
    )
    listener._loop = loop
    listener._handle_announcement(b"z" * 16, "1.2.3.4", 0, 0)
    listener._last_seen[b"z" * 16] = loop.time() - 0.02

    async def runner() -> None:
        task = asyncio.create_task(listener._cleanup_loop())
        await asyncio.sleep(0.02)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    loop.run_until_complete(runner())
    assert removed == [b"z" * 16]
    assert b"z" * 16 not in listener._last_seen


def test_announcer_stop(monkeypatch: pytest.MonkeyPatch) -> None:
    async def runner() -> None:
        loop = DummyLoop()
        sock = DummySocket()

        monkeypatch.setattr(asyncio, "get_event_loop", lambda: loop)
        monkeypatch.setattr(socket, "socket", lambda *a, **k: sock)

        ann = Announcer(b"a" * 16, 5001, interval=0.01)
        await ann.start()
        await ann.stop()
        assert (socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 1) in sock.opts

    asyncio.run(runner())


def test_listener_stop(monkeypatch: pytest.MonkeyPatch) -> None:
    async def runner() -> None:
        loop = DummyLoop()

        class FakeSocketModule:
            AF_INET = socket.AF_INET
            SOCK_DGRAM = socket.SOCK_DGRAM
            SOL_SOCKET = socket.SOL_SOCKET
            SO_REUSEADDR = socket.SO_REUSEADDR
            IPPROTO_IP = socket.IPPROTO_IP
            IP_ADD_MEMBERSHIP = socket.IP_ADD_MEMBERSHIP
            IP_MULTICAST_LOOP = socket.IP_MULTICAST_LOOP

            sock = DummySocket()

            @staticmethod
            def inet_aton(addr: str) -> bytes:
                return socket.inet_aton(addr)

            @staticmethod
            def socket(*args: Any, **kwargs: Any) -> DummySocket:
                return FakeSocketModule.sock

        monkeypatch.setattr(asyncio, "get_event_loop", lambda: loop)
        monkeypatch.setattr(discovery_listener, "socket", FakeSocketModule)

        listener = Listener(lambda *_: None)
        await listener.start()
        await listener.stop()

    asyncio.run(runner())
