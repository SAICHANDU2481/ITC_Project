"""
Unit tests for Arithmetic / Range Source Codec.
Tests exact round-trip reconstruction, Unicode, binary bytes, empty inputs,
compression metrics, and malformed stream error detection.
"""

import pytest
import numpy as np
from src.source_coding.arithmetic_codec import ArithmeticCodec


def test_arithmetic_roundtrip_english_text():
    codec = ArithmeticCodec()
    text = "Hello, this is my wireless ITC project! Testing Arithmetic Coding transmission."
    compressed, stats = codec.encode(text)
    assert len(compressed) > 0
    assert stats['raw_bytes'] == len(text.encode('utf-8'))
    assert 'compression_ratio' in stats

    recovered = codec.decode(compressed, return_as_string=True)
    assert recovered == text


def test_arithmetic_unicode_and_special_chars():
    codec = ArithmeticCodec()
    text = "Wireless Telemetry 📡🛰️ — SNR: 12.5 dB, BER: 1.0e-5, Greek: α β γ δ Ω, Hindi: नमस्ते, 日本語: 無線通信"
    compressed, stats = codec.encode(text)
    recovered = codec.decode(compressed, return_as_string=True)
    assert recovered == text


def test_arithmetic_empty_input():
    codec = ArithmeticCodec()
    compressed, stats = codec.encode("")
    assert stats['raw_bytes'] == 0
    recovered_str = codec.decode(compressed, return_as_string=True)
    assert recovered_str == ""

    compressed_b, stats_b = codec.encode(b"")
    recovered_bytes = codec.decode(compressed_b, return_as_string=False)
    assert recovered_bytes == b""


def test_arithmetic_repeated_pattern_compression():
    codec = ArithmeticCodec()
    text = "FRAME_HEADER_SYNC_0123456789" * 40  # 1120 bytes
    compressed, stats = codec.encode(text)
    assert stats['compression_ratio'] > 1.2  # Should achieve strong compression
    recovered = codec.decode(compressed, return_as_string=True)
    assert recovered == text


def test_arithmetic_arbitrary_binary_bytes():
    codec = ArithmeticCodec()
    rng = np.random.default_rng(42)
    raw_bytes = rng.integers(0, 256, size=500, dtype=np.uint8).tobytes()
    compressed, stats = codec.encode(raw_bytes)
    recovered = codec.decode(compressed, return_as_string=False)
    assert recovered == raw_bytes


def test_arithmetic_malformed_stream_detection():
    codec = ArithmeticCodec()
    
    # 1. Too short stream
    with pytest.raises(ValueError, match="header too short"):
        codec.decode(b"SHORT")

    # 2. Bad magic header
    with pytest.raises(ValueError, match="Invalid arithmetic stream magic"):
        codec.decode(b"BADM" + b"\x00" * 20)

    # 3. Truncated bitmap or table
    with pytest.raises(ValueError, match="truncated presence bitmap|truncated frequency table"):
        codec.decode(b"ARTH" + (100).to_bytes(4, 'big') + (50).to_bytes(4, 'big') + b"\x00" * 10)

    # 4. Truncated frequency table with active symbol in bitmap
    bad_bitmap = bytearray(32)
    bad_bitmap[0] = 0x01  # symbol 0 is active, expects 2 bytes of frequency
    with pytest.raises(ValueError, match="truncated frequency table"):
        codec.decode(b"ARTH" + (100).to_bytes(4, 'big') + (50).to_bytes(4, 'big') + bytes(bad_bitmap) + b"\x00")


def test_arithmetic_metadata_metrics():
    codec = ArithmeticCodec()
    text = "Sample payload for entropy and metadata measurement."
    compressed, stats = codec.encode(text)
    assert stats['entropy_bits_per_symbol'] > 0
    # Header (12B) + Bitmap (32B) + Active Symbol Frequencies (2B * N)
    assert stats['metadata_overhead_bytes'] >= 12 + 32
    assert stats['encoding_duration_ms'] >= 0.0
