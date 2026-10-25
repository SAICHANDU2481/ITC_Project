"""
Polar Codec (Arıkan, 2009).
Implements Polar code construction via Bhattacharyya parameter channel polarization,
recursive Arikan kernel encoding, and Successive Cancellation (SC) decoding.
Standardized in 3GPP 5G and evaluated for modern wireline optical/backplane links.
"""

from typing import List, Set, Tuple, Optional
import numpy as np
from .base import ChannelCodec


class PolarCodec(ChannelCodec):
    """
    Polar Codec with Successive Cancellation (SC) LLR decoding.
    """

    def __init__(self, n: int = 64, k: int = 32, design_snr_db: float = 2.0):
        """
        Args:
            n: Codeword length, must be a power of 2 (e.g. 32, 64, 128).
            k: Information message length (k < n).
            design_snr_db: Design SNR for Bhattacharyya parameter computation.
        """
        # Validate power of 2
        m = int(np.round(np.log2(n)))
        if (1 << m) != n:
            raise ValueError(f"Polar code length n ({n}) must be a power of 2.")

        super().__init__(n=n, k=k, name=f"Polar({n},{k})-SC")
        self.log2_n = m
        self.design_snr_db = design_snr_db

        # Compute channel polarization bit reliabilities using Bhattacharyya recursions
        self.info_indices, self.frozen_indices = self._select_information_channels(n, k, design_snr_db)

        # Precompute Arikan polarization matrix F_N
        F2 = np.array([[1, 0], [1, 1]], dtype=np.uint8)
        self.FN = F2
        for _ in range(self.log2_n - 1):
            self.FN = np.kron(self.FN, F2)

    def _select_information_channels(self, n: int, k: int, design_snr_db: float) -> Tuple[List[int], Set[int]]:
        """
        Compute Bhattacharyya parameters Z(W) recursively to identify the k most reliable
        bit channels for information transmission.
        """
        # Initial Bhattacharyya parameter for AWGN channel at design SNR
        snr_linear = 10.0 ** (design_snr_db / 10.0)
        z0 = np.exp(-snr_linear)

        z = np.array([z0], dtype=np.float64)
        for stage in range(self.log2_n):
            z_minus = 2.0 * z - z**2
            z_plus = z**2
            z = np.empty(2 * len(z), dtype=np.float64)
            z[0::2] = z_minus
            z[1::2] = z_plus

        # Sort bit channels by Bhattacharyya parameter ascending (smallest error probability first)
        reliability_order = np.argsort(z)

        # Top k channels are information channels; rest are frozen
        info_indices = sorted(reliability_order[:k].tolist())
        frozen_indices = set(reliability_order[k:].tolist())

        return info_indices, frozen_indices

    def encode_block(self, message_bits: np.ndarray) -> np.ndarray:
        """
        Map k message bits onto information channels in vector u (with frozen bits = 0),
        then transform via Arikan matrix: x = u @ F_N mod 2.
        """
        m_bits = np.asarray(message_bits, dtype=np.uint8).flatten()
        if len(m_bits) != self.k:
            raise ValueError(f"Polar message length must be {self.k}, got {len(m_bits)}")

        u = np.zeros(self.n, dtype=np.uint8)
        u[self.info_indices] = m_bits

        # Fast recursive Arikan polarization encoding
        x = u.copy()
        for step in range(self.log2_n):
            block_size = 1 << (step + 1)
            half = block_size >> 1
            for offset in range(0, self.n, block_size):
                for j in range(half):
                    x[offset + j] = (x[offset + j] ^ x[offset + half + j])

        return x

    def decode_block(self, received: np.ndarray, channel_type: str = "awgn", **kwargs) -> np.ndarray:
        """
        Successive Cancellation (SC) decoding over received channel block.
        """
        y = np.asarray(received, dtype=np.float64).flatten()
        if len(y) != self.n:
            raise ValueError(f"Received block length must be {self.n}, got {len(y)}")

        # Convert to channel LLRs
        if "llrs" in kwargs:
            L_ch = kwargs["llrs"]
        elif channel_type == "awgn":
            sigma = kwargs.get("sigma", 0.5)
            L_ch = (2.0 / (sigma**2)) * y
        elif channel_type == "bsc":
            if np.any(y < 0.0) or np.any(y > 1.0):
                L_ch = y.copy()
            else:
                p = kwargs.get("p", 0.05)
                p = np.clip(p, 1e-12, 0.5 - 1e-12)
                log_ratio = np.log((1.0 - p) / p)
                L_ch = log_ratio * (1.0 - 2.0 * y)
        elif channel_type in ("lossless", "ideal"):
            if np.any(y < 0.0) or np.any(y > 1.0):
                L_ch = y.copy()
            else:
                # Binary bits {0, 1}: 0 -> +50.0, 1 -> -50.0
                L_ch = 50.0 * (1.0 - 2.0 * y)
        else:
            if not (np.any(y < 0.0) or np.any(y > 1.0)) and np.all((y == 0.0) | (y == 1.0)):
                # Fallback for binary hard bits {0, 1}
                L_ch = 50.0 * (1.0 - 2.0 * y)
            else:
                L_ch = y.copy()

        # Successive cancellation decoding tree
        # Data structure for SC tree: LLR arrays at each stage
        u_hat = np.zeros(self.n, dtype=np.uint8)

        # Recursive SC traversal
        self._sc_decode(0, 0, L_ch, u_hat)

        # Extract information bits
        return u_hat[self.info_indices]

    def _sc_decode(self, stage: int, index: int, llrs: np.ndarray, u_hat: np.ndarray) -> np.ndarray:
        """
        Recursive helper for Successive Cancellation decoding.
        stage: tree depth from root (0 to log2_n)
        index: block index at current stage
        llrs: LLR vector at current node
        u_hat: global estimated u vector
        """
        n_curr = len(llrs)
        if n_curr == 1:
            bit_idx = index
            if bit_idx in self.frozen_indices:
                u_hat[bit_idx] = 0
            else:
                u_hat[bit_idx] = 0 if llrs[0] >= 0.0 else 1
            return np.array([u_hat[bit_idx]], dtype=np.uint8)

        half = n_curr >> 1
        l1 = llrs[:half]
        l2 = llrs[half:]

        # f-node operation for upper branch: f(l1, l2) = sgn(l1)*sgn(l2)*min(|l1|, |l2|)
        s1 = np.sign(l1)
        s1[s1 == 0] = 1.0
        s2 = np.sign(l2)
        s2[s2 == 0] = 1.0
        llr_upper = s1 * s2 * np.minimum(np.abs(l1), np.abs(l2))

        # Decode upper branch
        u1_hat = self._sc_decode(stage + 1, index, llr_upper, u_hat)

        # g-node operation for lower branch: g(l1, l2, u1) = l2 + (1 - 2*u1) * l1
        llr_lower = l2 + (1.0 - 2.0 * u1_hat.astype(np.float64)) * l1

        # Decode lower branch
        u2_hat = self._sc_decode(stage + 1, index + half, llr_lower, u_hat)

        # Combine hard decisions
        u_combined = np.empty(n_curr, dtype=np.uint8)
        u_combined[:half] = (u1_hat ^ u2_hat)
        u_combined[half:] = u2_hat
        return u_combined
