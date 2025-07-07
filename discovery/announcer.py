"""Broadcast node presence over multicast."""

from __future__ import annotations

import asyncio
import logging
import socket
from typing import Optional

from .protocol import pack_announcement

MULTICAST_GROUP = "239.255.0.1"
MULTICAST_PORT = 50000


class Announcer:
    """Periodically broadcast this node's presence."""

    def __init__(
        self,
        node_id: bytes,
        port: int,
        interval: float = 5.0,
        interface_ip: str = "0.0.0.0",
    ) -> None:
        self.node_id = node_id
        self.port = port
        self.interval = interval
        self.interface_ip = interface_ip
        self.transport: Optional[asyncio.DatagramTransport] = None
        self._task: Optional[asyncio.Task[None]] = None

    async def start(self) -> None:
        loop = asyncio.get_event_loop()
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 1)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 0)
        sock.setsockopt(
            socket.IPPROTO_IP,
            socket.IP_MULTICAST_IF,
            socket.inet_aton(self.interface_ip),
        )
        sock.bind((self.interface_ip, 0))
        self.transport, _ = await loop.create_datagram_endpoint(
            lambda: asyncio.DatagramProtocol(),
            sock=sock,
        )
        try:
            await self._send_announcement()
        except OSError as exc:  # pragma: no cover - depends on OS
            logging.getLogger(__name__).warning("initial announcement failed: %s", exc)
        self._task = asyncio.create_task(self._announce_loop())

    async def _send_announcement(self) -> None:
        loop = asyncio.get_event_loop()
        ts = int(loop.time() * 1000)
        packet = pack_announcement(self.node_id, self.port, ts)
        if self.transport is not None:
            self.transport.sendto(packet, (MULTICAST_GROUP, MULTICAST_PORT))

    async def _announce_loop(self) -> None:
        while True:
            await self._send_announcement()
            await asyncio.sleep(self.interval)

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        if self.transport:
            self.transport.close()
