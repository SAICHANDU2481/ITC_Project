"""
Channel Analyzer and Shannon Capacity Diagnostics.
Computes theoretical capacity limits, channel entropy, and error distributions.
"""

from typing import Dict, Any
import numpy as np


class ChannelAnalyzer:
    """
    Computes theoretical capacity boundaries and channel metrics.
    """

    @staticmethod
    def shannon_awgn_capacity(snr_db: float, bandwidth_hz: float = 1.0) -> float:
        """
        Compute continuous Shannon capacity C = B * log2(1 + SNR) in bits/s.
        """
        snr_linear = 10.0 ** (snr_db / 10.0)
        return float(bandwidth_hz * np.log2(1.0 + snr_linear))

    @staticmethod
    def bsc_capacity(p: float) -> float:
        """
        Compute discrete Binary Symmetric Channel capacity:
        C = 1 - H_b(p) where H_b(p) is the binary entropy function.
        """
        if p <= 0.0 or p >= 1.0:
            return 1.0 if p <= 0.0 else 0.0
        if p >= 0.5:
            return 0.0
        hb = - (p * np.log2(p) + (1.0 - p) * np.log2(1.0 - p))
        return float(1.0 - hb)

    @staticmethod
    def evaluate_error_pattern(transmitted: np.ndarray, received: np.ndarray) -> Dict[str, Any]:
        """
        Analyze bit-level error patterns between transmitted and received streams.
        """
        tx = np.asarray(transmitted, dtype=np.uint8).flatten()
        rx = np.asarray(received, dtype=np.uint8).flatten()
        min_len = min(len(tx), len(rx))
        tx = tx[:min_len]
        rx = rx[:min_len]

        errors = np.bitwise_xor(tx, rx)
        num_errors = int(np.sum(errors))
        ber = float(num_errors / min_len) if min_len > 0 else 0.0

        # Run-length of consecutive errors (burstiness check)
        runs = []
        curr_run = 0
        for e in errors:
            if e:
                curr_run += 1
            else:
                if curr_run > 0:
                    runs.append(curr_run)
                    curr_run = 0
        if curr_run > 0:
            runs.append(curr_run)

        max_burst = max(runs) if runs else 0

        return {
            'total_bits': min_len,
            'bit_errors': num_errors,
            'ber': ber,
            'exact_match': (num_errors == 0),
            'max_error_burst': max_burst,
            'num_error_events': len(runs)
        }
