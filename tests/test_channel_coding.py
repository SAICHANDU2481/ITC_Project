"""
Unit tests for Channel Codecs: LDPC, Polar, and Hamming.
"""

import pytest
import numpy as np
from src.channel_coding import LDPCCodec, PolarCodec, HammingCodec


def test_ldpc_matrix_orthogonality():
    codec = LDPCCodec(n=64, k=32, seed=42)
    # Check G @ H^T = 0 mod 2
    syndrome = np.mod(codec.G @ codec.H.T, 2)
    assert np.all(syndrome == 0)


def test_ldpc_noiseless_recovery():
    codec = LDPCCodec(n=64, k=32, seed=42)
    msg = np.random.randint(0, 2, size=32, dtype=np.uint8)
    cw = codec.encode_block(msg)
    assert len(cw) == 64

    # High SNR noiseless observation (0 -> +10, 1 -> -10)
    y_noiseless = (1.0 - 2.0 * cw.astype(np.float64)) * 10.0
    decoded = codec.decode_block(y_noiseless, channel_type="awgn", sigma=0.1)
    assert np.array_equal(decoded, msg)


def test_ldpc_error_correction():
    codec = LDPCCodec(n=64, k=32, max_iter=25, seed=42)
    msg = np.array([1, 0, 1, 1, 0, 0, 1, 0] * 4, dtype=np.uint8)
    cw = codec.encode_block(msg)

    # Inject 2 bit errors into the codeword
    corrupted_cw = cw.copy()
    corrupted_cw[2] ^= 1
    corrupted_cw[15] ^= 1

    # Decode via BSC mode
    decoded = codec.decode_block(corrupted_cw, channel_type="bsc", p=0.04)
    assert np.array_equal(decoded, msg)


def test_polar_noiseless_recovery():
    polar = PolarCodec(n=64, k=32, design_snr_db=3.0)
    msg = np.random.randint(0, 2, size=32, dtype=np.uint8)
    cw = polar.encode_block(msg)
    assert len(cw) == 64

    y_noiseless = (1.0 - 2.0 * cw.astype(np.float64)) * 10.0
    decoded = polar.decode_block(y_noiseless, channel_type="awgn", sigma=0.1)
    assert np.array_equal(decoded, msg)


def test_hamming_single_error_correction():
    hamming = HammingCodec()
    msg = np.array([1, 0, 1, 1], dtype=np.uint8)
    cw = hamming.encode_block(msg)
    assert len(cw) == 7

    # Flip 1 bit (position 3)
    corrupted = cw.copy()
    corrupted[3] ^= 1

    decoded = hamming.decode_block(corrupted, channel_type="bsc")
    assert np.array_equal(decoded, msg)


def test_codec_arbitrary_length_segmentation():
    codec = LDPCCodec(n=64, k=32, seed=42)
    # Stream length that is not a multiple of k=32
    raw_stream = np.random.randint(0, 2, size=75, dtype=np.uint8)
    encoded, pad_len = codec.encode(raw_stream)

    assert pad_len == (32 - (75 % 32))
    assert len(encoded) == (len(raw_stream) + pad_len) * 2

    # High SNR channel
    y = (1.0 - 2.0 * encoded.astype(np.float64)) * 10.0
    decoded = codec.decode(y, pad_len=pad_len, channel_type="awgn", sigma=0.1)
    assert np.array_equal(decoded, raw_stream)


def test_hamming_all_single_bit_error_positions():
    hamming = HammingCodec()
    # Test all 16 possible 4-bit messages across all 7 error bit positions
    for val in range(16):
        msg = np.array([(val >> (3 - b)) & 1 for b in range(4)], dtype=np.uint8)
        cw = hamming.encode_block(msg)
        assert len(cw) == 7
        assert np.array_equal(cw[:4], msg)

        # Noiseless test
        assert np.array_equal(hamming.decode_block(cw, channel_type="bsc"), msg)

        # Single error at all 7 positions
        for err_pos in range(7):
            corrupted = cw.copy()
            corrupted[err_pos] ^= 1
            dec = hamming.decode_block(corrupted, channel_type="bsc")
            assert np.array_equal(dec, msg), f"Hamming failed to correct error at pos {err_pos} for msg {msg}"


