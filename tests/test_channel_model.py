"""
Unit tests for WiredChannel and ChannelAnalyzer.
"""

import pytest
import numpy as np
from src.channel_model import WiredChannel, ChannelAnalyzer


def test_lossless_channel_exactness():
    channel = WiredChannel(seed=42)
    bits = np.array([1, 0, 1, 1, 0, 0, 1, 0, 1, 1], dtype=np.uint8)
    rx_bits, llrs = channel.transmit_lossless(bits)

    assert np.array_equal(rx_bits, bits)
    assert np.all(llrs[bits == 0] > 0)
    assert np.all(llrs[bits == 1] < 0)


def test_bsc_empirical_flip_rate():
    channel = WiredChannel(seed=42)
    n_bits = 20000
    bits = np.zeros(n_bits, dtype=np.uint8)
    target_p = 0.05
    rx_bits, _ = channel.transmit_bsc(bits, p=target_p)

    empirical_p = np.mean(rx_bits)
    # Check within 3 standard errors of binomial distribution
    std_err = np.sqrt(target_p * (1 - target_p) / n_bits)
    assert abs(empirical_p - target_p) < 3.5 * std_err


def test_awgn_theoretical_ber_formula():
    # At Eb/N0 = 0 dB, theoretical BPSK BER is Q(sqrt(2)) = 0.5 * erfc(1) ~ 0.07865
    ber_0db = WiredChannel.theoretical_uncoded_ber_awgn(0.0)
    assert abs(ber_0db - 0.07865) < 1e-4

    # High SNR should be very small
    ber_10db = WiredChannel.theoretical_uncoded_ber_awgn(10.0)
    assert ber_10db < 1e-5


def test_channel_analyzer_capacity():
    # Lossless BSC (p = 0) has capacity 1 bit/channel use
    cap_0 = ChannelAnalyzer.bsc_capacity(0.0)
    assert cap_0 == 1.0

    # Completely noisy BSC (p = 0.5) has capacity 0
    cap_half = ChannelAnalyzer.bsc_capacity(0.5)
    assert cap_half == 0.0

    # AWGN capacity is strictly increasing with SNR
    cap_snr0 = ChannelAnalyzer.shannon_awgn_capacity(0.0)
    cap_snr10 = ChannelAnalyzer.shannon_awgn_capacity(10.0)
    assert cap_snr10 > cap_snr0


def test_bsc_multi_probabilities_and_seeds():
    # Phase 5B required test: p = 0, 0.001, 0.01, 0.05, 0.10 with reproducible seeds
    p_values = [0.0, 0.001, 0.01, 0.05, 0.10]
    n_bits = 50000
    for seed in [101, 202]:
        ch = WiredChannel(seed=seed)
        bits = np.zeros(n_bits, dtype=np.uint8)
        for p in p_values:
            rx, llrs = ch.transmit_bsc(bits, p=p)
            emp_p = float(np.mean(rx))
            if p == 0.0:
                assert emp_p == 0.0
            else:
                std_err = np.sqrt(p * (1.0 - p) / n_bits)
                z = abs(emp_p - p) / std_err
                assert z < 3.5, f"Observed p={emp_p} deviated from target p={p} (z={z})"


def test_awgn_noise_variance_and_code_rate_scaling():
    # Phase 5C: test noise variance calculation and code-rate scaling
    ch = WiredChannel(seed=777)
    test_bits = np.zeros(100, dtype=np.uint8)
    snr = 4.0

    # Uncoded: R = 1.0
    _, _, _, sigma_r1 = ch.transmit_awgn(test_bits, eb_no_db=snr, code_rate=1.0)
    expected_sigma_r1 = 1.0 / np.sqrt(2.0 * (10.0 ** (snr / 10.0)))
    assert abs(sigma_r1 - expected_sigma_r1) < 1e-6

    # Coded: R = 0.5 (Rate-1/2 LDPC/Polar)
    _, _, _, sigma_rhalf = ch.transmit_awgn(test_bits, eb_no_db=snr, code_rate=0.5)
    # sigma_coded = sigma_uncoded / sqrt(R) = sigma_uncoded * sqrt(2)
    assert abs(sigma_rhalf - (expected_sigma_r1 * np.sqrt(2.0))) < 1e-6


def test_awgn_empirical_vs_theoretical_bpsk_ber():
    # Compare simulated BPSK BER with theoretical formula
    ch = WiredChannel(seed=888)
    n_bits = 80000
    bits = ch.rng.integers(0, 2, size=n_bits, dtype=np.uint8)

    for snr in [0.0, 3.0, 6.0]:
        rx_hard, _, _, _ = ch.transmit_awgn(bits, eb_no_db=snr, code_rate=1.0)
        sim_ber = float(np.mean(rx_hard != bits))
        th_ber = WiredChannel.theoretical_uncoded_ber_awgn(snr)
        std_err = np.sqrt(th_ber * (1.0 - th_ber) / n_bits)
        z = abs(sim_ber - th_ber) / std_err
        assert z < 3.5, f"Simulated BER={sim_ber} diverged from theory={th_ber} at {snr} dB (z={z})"

