"""Binary packet packing and unpacking for discovery announcements."""

from __future__ import annotations

import struct

# Packet format: 16-byte UUID (as bytes) + H: port + Q: timestamp
PACKET_FMT = "!16sHQ"


def pack_announcement(node_id: bytes, port: int, timestamp: int) -> bytes:
    """Pack announcement data into binary format."""
    return struct.pack(PACKET_FMT, node_id, port, timestamp)


def unpack_announcement(data: bytes) -> tuple[bytes, int, int]:
    """Unpack binary announcement data."""
    node_id, port, timestamp = struct.unpack(PACKET_FMT, data)
    return node_id, port, timestamp
