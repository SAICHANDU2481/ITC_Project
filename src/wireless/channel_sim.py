"""
Wireless Physical Layer Channel Simulation Module (Mode C).
Implements BPSK modulation, wireless AWGN channel simulation with exact noise variance,
soft demodulation, LDPC iterative belief propagation decoding, uncoded baseline comparison,
and BER / FER performance evaluation.
"""

from typing import Dict, Any, List, Tuple, Optional, Union
import time
import math
import numpy as np

from src.source_coding.arithmetic_codec import ArithmeticCodec
from src.source_coding.lzw_codec import LZWCodec
from src.source_coding.binary_converter import BinaryConverter
from src.source_coding.saturated_source import SaturatedSource
from src.channel_coding.ldpc_codec import LDPCCodec
from src.metrics.evaluator import PerformanceEvaluator


class WirelessPhysicalChannel:
    """
    Physical-layer wireless channel model.
    Models BPSK baseband signaling over an Additive White Gaussian Noise (AWGN) channel.
    """

    def __init__(self, seed: Optional[int] = 42):
        self.seed = seed
        self.rng = np.random.default_rng(seed)

    def reset_seed(self, seed: Optional[int] = None):
        if seed is not None:
            self.seed = seed
        self.rng = np.random.default_rng(self.seed)

    @staticmethod
    def modulate_bpsk(bits: np.ndarray) -> np.ndarray:
        """
        BPSK modulation: Bit 0 -> +1.0 V, Bit 1 -> -1.0 V.
        """
        b = np.asarray(bits, dtype=np.uint8).flatten()
        return 1.0 - 2.0 * b.astype(np.float64)

    def transmit_awgn(
        self,
        bits: np.ndarray,
        eb_no_db: float,
        code_rate: float = 1.0
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, float]:
        """
        Transmit bits over wireless AWGN channel.
        
        Args:
            bits: Input binary array.
            eb_no_db: Energy per bit to noise spectral density in dB.
            code_rate: FEC code rate R = K/N (1.0 for uncoded, 0.5 for Rate-1/2 LDPC).
            
        Returns:
            hard_bits: Hard sliced decision bits (y < 0 -> 1, y >= 0 -> 0).
            rx_soft: Continuous channel samples y = s + n.
            rx_llrs: Initial log-likelihood ratios L_i = 2 * y / sigma^2.
            sigma: Channel noise standard deviation.
        """
        s = self.modulate_bpsk(bits)

        # Handle lossless / infinite SNR
        if eb_no_db >= 50.0:
            hard = (s < 0.0).astype(np.uint8)
            llrs = np.where(hard == 0, 50.0, -50.0)
            return hard, s, llrs, 0.0

        # Exact noise standard deviation for BPSK
        eb_no_lin = 10.0 ** (eb_no_db / 10.0)
        es_no_lin = eb_no_lin * code_rate
        sigma = 1.0 / np.sqrt(2.0 * es_no_lin)

        noise = self.rng.normal(0.0, sigma, size=len(s))
        y = s + noise

        hard_bits = (y < 0.0).astype(np.uint8)
        llrs = (2.0 / (sigma ** 2)) * y

        return hard_bits, y, llrs, sigma

    @staticmethod
    def theoretical_bpsk_ber(eb_no_db: float) -> float:
        """
        Theoretical uncoded BPSK BER in AWGN:
        P_b = 0.5 * erfc(sqrt(10^(Eb/N0 / 10))).
        """
        eb_no_lin = 10.0 ** (eb_no_db / 10.0)
        return float(0.5 * math.erfc(math.sqrt(eb_no_lin)))


