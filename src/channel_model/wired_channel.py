"""
Wired Communication Channel Model.
Implements realistic physical models of wired transmission media:
1. Ideal Lossless baseline (as referenced in teacher's notes, p = 0).
2. Electrical Additive White Gaussian Noise (AWGN) channel with BPSK modulation.
3. Parametric Binary Symmetric Channel (BSC) with bit-flip probability p.
"""

from typing import Tuple, Optional, Union
import numpy as np
import math


class WiredChannel:
    """
    Simulation of wired communication channels including physical thermal noise
    and discrete bit-flip perturbations.
    """

    def __init__(self, mode: str = "awgn", seed: Optional[int] = 42):
        """
        Args:
            mode: 'lossless', 'awgn', or 'bsc'
            seed: Configurable random seed for reproducibility.
        """
        self.mode = mode.lower()
        self.seed = seed
        self.rng = np.random.default_rng(seed)

    def reset_seed(self, seed: Optional[int] = None) -> None:
        """Reset RNG seed."""
        if seed is not None:
            self.seed = seed
        self.rng = np.random.default_rng(self.seed)

    def transmit_lossless(self, bits: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Transmit bits through an ideal lossless wired link.
        Outputs pristine bits with zero errors (BER = 0).
        """
        bits = np.asarray(bits, dtype=np.uint8).flatten()
        # High-confidence LLRs for soft decoders
        llrs = np.where(bits == 0, 50.0, -50.0)
        return bits.copy(), llrs

    def transmit_bsc(self, bits: np.ndarray, p: float = 0.0) -> Tuple[np.ndarray, np.ndarray]:
        """
        Transmit bits through a Binary Symmetric Channel (BSC) with bit-flip probability p.
        Returns:
            received_bits: np.ndarray of uint8 bits after potential flips.
            llrs: Channel log-likelihood ratios L_i = ln((1-p)/p) * (1 - 2*y_i).
        """
        bits = np.asarray(bits, dtype=np.uint8).flatten()
        p = float(np.clip(p, 0.0, 0.5))

        if p == 0.0:
            return self.transmit_lossless(bits)

        # Generate bit-flip error mask
        flips = (self.rng.random(len(bits)) < p).astype(np.uint8)
        received_bits = (bits ^ flips).astype(np.uint8)

        # Compute BSC LLRs
        p_safe = np.clip(p, 1e-12, 0.5 - 1e-12)
        log_ratio = np.log((1.0 - p_safe) / p_safe)
        llrs = log_ratio * (1.0 - 2.0 * received_bits.astype(np.float64))

        return received_bits, llrs

    def transmit_awgn(
        self,
        bits: np.ndarray,
        eb_no_db: float,
        code_rate: float = 1.0
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, float]:
        """
        Transmit bits through baseband electrical wired link with AWGN and BPSK modulation.
        BPSK mapping: 0 -> +1.0 V, 1 -> -1.0 V.
        Noise variance: sigma^2 = 1 / (2 * code_rate * 10^(Eb/N0_dB / 10)).
        Returns:
            hard_bits: Sliced received bits (y < 0 -> 1, y >= 0 -> 0).
            soft_samples: Real continuous channel samples y = s + n.
            llrs: Log-likelihood ratios L_i = 2 * y / sigma^2.
            sigma: Channel noise standard deviation.
        """
        bits = np.asarray(bits, dtype=np.uint8).flatten()

        # Handle infinite SNR (lossless case)
        if eb_no_db >= 50.0:
            hard_bits, llrs = self.transmit_lossless(bits)
            return hard_bits, (1.0 - 2.0 * bits).astype(np.float64), llrs, 0.0

        # BPSK modulation: 0 -> +1, 1 -> -1
        s = 1.0 - 2.0 * bits.astype(np.float64)

        # Compute noise standard deviation
        eb_no_linear = 10.0 ** (eb_no_db / 10.0)
        es_no_linear = eb_no_linear * code_rate
        sigma = 1.0 / np.sqrt(2.0 * es_no_linear)

        # Add zero-mean Gaussian noise n ~ N(0, sigma^2)
        noise = self.rng.normal(0.0, sigma, size=len(bits))
        y = s + noise

        # Hard slicer decision
        hard_bits = (y < 0.0).astype(np.uint8)

        # Channel LLR: 2 * y / sigma^2
        llrs = (2.0 / (sigma**2)) * y

        return hard_bits, y, llrs, sigma

    @staticmethod
    def theoretical_uncoded_ber_awgn(eb_no_db: float) -> float:
        """
        Calculate exact theoretical BPSK uncoded BER over AWGN:
        P_b = Q(sqrt(2 * Eb/N0)) = 0.5 * erfc(sqrt(Eb/N0)).
        """
        eb_no_linear = 10.0 ** (eb_no_db / 10.0)
        # Using exact Python math.erfc
        return 0.5 * math.erfc(math.sqrt(eb_no_linear))
