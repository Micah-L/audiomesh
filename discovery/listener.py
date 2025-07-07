"""Listen for peer announcements."""

from __future__ import annotations

import asyncio
import socket
import struct
from typing import Callable, Dict, Optional

from .exceptions import PeerTimeoutError
from .protocol import PACKET_FMT, unpack_announcement

MULTICAST_GROUP = "239.255.0.1"
MULTICAST_PORT = 50000


class ListenerProtocol(asyncio.DatagramProtocol):
    """Protocol handler for discovery announcements."""

    def __init__(self, on_announcement: Callable[[bytes, str, int, int], None]) -> None:
        self.on_announcement = on_announcement

    def datagram_received(self, data: bytes, addr: tuple[str, int]) -> None:
        if len(data) != struct.calcsize(PACKET_FMT):
            return
        node_id, port, ts = unpack_announcement(data)
        self.on_announcement(node_id, addr[0], port, ts)


class Listener:
    """Listen for discovery announcements."""

    def __init__(
        self,
        on_announcement: Callable[[bytes, str, int, int], None],
        *,
        interface_ip: str = "0.0.0.0",
        timeout: float = 10.0,
        on_timeout: Optional[Callable[[PeerTimeoutError], None]] = None,
        on_removed: Optional[Callable[[bytes], None]] = None,
    ) -> None:
        self.on_announcement = on_announcement
        self.interface_ip = interface_ip
        self.timeout = timeout
        self.on_timeout = on_timeout
        self.on_removed = on_removed
        self.transport: Optional[asyncio.DatagramTransport] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._last_seen: Dict[bytes, float] = {}
        self._cleanup_task: Optional[asyncio.Task[None]] = None

    async def start(self) -> None:
        self._loop = asyncio.get_event_loop()
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 0)
        sock.bind((self.interface_ip, MULTICAST_PORT))
        mreq = socket.inet_aton(MULTICAST_GROUP) + socket.inet_aton(self.interface_ip)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        self.transport, _ = await self._loop.create_datagram_endpoint(
            lambda: ListenerProtocol(self._handle_announcement),
            sock=sock,
        )
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    def _handle_announcement(self, node_id: bytes, ip: str, port: int, ts: int) -> None:
        assert self._loop is not None
        self._last_seen[node_id] = self._loop.time()
        self.on_announcement(node_id, ip, port, ts)

    async def _cleanup_loop(self) -> None:
        assert self._loop is not None
        while True:
            now = self._loop.time()
            expired = [
                nid
                for nid, last in self._last_seen.items()
                if now - last > self.timeout
            ]
            for nid in expired:
                self._last_seen.pop(nid, None)
                if self.on_timeout is not None:
                    self.on_timeout(PeerTimeoutError(f"peer {nid!r} timed out"))
                if self.on_removed is not None:
                    self.on_removed(nid)
            await asyncio.sleep(self.timeout)

    async def stop(self) -> None:
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        if self.transport:
            self.transport.close()