class WirelessSimulationPipeline:
    """
    Complete end-to-end wireless simulation pipeline comparing
    LDPC forward error correction against uncoded transmission over AWGN.
    """

    def __init__(self, seed: Optional[int] = 42):
        self.seed = seed
        self.channel = WirelessPhysicalChannel(seed=seed)
        self.arithmetic_codec = ArithmeticCodec()
        self.lzw_codec = LZWCodec(bit_depth=12)
        self.ldpc_codec = LDPCCodec(n=64, k=32, max_iter=25, seed=seed)

    def run_simulation(
        self,
        message: str,
        eb_no_db: float = 4.0,
        source_codec: str = "arithmetic",
        ldpc_max_iter: int = 25
    ) -> Dict[str, Any]:
        """
        Execute full physical-layer simulation.
        """
        t0 = time.perf_counter()

        # Step 1: Raw payload
        raw_bytes = message.encode("utf-8")
        raw_bits = np.unpackbits(np.frombuffer(raw_bytes, dtype=np.uint8))
        orig_size = len(raw_bytes)

        # Step 2: Source Coding
        t_src = time.perf_counter()
        if source_codec.lower() == "arithmetic":
            compressed_bytes, src_stats = self.arithmetic_codec.encode(message)
            source_bits = np.unpackbits(np.frombuffer(compressed_bytes, dtype=np.uint8))
        else:
            source_bits, src_stats = self.lzw_codec.encode(message)
            compressed_bytes = np.packbits(source_bits).tobytes()
        src_duration_ms = (time.perf_counter() - t_src) * 1000.0

        # Step 3: LDPC Channel Encoding
        t_enc = time.perf_counter()
        self.ldpc_codec.max_iter = ldpc_max_iter
        tx_coded_bits, pad_len = self.ldpc_codec.encode(source_bits)
        enc_duration_ms = (time.perf_counter() - t_enc) * 1000.0
        num_blocks = len(tx_coded_bits) // self.ldpc_codec.n

        # Step 4: Coded Transmission over Wireless AWGN (Rate R = 0.5)
        rx_hard_coded, rx_soft, _, sigma_coded = self.channel.transmit_awgn(
            tx_coded_bits, eb_no_db=eb_no_db, code_rate=self.ldpc_codec.rate
        )
        pre_fec_eval = PerformanceEvaluator.calculate_ber(tx_coded_bits, rx_hard_coded)

        # Step 5: Iterative LDPC Log-Domain Belief Propagation Decoding
        t_dec = time.perf_counter()
        dec_source_bits = self.ldpc_codec.decode(
            rx_soft, pad_len=pad_len, channel_type="awgn", sigma=sigma_coded
        )
        dec_duration_ms = (time.perf_counter() - t_dec) * 1000.0

        post_fec_eval = PerformanceEvaluator.calculate_ber(source_bits, dec_source_bits)

        # Measure Block / Frame Error Rate
        block_errors = 0
        padded_tx = np.concatenate([source_bits, np.zeros(pad_len, dtype=np.uint8)]) if pad_len > 0 else source_bits
        padded_dec = np.concatenate([dec_source_bits, np.zeros(pad_len, dtype=np.uint8)]) if pad_len > 0 else dec_source_bits
        for b in range(num_blocks):
            blk_tx = padded_tx[b * self.ldpc_codec.k : (b + 1) * self.ldpc_codec.k]
            blk_dec = padded_dec[b * self.ldpc_codec.k : (b + 1) * self.ldpc_codec.k]
            if not np.array_equal(blk_tx, blk_dec):
                block_errors += 1
        fer = float(block_errors / num_blocks) if num_blocks > 0 else 0.0

        # Step 6: Source Reconstruction
        reconstructed_text = ""
        try:
            if source_codec.lower() == "arithmetic":
                dec_bytes = np.packbits(dec_source_bits).tobytes()
                reconstructed_text = self.arithmetic_codec.decode(dec_bytes, return_as_string=True)
            else:
                reconstructed_text = self.lzw_codec.decode(dec_source_bits, return_as_string=True)
        except Exception as e:
            reconstructed_text = f"[SOURCE_DECODE_ERROR: {str(e)}]"

        exact_recovery = (reconstructed_text == message)

        # Step 7: Uncoded Baseline over the Same Channel at Same Eb/N0 (Rate R = 1.0)
        rx_uncoded_hard, _, _, sigma_uncoded = self.channel.transmit_awgn(
            source_bits, eb_no_db=eb_no_db, code_rate=1.0
        )
        uncoded_eval = PerformanceEvaluator.calculate_ber(source_bits, rx_uncoded_hard)

        uncoded_text = ""
        try:
            if source_codec.lower() == "arithmetic":
                dec_unc_bytes = np.packbits(rx_uncoded_hard).tobytes()
                uncoded_text = self.arithmetic_codec.decode(dec_unc_bytes, return_as_string=True)
            else:
                uncoded_text = self.lzw_codec.decode(rx_uncoded_hard, return_as_string=True)
        except Exception:
            uncoded_text = "[UNCODED_ERROR_CORRUPTED_STREAM]"

        uncoded_exact = (uncoded_text == message)

        total_sim_ms = (time.perf_counter() - t0) * 1000.0
        gain = (pre_fec_eval['ber'] / max(post_fec_eval['ber'], 1e-12)) if post_fec_eval['ber'] > 0 else float("inf")

        return {
            'eb_no_db': eb_no_db,
            'source_codec': source_codec,
            'orig_size_bytes': orig_size,
            'compressed_size_bytes': len(compressed_bytes),
            'compression_ratio': float(orig_size / max(len(compressed_bytes), 1)),
            'total_codeword_bits': len(tx_coded_bits),
            'info_bits': len(source_bits),
            'num_ldpc_blocks': num_blocks,
            'noise_sigma_coded': sigma_coded,
            'noise_sigma_uncoded': sigma_uncoded,
            # Coded BER & FER
            'pre_fec_errors': pre_fec_eval['bit_errors'],
            'pre_fec_ber': pre_fec_eval['ber'],
            'post_fec_errors': post_fec_eval['bit_errors'],
            'post_fec_ber': post_fec_eval['ber'],
            'frame_errors': block_errors,
            'fer': fer,
            'error_suppression_gain': gain,
            'exact_recovery': exact_recovery,
            'reconstructed_text': reconstructed_text,
            # Uncoded baseline
            'uncoded_errors': uncoded_eval['bit_errors'],
            'uncoded_ber': uncoded_eval['ber'],
            'uncoded_exact': uncoded_exact,
            'uncoded_text': uncoded_text,
            'theory_bpsk_ber': self.channel.theoretical_bpsk_ber(eb_no_db),
            # Timings
            'src_duration_ms': src_duration_ms,
            'enc_duration_ms': enc_duration_ms,
            'dec_duration_ms': dec_duration_ms,
            'total_sim_ms': total_sim_ms
        }

    def run_snr_sweep(
        self,
        eb_no_list: List[float] = [0.0, 2.0, 4.0, 6.0, 8.0, 10.0],
        bits_per_point: int = 12800,
        trials_per_point: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Run multi-point Monte Carlo BER sweep for plotting and CSV export.
        """
        records = []
        source = SaturatedSource(seed=42)

        for snr in eb_no_list:
            pre_errs, post_errs, unc_errs, blk_errs = 0, 0, 0, 0
            total_cw_bits = 0
            total_info_bits = 0
            total_blocks = 0

            for trial in range(trials_per_point):
                # Generate random information bits
                info_bits = source.rng.integers(0, 2, size=bits_per_point // trials_per_point, dtype=np.uint8)
                tx_cw, pad = self.ldpc_codec.encode(info_bits)
                n_blks = len(tx_cw) // self.ldpc_codec.n

                # Coded AWGN
                rx_hard, rx_soft, _, sig = self.channel.transmit_awgn(
                    tx_cw, eb_no_db=snr, code_rate=self.ldpc_codec.rate
                )
                pre_res = PerformanceEvaluator.calculate_ber(tx_cw, rx_hard)
                pre_errs += pre_res['bit_errors']
                total_cw_bits += len(tx_cw)

                # Decode
                dec_info = self.ldpc_codec.decode(rx_soft, pad_len=pad, channel_type="awgn", sigma=sig)
                post_res = PerformanceEvaluator.calculate_ber(info_bits, dec_info)
                post_errs += post_res['bit_errors']
                total_info_bits += len(info_bits)

                # FER
                padded_tx = np.concatenate([info_bits, np.zeros(pad, dtype=np.uint8)]) if pad > 0 else info_bits
                padded_dec = np.concatenate([dec_info, np.zeros(pad, dtype=np.uint8)]) if pad > 0 else dec_info
                for b in range(n_blks):
                    if not np.array_equal(padded_tx[b*32:(b+1)*32], padded_dec[b*32:(b+1)*32]):
                        blk_errs += 1
                total_blocks += n_blks

                # Uncoded AWGN
                rx_unc, _, _, _ = self.channel.transmit_awgn(info_bits, eb_no_db=snr, code_rate=1.0)
                unc_res = PerformanceEvaluator.calculate_ber(info_bits, rx_unc)
                unc_errs += unc_res['bit_errors']

            rec = {
                'eb_no_db': snr,
                'theory_bpsk_ber': self.channel.theoretical_bpsk_ber(snr),
                'uncoded_ber': float(unc_errs / total_info_bits),
                'pre_fec_ber': float(pre_errs / total_cw_bits),
                'ldpc_post_fec_ber': float(post_errs / total_info_bits),
                'frame_error_rate': float(blk_errs / total_blocks) if total_blocks > 0 else 0.0,
                'total_info_bits': total_info_bits,
                'total_codeword_bits': total_cw_bits
            }
            records.append(rec)

        return records
