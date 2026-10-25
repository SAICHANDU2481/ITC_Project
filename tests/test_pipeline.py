"""
Unit tests for end-to-end CommunicationPipeline and PerformanceEvaluator.
"""

import pytest
import numpy as np
from src.simulation import CommunicationPipeline
from src.channel_coding import LDPCCodec, PolarCodec, HammingCodec
from src.metrics import PerformanceEvaluator


def test_pipeline_lossless_recovery():
    codec = LDPCCodec(n=64, k=32, seed=42)
    pipeline = CommunicationPipeline(channel_codec=codec, use_source_coding=True, seed=42)
    sample_text = "VIT_AP_23BCE7551_LOSSLESS_WIRED_CHANNEL_VERIFICATION_TEST"

    result = pipeline.run_single_transmission(sample_text, channel_mode="lossless")
    assert result['exact_recovery'] is True
    assert result['post_fec_errors'] == 0
    assert result['post_fec_ber'] == 0.0


def test_pipeline_noisy_awgn_recovery():
    # At high Eb/N0 (8 dB), LDPC should recover payload with zero errors
    codec = LDPCCodec(n=64, k=32, seed=42)
    pipeline = CommunicationPipeline(channel_codec=codec, use_source_coding=True, seed=42)
    sample_text = "NODE_23BCE7551_PACKET_HIGH_SNR_RELIABILITY_TEST"

    result = pipeline.run_single_transmission(sample_text, channel_mode="awgn", channel_param=8.0)
    assert result['post_fec_errors'] == 0
    assert result['exact_recovery'] is True


def test_metrics_ber_calculator():
    tx = np.array([0, 1, 0, 1, 1, 0, 0, 1], dtype=np.uint8)
    rx = np.array([0, 1, 1, 1, 1, 0, 0, 0], dtype=np.uint8)  # 2 errors at idx 2 and 7
    res = PerformanceEvaluator.calculate_ber(tx, rx)

    assert res['total_bits'] == 8
    assert res['bit_errors'] == 2
    assert res['ber'] == 0.25
    assert res['zero_error_observed'] is False


def test_metrics_coding_rate():
    res = PerformanceEvaluator.calculate_coding_metrics(n=64, k=32)
    assert res['code_rate'] == 0.5
    assert res['parity_bits'] == 32
    assert res['redundancy_overhead_pct'] == 100.0


def test_pipeline_binary_array_lossless_exact_recovery():
    # Regression test: verifies that binary arrays produce exact_recovery=True in lossless channel
    codec = LDPCCodec(n=64, k=32, seed=42)
    pipeline = CommunicationPipeline(channel_codec=codec, use_source_coding=True, seed=42)
    binary_input = np.random.default_rng(42).integers(0, 2, size=256, dtype=np.uint8)

    result = pipeline.run_single_transmission(binary_input, channel_mode="lossless")
    assert result['exact_recovery'] is True
    assert result['post_fec_errors'] == 0
    assert result['post_fec_ber'] == 0.0


def test_pipeline_arbitrary_binary_length_roundtrip():
    # Non-multiple of 8 length bitstream (e.g. 75 bits) with source coding and FEC
    codec = LDPCCodec(n=64, k=32, seed=42)
    pipeline = CommunicationPipeline(channel_codec=codec, use_source_coding=True, seed=42)
    raw_bits = np.random.default_rng(123).integers(0, 2, size=75, dtype=np.uint8)

    result = pipeline.run_single_transmission(raw_bits, channel_mode="lossless")
    assert result['exact_recovery'] is True
    assert result['post_fec_errors'] == 0


def test_pipeline_polar_codec_recovery():
    codec = PolarCodec(n=64, k=32, design_snr_db=3.0)
    pipeline = CommunicationPipeline(channel_codec=codec, use_source_coding=True, seed=42)
    text = "POLAR_CODE_END_TO_END_VERIFICATION_23BCE7551"

    result = pipeline.run_single_transmission(text, channel_mode="lossless")
    assert result['exact_recovery'] is True
    assert result['post_fec_errors'] == 0


def test_pipeline_hamming_codec_recovery():
    codec = HammingCodec()
    pipeline = CommunicationPipeline(channel_codec=codec, use_source_coding=True, seed=42)
    text = "HAMMING_7_4_END_TO_END_PIPELINE_TEST"

    result = pipeline.run_single_transmission(text, channel_mode="lossless")
    assert result['exact_recovery'] is True
    assert result['post_fec_errors'] == 0


def test_metrics_length_mismatch_detection():
    # When lengths differ, exact_match must be False and length_mismatch True
    tx = np.array([0, 1, 0, 1], dtype=np.uint8)
    rx = np.array([0, 1, 0, 1, 0, 0], dtype=np.uint8)
    res = PerformanceEvaluator.calculate_ber(tx, rx)

    assert res['length_mismatch'] is True
    assert res['exact_match'] is False

