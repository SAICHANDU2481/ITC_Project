"""
Saturated Information Source Generator.
Simulates a source that continuously generates information with configurable
statistical properties and reproducible seeds.
"""

from typing import List, Tuple, Union, Optional
import numpy as np


class SaturatedSource:
    """
    Saturated information source capable of generating continuous streams of:
    1. Natural / structured ASCII text (telemetry packets).
    2. Two-state Markov correlated binary sequences with controlled entropy.
    3. Biased or uniform pseudo-random symbol sequences.
    """

    def __init__(self, seed: Optional[int] = 42):
        self.seed = seed
        self.rng = np.random.default_rng(seed)

    def reset_seed(self, seed: Optional[int] = None) -> None:
        """Reset the random number generator seed."""
        if seed is not None:
            self.seed = seed
        self.rng = np.random.default_rng(self.seed)

    def generate_text_stream(self, num_packets: int = 5, packet_length: int = 64) -> str:
        """
        Generate a structured telemetry / payload string representing continuous
        stream transmissions across a network interface.
        """
        templates = [
            "NODE-VITAP-23BCE7551:SENSOR_TEMP={temp:.2f}C:VOLT={volt:.2f}V:STATUS=OK;",
            "PAYLOAD_DATA_FRAME_WIRED_LINK_ID={link_id:04d}_STREAM_SATURATED_DATA_PACKET;",
            "TELEMETRY_LOG_CHANNEL_CODING_EXPERIMENT_REG_23BCE7551_PKT_{pkt_id:05d};",
            "ETH_FRAME_PREAMBLE_10GBASE_T_IEEE802_3AN_WIRED_LOSSLESS_TEST_SEQ_{seq:04d};",
        ]

        text_stream = []
        for i in range(num_packets):
            tmpl = templates[i % len(templates)]
            segment = tmpl.format(
                temp=20.0 + 15.0 * self.rng.random(),
                volt=3.1 + 0.3 * self.rng.random(),
                link_id=int(self.rng.integers(1, 1000)),
                pkt_id=i + 1,
                seq=(i * 17) % 1000,
            )
            # Pad or slice to desired length approximately
            text_stream.append(segment)

        return "".join(text_stream)

    def generate_markov_bits(self, num_bits: int, p01: float = 0.15, p10: float = 0.25) -> np.ndarray:
        """
        Generate correlated binary sequence using a 2-state discrete-time Markov chain.
        State 0 -> State 1 with prob p01.
        State 1 -> State 0 with prob p10.
        Produces non-uniform entropy H(X) < 1, making source compression effective.
        """
        bits = np.empty(num_bits, dtype=np.uint8)
        current_state = 0 if self.rng.random() < 0.5 else 1

        for i in range(num_bits):
            bits[i] = current_state
            if current_state == 0:
                if self.rng.random() < p01:
                    current_state = 1
            else:
                if self.rng.random() < p10:
                    current_state = 0

        return bits

    def generate_random_bits(self, num_bits: int, p_one: float = 0.5) -> np.ndarray:
        """Generate independent Bernoulli bits with P(1) = p_one."""
        return (self.rng.random(num_bits) < p_one).astype(np.uint8)

    @staticmethod
    def compute_empirical_entropy(data: Union[str, np.ndarray]) -> float:
        """
        Calculate Shannon entropy H(X) = -sum(p * log2(p)) in bits/symbol.
        """
        if isinstance(data, str):
            symbols = list(data.encode('utf-8'))
        else:
            symbols = np.asarray(data).flatten()

        if len(symbols) == 0:
            return 0.0

        _, counts = np.unique(symbols, return_counts=True)
        probabilities = counts / len(symbols)
        # Avoid log(0)
        probabilities = probabilities[probabilities > 0]
        return float(-np.sum(probabilities * np.log2(probabilities)))