def test_hamming_double_bit_errors():
    # Hamming(7,4) has minimum Hamming distance d_min = 3.
    # Therefore, 2-bit errors exceed its t=1 error-correction capability.
    hamming = HammingCodec()
    msg = np.array([1, 0, 1, 0], dtype=np.uint8)
    cw = hamming.encode_block(msg)

    miscorrections = 0
    for p1 in range(7):
        for p2 in range(p1 + 1, 7):
            corrupted = cw.copy()
            corrupted[p1] ^= 1
            corrupted[p2] ^= 1
            dec = hamming.decode_block(corrupted, channel_type="bsc")
            if not np.array_equal(dec, msg):
                miscorrections += 1
    # Confirms that double errors are not corrected
    assert miscorrections > 0


def test_hamming_unsupported_lengths():
    hamming = HammingCodec()
    with pytest.raises(ValueError, match="Hamming.*requires 4 message bits"):
        hamming.encode_block(np.array([1, 0, 1], dtype=np.uint8))

    with pytest.raises(ValueError, match="Received block length must be 7"):
        hamming.decode_block(np.array([1, 0, 1, 1, 0, 0], dtype=np.uint8))


def test_ldpc_lossless_hard_bits_recovery():
    # Regression test: verifies that binary {0, 1} inputs are decoded accurately in lossless mode
    codec = LDPCCodec(n=64, k=32, seed=42)
    msg = np.array([1, 1, 0, 0, 1, 0, 1, 0] * 4, dtype=np.uint8)
    cw = codec.encode_block(msg)

    # Decode hard bits directly with channel_type='lossless'
    dec = codec.decode_block(cw, channel_type="lossless")
    assert np.array_equal(dec, msg)


def test_ldpc_min_sum_decoding():
    codec = LDPCCodec(n=64, k=32, max_iter=25, algorithm="min_sum", seed=42)
    msg = np.array([0, 1, 1, 0, 1, 0, 0, 1] * 4, dtype=np.uint8)
    cw = codec.encode_block(msg)

    corrupted = cw.copy()
    corrupted[1] ^= 1
    corrupted[20] ^= 1

    dec = codec.decode_block(corrupted, channel_type="bsc", p=0.03)
    assert np.array_equal(dec, msg)


def test_ldpc_unsupported_lengths():
    codec = LDPCCodec(n=64, k=32, seed=42)
    with pytest.raises(ValueError, match="Message block length must be exactly 32"):
        codec.encode_block(np.zeros(20, dtype=np.uint8))

    with pytest.raises(ValueError, match="Received block length must be 64"):
        codec.decode_block(np.zeros(50, dtype=np.float64))


def test_polar_lossless_hard_bits_recovery():
    # Regression test: verifies Polar decoding of hard bits under lossless mode
    polar = PolarCodec(n=64, k=32, design_snr_db=3.0)
    msg = np.array([1, 0, 0, 1, 0, 1, 1, 0] * 4, dtype=np.uint8)
    cw = polar.encode_block(msg)

    dec = polar.decode_block(cw, channel_type="lossless")
    assert np.array_equal(dec, msg)


def test_polar_unsupported_lengths():
    polar = PolarCodec(n=64, k=32, design_snr_db=3.0)
    with pytest.raises(ValueError, match="Polar message length must be 32"):
        polar.encode_block(np.zeros(16, dtype=np.uint8))

    with pytest.raises(ValueError, match="Received block length must be 64"):
        polar.decode_block(np.zeros(32, dtype=np.float64))


def test_channel_codec_stream_decode_length_validation():
    codec = LDPCCodec(n=64, k=32, seed=42)
    # Stream length that is not a multiple of n=64
    invalid_stream = np.zeros(70, dtype=np.float64)
    with pytest.raises(ValueError, match="must be a multiple of codeword length n"):
        codec.decode(invalid_stream)

    # Invalid pad_len
    valid_stream = np.zeros(128, dtype=np.float64)
    with pytest.raises(ValueError, match="Padding length pad_len"):
        codec.decode(valid_stream, pad_len=32)  # pad_len must be < k=32

