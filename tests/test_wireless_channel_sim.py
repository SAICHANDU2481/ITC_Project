"""
Unit tests for Wireless Physical Layer Simulation (Mode C).
Tests BPSK modulation, AWGN channel transmission, LDPC error correction,
uncoded baseline comparison, and SNR sweeps.
"""

import pytest
import numpy as np
from src.wireless.channel_sim import WirelessPhysicalChannel, WirelessSimulationPipeline


def test_bpsk_modulation():
    bits = np.array([0, 1, 0, 0, 1], dtype=np.uint8)
    symbols = WirelessPhysicalChannel.modulate_bpsk(bits)
    expected = np.array([1.0, -1.0, 1.0, 1.0, -1.0])
    assert np.allclose(symbols, expected)


def test_theoretical_bpsk_ber():
    # At 0 dB: P_b = 0.5 * erfc(1) ≈ 0.0786
    ber_0 = WirelessPhysicalChannel.theoretical_bpsk_ber(0.0)
    assert 0.078 < ber_0 < 0.079

    # At 10 dB: P_b ≈ 3.87e-6
    ber_10 = WirelessPhysicalChannel.theoretical_bpsk_ber(10.0)
    assert 1e-6 < ber_10 < 1e-5


def test_wireless_pipeline_high_snr_exact_recovery():
    pipeline = WirelessSimulationPipeline(seed=42)
    message = "WIRELESS_SIMULATION_HIGH_SNR_NODE_TEST"

    # At 8.0 dB, LDPC should achieve 0 post-FEC errors and exact recovery
    res = pipeline.run_simulation(
        message=message,
        eb_no_db=8.0,
        source_codec="arithmetic",
        ldpc_max_iter=25
    )

    assert res['exact_recovery'] is True
    assert res['post_fec_errors'] == 0
    assert res['reconstructed_text'] == message
    assert res['compression_ratio'] > 0


def test_wireless_pipeline_low_snr_error_suppression():
    pipeline = WirelessSimulationPipeline(seed=42)
    message = "TELEMETRY_LOG_CHANNEL_CODING_EXPERIMENT_DATA_STREAM"

    res = pipeline.run_simulation(
        message=message,
        eb_no_db=4.0,
        source_codec="arithmetic",
        ldpc_max_iter=25
    )

    # Pre-FEC should have errors at 4 dB
    assert res['pre_fec_errors'] > 0
    # Error suppression gain should reduce errors significantly
    assert res['error_suppression_gain'] > 1.0


def test_wireless_snr_sweep():
    pipeline = WirelessSimulationPipeline(seed=42)
    sweep_records = pipeline.run_snr_sweep(
        eb_no_list=[2.0, 6.0],
        bits_per_point=2560,
        trials_per_point=2
    )

    assert len(sweep_records) == 2
    for r in sweep_records:
        assert 'eb_no_db' in r
        assert 'pre_fec_ber' in r
        assert 'ldpc_post_fec_ber' in r
        assert 'uncoded_ber' in r
        assert 'frame_error_rate' in r
        assert r['total_info_bits'] > 0
