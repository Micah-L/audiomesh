import uuid

from discovery.protocol import pack_announcement, unpack_announcement


def test_pack_unpack_roundtrip() -> None:
    node_id = uuid.uuid4().bytes
    packet = pack_announcement(node_id, 1234, 42)
    res = unpack_announcement(packet)
    assert res == (node_id, 1234, 42)
