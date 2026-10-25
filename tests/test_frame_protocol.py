"""
Unit tests for Wireless Frame Protocol.
Tests serialization, deserialization, sequence numbers, checksum validation,
malformed frame detection, and TCP stream socket framing.
"""

import socket
import threading
import pytest
from src.wireless.frame_protocol import (
    WirelessFrame,
    FrameType,
    StatusCode,
    InvalidFrameError,
    ChecksumMismatchError
)


def test_frame_serialization_roundtrip():
    payload = b"Testing wireless frame serialization with payload bytes!"
    frame = WirelessFrame(
        frame_type=FrameType.DATA,
        seq_num=42,
        payload=payload,
        orig_size=100,
        src_size=80,
        flags=WirelessFrame.FLAG_LDPC_CODED | WirelessFrame.FLAG_SOURCE_CODED
    )
    wire_bytes = frame.serialize()
    assert wire_bytes.startswith(b"WIRL")
    assert len(wire_bytes) == WirelessFrame.HEADER_SIZE + len(payload)

    parsed_frame, remaining = WirelessFrame.deserialize(wire_bytes)
    assert len(remaining) == 0
    assert parsed_frame.seq_num == 42
    assert parsed_frame.frame_type == FrameType.DATA
    assert parsed_frame.payload == payload
    assert parsed_frame.orig_size == 100
    assert parsed_frame.src_size == 80
    assert parsed_frame.flags & WirelessFrame.FLAG_LDPC_CODED


def test_ack_frame():
    ack = WirelessFrame.create_ack(seq_num=101, status=StatusCode.OK)
    wire = ack.serialize()
    parsed, _ = WirelessFrame.deserialize(wire)
    assert parsed.frame_type == FrameType.ACK
    assert parsed.seq_num == 101
    assert parsed.status == StatusCode.OK
    assert len(parsed.payload) == 0


def test_checksum_corruption_detection():
    payload = b"Critical transmission data"
    frame = WirelessFrame(seq_num=5, payload=payload)
    wire_bytes = bytearray(frame.serialize())

    # Corrupt one bit in payload
    wire_bytes[-1] ^= 0x01

    with pytest.raises(ChecksumMismatchError):
        WirelessFrame.deserialize(bytes(wire_bytes))


def test_invalid_magic_and_truncated_frame():
    with pytest.raises(InvalidFrameError, match="Insufficient bytes"):
        WirelessFrame.deserialize(b"SHORT")

    bad_magic = b"NOPE" + b"\x00" * 32
    with pytest.raises(InvalidFrameError, match="Invalid frame magic"):
        WirelessFrame.deserialize(bad_magic)


def test_socket_stream_framing_partial_reads():
    # Test reading frame over an actual socket pair with simulated fragmentation
    server_sock, client_sock = socket.socketpair()

    payload = b"Streaming across network socket with partial TCP chunks!"
    frame = WirelessFrame(seq_num=77, payload=payload)
    wire_data = frame.serialize()

    def send_in_fragments():
        # Send byte by byte or in small chunks
        chunk_size = 7
        for i in range(0, len(wire_data), chunk_size):
            client_sock.sendall(wire_data[i : i + chunk_size])
        client_sock.close()

    t = threading.Thread(target=send_in_fragments)
    t.start()

    received_frame = WirelessFrame.read_from_socket(server_sock, timeout=3.0)
    t.join()
    server_sock.close()

    assert received_frame.seq_num == 77
    assert received_frame.payload == payload
