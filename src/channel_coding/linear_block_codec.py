"""
Systematic Linear Block Codec (Hamming / BCH baseline).
Implements standard systematic (7, 4) Hamming forward error correction
with syndrome decoding for low-complexity wireline links.
"""

from typing import Tuple
import numpy as np
from .base import ChannelCodec


class HammingCodec(ChannelCodec):
    """
    Systematic (7, 4) Hamming Codec.
    Corrects all single-bit errors per 7-bit block with zero ambiguity.
    """

    def __init__(self):
        super().__init__(n=7, k=4, name="Hamming(7,4)")

        # Generator matrix G = [I_4 | P] in systematic form
        # P is 4x3 parity submatrix
        self.P = np.array([
            [1, 1, 0],
            [1, 0, 1],
            [0, 1, 1],
            [1, 1, 1]
        ], dtype=np.uint8)

        self.G = np.hstack([np.eye(4, dtype=np.uint8), self.P])

        # Parity check matrix H = [P^T | I_3] (3x7)
        self.H = np.hstack([self.P.T, np.eye(3, dtype=np.uint8)])

        # Precompute syndrome decoding dictionary
        # syndrome s (3-bit integer) -> error pattern e (7-bit vector)
        self.syndrome_table = {}
        # Zero syndrome -> no error
        self.syndrome_table[0] = np.zeros(7, dtype=np.uint8)

        for col in range(7):
            e = np.zeros(7, dtype=np.uint8)
            e[col] = 1
            s_vec = np.mod(self.H @ e, 2)
            s_int = int((s_vec[0] << 2) | (s_vec[1] << 1) | s_vec[2])
            self.syndrome_table[s_int] = e

    def encode_block(self, message_bits: np.ndarray) -> np.ndarray:
        m = np.asarray(message_bits, dtype=np.uint8).flatten()
        if len(m) != 4:
            raise ValueError(f"Hamming(7,4) requires 4 message bits, got {len(m)}")
        return np.mod(m @ self.G, 2).astype(np.uint8)

    def decode_block(self, received: np.ndarray, channel_type: str = "awgn", **kwargs) -> np.ndarray:
        y = np.asarray(received).flatten()
        if len(y) != 7:
            raise ValueError(f"Received block length must be 7, got {len(y)}")

        # Hard slicing: distinguish soft/LLR values (positive=0, negative=1)
        # from binary {0, 1} indicators.
        if channel_type in ("awgn", "llr") or np.any(y < 0.0) or np.any(y > 1.0):
            # For BPSK / LLR: 0 -> +1 / +LLR, 1 -> -1 / -LLR; slicer decision: y < 0 -> 1, y >= 0 -> 0
            r_hard = (y < 0.0).astype(np.uint8)
        else:
            # Binary bits {0, 1}
            r_hard = (y > 0.5).astype(np.uint8)

        # Compute syndrome s = H @ r mod 2
        s_vec = np.mod(self.H @ r_hard, 2)
        s_int = int((s_vec[0] << 2) | (s_vec[1] << 1) | s_vec[2])

        error_pattern = self.syndrome_table.get(s_int, np.zeros(7, dtype=np.uint8))
        c_corrected = (r_hard ^ error_pattern).astype(np.uint8)

        # First 4 bits are systematic message bits
        return c_corrected[:4]
