"""
Unit tests for Saturated Source, Binary Converter, and LZW Source Codec.
"""

import pytest
import numpy as np
from src.source_coding import SaturatedSource, BinaryConverter, LZWCodec


def test_saturated_source_generation():
    source = SaturatedSource(seed=42)
    text = source.generate_text_stream(num_packets=5)
    assert len(text) > 50
    assert "23BCE7551" in text

    # Test Markov stream
    m_bits = source.generate_markov_bits(num_bits=1000, p01=0.2, p10=0.3)
    assert len(m_bits) == 1000
    assert set(np.unique(m_bits)).issubset({0, 1})

    # Test entropy
    h_text = source.compute_empirical_entropy(text)
    assert h_text > 0.0


def test_binary_converter_text_roundtrip():
    text = "TEST_TELEMETRY_PAYLOAD_23BCE7551_VITAP!"
    bits = BinaryConverter.text_to_bits(text)
    assert len(bits) == len(text.encode('utf-8')) * 8
    assert set(np.unique(bits)).issubset({0, 1})

    recovered = BinaryConverter.bits_to_text(bits)
    assert recovered == text


def test_binary_converter_ints_roundtrip():
    original_ints = [15, 255, 1024, 4095, 0, 77]
    bit_depth = 12
    bits = BinaryConverter.ints_to_bits(original_ints, bit_depth=bit_depth)
    assert len(bits) == len(original_ints) * bit_depth

    recovered_ints = BinaryConverter.bits_to_ints(bits, bit_depth=bit_depth)
    assert recovered_ints == original_ints


def test_lzw_roundtrip_text():
    codec = LZWCodec(bit_depth=12)
    sample_text = "TOBEORNOTTOBEORTOBEORNOT_VITAP_23BCE7551_SATURATED_DATA_STREAM"
    comp_bits, stats = codec.encode(sample_text)

    assert len(comp_bits) > 0
    assert stats['compressed_bits'] == len(comp_bits)

    recovered = codec.decode(comp_bits, return_as_string=True)
    assert recovered == sample_text


def test_lzw_edge_case_cScSc():
    # String pattern that triggers the classic LZW cScSc edge case
    codec = LZWCodec(bit_depth=12)
    text = "ABABABA"
    comp_bits, _ = codec.encode(text)
    recovered = codec.decode(comp_bits, return_as_string=True)
    assert recovered == text


def test_lzw_binary_bytes_roundtrip():
    codec = LZWCodec(bit_depth=12)
    data_bytes = bytes([0, 1, 2, 0, 1, 2, 0, 1, 2, 55, 99, 128, 255])
    comp_bits, _ = codec.encode(data_bytes)
    recovered_bytes = codec.decode(comp_bits, return_as_string=False)
    assert recovered_bytes == data_bytes


def test_lzw_empty_input():
    codec = LZWCodec(bit_depth=12)
    # Empty string
    bits, stats = codec.encode("")
    assert len(bits) == 0
    assert stats['compressed_bits'] == 0
    recovered = codec.decode(bits, return_as_string=True)
    assert recovered == ""

    # Empty bytes
    bits_b, stats_b = codec.encode(b"")
    assert len(bits_b) == 0
    recovered_b = codec.decode(bits_b, return_as_string=False)
    assert recovered_b == b""


def test_lzw_single_character():
    codec = LZWCodec(bit_depth=12)
    s = "Z"
    bits, stats = codec.encode(s)
    # 1 code of 12 bits
    assert len(bits) == 12
    # Single 8-bit char expanded to 12 bits -> CR < 1.0
    assert stats['compression_ratio'] < 1.0
    recovered = codec.decode(bits, return_as_string=True)
    assert recovered == s


def test_lzw_repeated_characters_high_compression():
    codec = LZWCodec(bit_depth=12)
    text = "A" * 1000  # 1000 bytes = 8000 raw bits
    bits, stats = codec.encode(text)
    recovered = codec.decode(bits, return_as_string=True)
    assert recovered == text
    # High compression ratio (> 10x) and positive space savings (> 90%)
    assert stats['compression_ratio'] > 10.0
    assert stats['space_saving_pct'] > 90.0


def test_lzw_all_256_possible_byte_values():
    codec = LZWCodec(bit_depth=12)
    all_bytes = bytes(range(256))
    bits, stats = codec.encode(all_bytes)
    recovered = codec.decode(bits, return_as_string=False)
    assert recovered == all_bytes
    # No repeated substrings: expands data by 12/8 = 1.5x, CR = 0.667
    assert stats['compression_ratio'] < 1.0


def test_lzw_dictionary_growth_and_freeze():
    # Test with bit_depth=9 (max_table_size = 512 entries)
    codec = LZWCodec(bit_depth=9)
    # 5000 characters of repeating alphabet to easily fill 512 entries
    data = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789" * 150
    bits, stats = codec.encode(data)
    # Dictionary reaches exactly 512 entries and freezes
    assert stats['dictionary_entries_used'] == 512
    recovered = codec.decode(bits, return_as_string=True)
    assert recovered == data


def test_lzw_incompressible_random_data_expansion():
    # Demonstrates Shannon source coding limit: uniform random data cannot be compressed
    codec = LZWCodec(bit_depth=12)
    rng = np.random.default_rng(2026)
    random_bytes = bytes(rng.integers(0, 256, size=1500, dtype=np.uint8))
    bits, stats = codec.encode(random_bytes)
    recovered = codec.decode(bits, return_as_string=False)
    assert recovered == random_bytes
    # Must report expansion (CR < 1.0, negative space savings)
    assert stats['compression_ratio'] < 1.0
    assert stats['space_saving_pct'] < 0.0

