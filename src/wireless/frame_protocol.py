"""
Wireless Frame Protocol & Integrity Verification Module.
Implements a versioned binary frame format with explicit lengths, sequence numbers,
CRC32 integrity verification, and robust TCP stream framing handling partial reads.
"""

from typing import Tuple, Optional, Union
import struct
import binascii
import socket
import enum
import time


class FrameType(enum.IntEnum):
    DATA = 1         # Standard text / telemetry payload frame
    ACK = 2          # Receiver acknowledgment frame
    STREAM = 3       # Continuous stream frame
    PING = 4         # Link connectivity check
    PONG = 5         # Ping reply


class StatusCode(enum.IntEnum):
    OK = 0                   # Success / exact reconstruction
    CHECKSUM_ERROR = 1       # Frame corrupted in transit / CRC mismatch
    DECODE_ERROR = 2         # Source or channel decoding failed
    MALFORMED_FRAME = 3      # Frame header or length violation
    PENDING = 4              # Acknowledgment pending / in-flight


class InvalidFrameError(ValueError):
    """Raised when frame header magic, version, or length is malformed."""
    pass


class ChecksumMismatchError(ValueError):
    """Raised when payload CRC32 does not match the frame header CRC."""
    pass


class WirelessFrame:
    """
    Binary Wire Frame structure:
    Offset  Size  Field          Description
    0       4B    Magic          b"WIRL" (0x5749524C)
    4       1B    Version        0x01
    5       1B    Frame Type     FrameType enum (DATA=1, ACK=2, STREAM=3, PING=4)
    6       2B    Flags          Bitmask (0x01=LDPC coded, 0x02=Source coded, 0x04=Arithmetic, 0x08=LZW)
    8       4B    Sequence No    Monotonically increasing uint32
    12      4B    Orig Size      Original uncompressed payload size in bytes
    16      4B    Src Size       Source-coded payload size in bytes
    20      4B    Payload Len    Length of payload bytes immediately following header
    24      4B    CRC32          CRC32 checksum of the payload bytes (IEEE 802.3 standard)
    28      1B    Status Code    StatusCode enum (OK=0, CHECKSUM_ERR=1, DECODE_ERR=2)
    29      7B    Reserved       Zero-padded reserved bytes for future extensions
    Total Header = 36 bytes.
    """

    MAGIC = b"WIRL"
    VERSION = 1
    HEADER_FORMAT = ">4sBBHIIIIIB7s"
    HEADER_SIZE = 36

    FLAG_LDPC_CODED = 0x0001
    FLAG_SOURCE_CODED = 0x0002
    FLAG_ARITHMETIC = 0x0004
    FLAG_LZW = 0x0008

    def __init__(
        self,
        frame_type: Union[FrameType, int] = FrameType.DATA,
        seq_num: int = 1,
        payload: bytes = b"",
        orig_size: int = 0,
        src_size: int = 0,
        flags: int = 0,
        status: Union[StatusCode, int] = StatusCode.OK,
        timestamp: Optional[float] = None
    ):
        self.frame_type = FrameType(frame_type)
        self.seq_num = int(seq_num)
        self.payload = bytes(payload)
        self.orig_size = int(orig_size) if orig_size > 0 else len(self.payload)
        self.src_size = int(src_size) if src_size > 0 else len(self.payload)
        self.flags = int(flags)
        self.status = StatusCode(status)
        self.timestamp = timestamp if timestamp is not None else time.time()
        self.crc32 = binascii.crc32(self.payload) & 0xFFFFFFFF

    def serialize(self) -> bytes:
        """
        Serialize this frame into wire-format bytes (Header + Payload).
        """
        payload_len = len(self.payload)
        header = struct.pack(
            self.HEADER_FORMAT,
            self.MAGIC,
            self.VERSION,
            int(self.frame_type),
            self.flags,
            self.seq_num,
            self.orig_size,
            self.src_size,
            payload_len,
            self.crc32,
            int(self.status),
            b"\x00" * 7
        )
        return header + self.payload

    @classmethod
    def deserialize(cls, data: bytes) -> Tuple["WirelessFrame", bytes]:
        """
        Parse a single WirelessFrame from raw byte buffer.
        Returns:
            (frame, remaining_bytes)
        Raises:
            InvalidFrameError: If header magic or version is invalid.
            ChecksumMismatchError: If payload CRC32 check fails.
        """
        if len(data) < cls.HEADER_SIZE:
            raise InvalidFrameError(f"Insufficient bytes for frame header: need {cls.HEADER_SIZE}, got {len(data)}")

        magic, version, ftype, flags, seq, orig_sz, src_sz, plen, crc, status, _ = struct.unpack_from(
            cls.HEADER_FORMAT, data, 0
        )

        if magic != cls.MAGIC:
            raise InvalidFrameError(f"Invalid frame magic: expected {cls.MAGIC!r}, got {magic!r}")

        if version != cls.VERSION:
            raise InvalidFrameError(f"Unsupported frame version: expected {cls.VERSION}, got {version}")

        total_frame_len = cls.HEADER_SIZE + plen
        if len(data) < total_frame_len:
            raise InvalidFrameError(f"Incomplete frame payload: expected {plen} bytes, buffer has {len(data) - cls.HEADER_SIZE}")

        payload = data[cls.HEADER_SIZE : total_frame_len]
        remaining = data[total_frame_len:]

        # Verify integrity
        computed_crc = binascii.crc32(payload) & 0xFFFFFFFF
        if computed_crc != crc:
            raise ChecksumMismatchError(
                f"CRC32 mismatch on sequence #{seq}: header has 0x{crc:08X}, payload computed 0x{computed_crc:08X}"
            )

        frame = cls(
            frame_type=FrameType(ftype),
            seq_num=seq,
            payload=payload,
            orig_size=orig_sz,
            src_size=src_sz,
            flags=flags,
            status=StatusCode(status)
        )
        return frame, remaining

    @classmethod
    def create_ack(cls, seq_num: int, status: StatusCode = StatusCode.OK) -> "WirelessFrame":
        """
        Create a lightweight acknowledgment frame.
        """
        return cls(
            frame_type=FrameType.ACK,
            seq_num=seq_num,
            payload=b"",
            orig_size=0,
            src_size=0,
            flags=0,
            status=status
        )

    @classmethod
    def read_from_socket(cls, sock: socket.socket, timeout: Optional[float] = None) -> "WirelessFrame":
        """
        Read exactly one complete frame from a stream socket, handling partial TCP chunks.
        """
        if timeout is not None:
            sock.settimeout(timeout)

        # 1. Read header (exactly 36 bytes)
        header_bytes = bytearray()
        while len(header_bytes) < cls.HEADER_SIZE:
            chunk = sock.recv(cls.HEADER_SIZE - len(header_bytes))
            if not chunk:
                raise ConnectionResetError("Connection closed while receiving frame header.")
            header_bytes.extend(chunk)

        # 2. Parse header to determine payload length
        magic, version, ftype, flags, seq, orig_sz, src_sz, plen, crc, status, _ = struct.unpack_from(
            cls.HEADER_FORMAT, header_bytes, 0
        )

        if magic != cls.MAGIC:
            raise InvalidFrameError(f"Invalid frame magic received: {magic!r}")

        # 3. Read payload (exactly plen bytes)
        payload_bytes = bytearray()
        while len(payload_bytes) < plen:
            chunk = sock.recv(plen - len(payload_bytes))
            if not chunk:
                raise ConnectionResetError("Connection closed while receiving frame payload.")
            payload_bytes.extend(chunk)

        # 4. Verify checksum
        payload = bytes(payload_bytes)
        computed_crc = binascii.crc32(payload) & 0xFFFFFFFF
        if computed_crc != crc:
            raise ChecksumMismatchError(
                f"CRC32 mismatch on received sequence #{seq}: header=0x{crc:08X}, payload=0x{computed_crc:08X}"
            )

        return cls(
            frame_type=FrameType(ftype),
            seq_num=seq,
            payload=payload,
            orig_size=orig_sz,
            src_size=src_sz,
            flags=flags,
            status=StatusCode(status)
        )

    def send_to_socket(self, sock: socket.socket) -> None:
        """
        Send complete frame over a stream socket using sendall.
        """
        sock.sendall(self.serialize())
