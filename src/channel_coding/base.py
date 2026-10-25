"""
Base Channel Codec Interface.
Defines abstract interface and common block segmentation / padding utilities
for forward error correction (FEC) in digital communication systems.
"""

from abc import ABC, abstractmethod
from typing import Tuple, Optional
import numpy as np


class ChannelCodec(ABC):
    """
    Abstract base class for channel encoders and decoders.
    """

    def __init__(self, n: int, k: int, name: str = "ChannelCodec"):
        """
        Args:
            n: Codeword length (total bits per block).
            k: Message length (information bits per block).
            name: Human-readable codec name.
        """
        if k >= n:
            raise ValueError(f"Message length k ({k}) must be strictly less than block length n ({n}).")
        self.n = n
        self.k = k
        self.name = name
        self.rate = float(k) / float(n)
        self.redundancy_overhead = float(n - k) / float(k)

    @abstractmethod
    def encode_block(self, message_bits: np.ndarray) -> np.ndarray:
        """Encode a single block of k bits into n codeword bits."""
        pass

    @abstractmethod
    def decode_block(self, received: np.ndarray, channel_type: str = "awgn", **kwargs) -> np.ndarray:
        """Decode a received block of n channel outputs (LLRs or hard bits) into k information bits."""
        pass

    def encode(self, bits: np.ndarray) -> Tuple[np.ndarray, int]:
        """
        Segment an arbitrary length bitstream into blocks of size k,
        zero-pad the final block if needed, and encode all blocks.
        Returns:
            encoded_bits: Concatenated codeword bits of length M * n.
            pad_len: Number of zero-padding bits added to the original stream.
        """
        bits = np.asarray(bits, dtype=np.uint8).flatten()
        pad_len = (self.k - (len(bits) % self.k)) % self.k
        if pad_len > 0:
            padded_bits = np.concatenate([bits, np.zeros(pad_len, dtype=np.uint8)])
        else:
            padded_bits = bits

        num_blocks = len(padded_bits) // self.k
        if num_blocks == 0:
            return np.empty(0, dtype=np.uint8), 0

        encoded_blocks = []
        for i in range(num_blocks):
            blk = padded_bits[i * self.k : (i + 1) * self.k]
            cw = self.encode_block(blk)
            encoded_blocks.append(cw)

        return np.concatenate(encoded_blocks), pad_len

    def decode(self, received: np.ndarray, pad_len: int = 0, channel_type: str = "awgn", **kwargs) -> np.ndarray:
        """
        Segment received channel sequence of length M * n, decode each block,
        concatenate decoded information bits, and remove any pad_len bits.
        """
        received = np.asarray(received).flatten()
        if len(received) == 0:
            return np.empty(0, dtype=np.uint8)

        if len(received) % self.n != 0:
            raise ValueError(
                f"Received stream length ({len(received)}) must be a multiple of codeword length n ({self.n})."
            )

        if pad_len < 0 or pad_len >= self.k:
            raise ValueError(
                f"Padding length pad_len ({pad_len}) must be in the range [0, k-1] ([0, {self.k - 1}])."
            )

        num_blocks = len(received) // self.n
        decoded_blocks = []
        for i in range(num_blocks):
            blk = received[i * self.n : (i + 1) * self.n]
            dec_blk = self.decode_block(blk, channel_type=channel_type, **kwargs)
            decoded_blocks.append(dec_blk)

        all_decoded = np.concatenate(decoded_blocks)
        if pad_len > 0 and len(all_decoded) >= pad_len:
            return all_decoded[:-pad_len]
        return all_decoded
