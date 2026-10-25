"""
Performance Evaluation and Metrics Module.
Calculates Bit Error Rate (BER), Frame Error Rate (FER), Coding Gain,
Source Reconstruction Accuracy, and Compression Metrics.
"""

from typing import Dict, Any, List, Optional
import numpy as np


class PerformanceEvaluator:
    """
    Standardized digital communication and information theory metric evaluator.
    """

    @staticmethod
    def calculate_ber(transmitted_bits: np.ndarray, decoded_bits: np.ndarray) -> Dict[str, Any]:
        """
        Calculate Bit Error Rate (BER) and error counts.
        """
        tx = np.asarray(transmitted_bits, dtype=np.uint8).flatten()
        rx = np.asarray(decoded_bits, dtype=np.uint8).flatten()

        compare_len = min(len(tx), len(rx))
        if compare_len == 0:
            exact = (len(tx) == len(rx))
            return {
                'total_bits': 0,
                'bit_errors': 0,
                'ber': 0.0,
                'zero_error_observed': exact,
                'ber_upper_bound_95': 1.0 if not exact else 0.0,
                'exact_match': exact,
                'length_mismatch': (len(tx) != len(rx))
            }

        errors = np.bitwise_xor(tx[:compare_len], rx[:compare_len])
        num_errors = int(np.sum(errors))
        ber = float(num_errors / compare_len)

        # Statistical rule of three: if 0 errors in N bits, upper 95% confidence bound is 3/N
        upper_bound_95 = float(3.0 / compare_len) if num_errors == 0 else ber
        exact_match = (len(tx) == len(rx)) and (num_errors == 0)

        return {
            'total_bits': compare_len,
            'bit_errors': num_errors,
            'ber': ber,
            'zero_error_observed': (num_errors == 0),
            'ber_upper_bound_95': upper_bound_95,
            'exact_match': exact_match,
            'length_mismatch': (len(tx) != len(rx))
        }

    @staticmethod
    def calculate_fer(
        transmitted_blocks: List[np.ndarray],
        decoded_blocks: List[np.ndarray]
    ) -> Dict[str, Any]:
        """
        Calculate Frame Error Rate (FER) / Block Error Rate (BLER).
        """
        num_blocks = min(len(transmitted_blocks), len(decoded_blocks))
        if num_blocks == 0:
            return {'total_blocks': 0, 'frame_errors': 0, 'fer': 0.0}

        frame_errors = 0
        for i in range(num_blocks):
            if not np.array_equal(transmitted_blocks[i], decoded_blocks[i]):
                frame_errors += 1

        fer = float(frame_errors / num_blocks)
        return {
            'total_blocks': num_blocks,
            'frame_errors': frame_errors,
            'fer': fer
        }

    @staticmethod
    def calculate_reconstruction_accuracy(original_text: str, reconstructed_text: str) -> Dict[str, Any]:
        """
        Evaluate text-level fidelity and character error rate (CER).
        """
        exact_match = (original_text == reconstructed_text)
        orig_len = len(original_text)
        rec_len = len(reconstructed_text)

        if orig_len == 0:
            return {
                'exact_match': exact_match,
                'char_accuracy': 1.0 if rec_len == 0 else 0.0,
                'char_errors': rec_len,
                'original_chars': 0,
                'reconstructed_chars': rec_len
            }

        # Count character matches
        match_chars = sum(1 for c1, c2 in zip(original_text, reconstructed_text) if c1 == c2)
        mismatch_chars = max(orig_len, rec_len) - match_chars
        char_accuracy = float(match_chars / max(orig_len, rec_len))

        return {
            'exact_match': exact_match,
            'char_accuracy': char_accuracy,
            'char_errors': mismatch_chars,
            'original_chars': orig_len,
            'reconstructed_chars': rec_len
        }

    @staticmethod
    def calculate_coding_metrics(n: int, k: int) -> Dict[str, Any]:
        """
        Calculate coding rate, parity bits, and redundancy overhead.
        """
        rate = float(k) / float(n)
        redundancy_bits = n - k
        overhead_pct = (float(redundancy_bits) / float(k)) * 100.0

        return {
            'codeword_length_n': n,
            'message_length_k': k,
            'code_rate': rate,
            'parity_bits': redundancy_bits,
            'redundancy_overhead_pct': overhead_pct
        }
