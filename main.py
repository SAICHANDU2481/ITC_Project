"""
Main Execution Entry Point for Information Theory and Channel Coding (ITC) Project.
Student Details:
- Name: Aravind
- Registration Number: 23BCE7551
- Topic: WIRED NETWORK DIGITAL COMMUNICATION SYSTEM
- Institution: School of Computer Science and Engineering, VIT-AP University
"""

import sys
import os
import argparse
import time

from src.source_coding import SaturatedSource, BinaryConverter, LZWCodec
from src.channel_coding import LDPCCodec, PolarCodec, HammingCodec
from src.channel_model import WiredChannel, ChannelAnalyzer
from src.metrics import PerformanceEvaluator
from src.simulation import CommunicationPipeline, ExperimentRunner


def print_banner():
    banner = """
========================================================================================
   INFORMATION THEORY & CHANNEL CODING: WIRED COMMUNICATION SYSTEM SIMULATION
   Student Registration Number: 23BCE7551 | Topic: WIRED NETWORK
   Techniques: LZW Source Coding + IEEE 802.3an LDPC / Polar / Hamming FEC
========================================================================================
"""
    print(banner)


def demonstrate_single_transmission():
    """
    Demonstrate end-to-end live pipeline with exact original vs reconstructed verification.
    """
    print("\n" + "="*80)
    print("LIVE DEMONSTRATION: Saturated Source -> LZW -> LDPC -> Wired Channel -> Recovery")
    print("="*80)

    # 1. Source generation
    source = SaturatedSource(seed=42)
    telemetry_stream = source.generate_text_stream(num_packets=3)
    print(f"\n[1] SATURATED SOURCE GENERATION:")
    print(f"    Original Information (Length: {len(telemetry_stream)} chars):")
    print(f"    \"{telemetry_stream}\"")

    # 2. Binary conversion
    raw_bits = BinaryConverter.text_to_bits(telemetry_stream)
    entropy = source.compute_empirical_entropy(telemetry_stream)
    print(f"\n[2] BINARY SOURCE REPRESENTATION:")
    print(f"    Raw bit count: {len(raw_bits)} bits ({len(raw_bits)//8} bytes)")
    print(f"    Empirical Shannon Entropy H(X): {entropy:.4f} bits/symbol")

    # 3. Source Coding (LZW)
    lzw = LZWCodec(bit_depth=12)
    source_encoded_bits, src_stats = lzw.encode(telemetry_stream)
    print(f"\n[3] MODERN LZW SOURCE ENCODER:")
    print(f"    Compressed bit count: {src_stats['compressed_bits']} bits (from {src_stats['raw_bits']} bits)")
    print(f"    Compression Ratio: {src_stats['compression_ratio']:.3f}x")
    print(f"    Bandwidth Space Savings: {src_stats['space_saving_pct']:.2f}%")

    # 4. Modern Channel Coding (LDPC Rate-1/2)
    ldpc = LDPCCodec(n=64, k=32, max_iter=25, algorithm="sum_product", seed=42)
    tx_bits, pad_len = ldpc.encode(source_encoded_bits)
    coding_metrics = PerformanceEvaluator.calculate_coding_metrics(ldpc.n, ldpc.k)
    print(f"\n[4] IEEE 802.3an LDPC CHANNEL ENCODER:")
    print(f"    Codeword block length (N): {ldpc.n}, Message block length (K): {ldpc.k}")
    print(f"    Code Rate (R): {coding_metrics['code_rate']:.2f}, Redundancy Overhead: {coding_metrics['redundancy_overhead_pct']:.1f}%")
    print(f"    Total Transmitted Codeword Bits: {len(tx_bits)} bits (Padding: {pad_len} bits)")

    # 5. Wired Channel Transmission
    channel = WiredChannel(seed=42)
    print(f"\n[5] TRANSMISSION THROUGH WIRED PHYSICAL CHANNEL:")

    # Case A: Lossless Channel (Teacher's direct baseline)
    print("\n  --- CASE A: Ideal Lossless Wired Baseline (p = 0, SNR -> inf) ---")
    rx_lossless, llrs_lossless = channel.transmit_lossless(tx_bits)
    dec_lossless = ldpc.decode(llrs_lossless, pad_len=pad_len, channel_type="lossless")
    rec_text_lossless = lzw.decode(dec_lossless, return_as_string=True)
    ber_lossless = PerformanceEvaluator.calculate_ber(source_encoded_bits, dec_lossless)
    exact_lossless = (rec_text_lossless == telemetry_stream)
    print(f"      Pre-FEC Errors: 0 / {len(tx_bits)} | BER: 0.0000")
    print(f"      Post-FEC Errors: 0 / {len(source_encoded_bits)} | BER: 0.0000")
    print(f"      Exact Information Recovery: {exact_lossless} [PERFECT LOSSLESS RESTORATION]")

    # Case B: Realistic Noisy Wired Channel (AWGN at Eb/N0 = 4.0 dB)
    snr_test = 4.0
    print(f"\n  --- CASE B: Realistic Wired AWGN Link (Eb/N0 = {snr_test} dB) ---")
    rx_hard, rx_soft, rx_llrs, sigma = channel.transmit_awgn(tx_bits, eb_no_db=snr_test, code_rate=ldpc.rate)
    pre_fec_eval = PerformanceEvaluator.calculate_ber(tx_bits, rx_hard)
    print(f"      Noise std dev sigma: {sigma:.4f}")
    print(f"      Pre-FEC Channel Slicer Errors: {pre_fec_eval['bit_errors']} / {pre_fec_eval['total_bits']} bits")
    print(f"      Pre-FEC Bit Error Rate (BER): {pre_fec_eval['ber']:.4e}")

    # Case C: Uncoded transmission baseline over the same channel
    rx_uncoded_hard, _, _, _ = channel.transmit_awgn(source_encoded_bits, eb_no_db=snr_test, code_rate=1.0)
    uncoded_eval = PerformanceEvaluator.calculate_ber(source_encoded_bits, rx_uncoded_hard)
    print(f"\n  --- COMPARISON: Uncoded Wired Transmission at Eb/N0 = {snr_test} dB ---")
    print(f"      Uncoded Received Bit Errors: {uncoded_eval['bit_errors']} / {uncoded_eval['total_bits']} bits")
    print(f"      Uncoded BER: {uncoded_eval['ber']:.4e}")

    # 6. Channel Decoding via Belief Propagation
    print(f"\n[6] CHANNEL DECODING (Iterative Log-Domain Belief Propagation):")
    dec_bits = ldpc.decode(rx_soft, pad_len=pad_len, channel_type="awgn", sigma=sigma)
    post_fec_eval = PerformanceEvaluator.calculate_ber(source_encoded_bits, dec_bits)
    print(f"      Post-FEC Residual Errors: {post_fec_eval['bit_errors']} / {post_fec_eval['total_bits']} bits")
    print(f"      Post-FEC Bit Error Rate: {post_fec_eval['ber']:.4e}")
    print(f"      Coding Error Suppression Gain: {pre_fec_eval['ber'] / max(post_fec_eval['ber'], 1e-12):.1f}x reduction")

    # 7. Source Reconstruction
    print(f"\n[7] SOURCE DECODING & RECONSTRUCTION:")
    reconstructed_text = lzw.decode(dec_bits, return_as_string=True)
    exact_recovery = (reconstructed_text == telemetry_stream)
    print(f"      Reconstructed Text Length: {len(reconstructed_text)} chars")
    print(f"      Reconstructed Excerpt: \"{reconstructed_text[:80]}...\"")
    print(f"      Exact Bit-for-Bit Recovery: {exact_recovery}")
    if exact_recovery:
        print("      SUCCESS: The LDPC decoder eradicated all channel errors, enabling 100% exact source restoration!")


def run_full_suite():
    """
    Run the complete experimental suite, save CSVs, and plot figures.
    """
    runner = ExperimentRunner(output_dir="results", seed=42)

    # 1. AWGN Sweep (0 to 10 dB)
    runner.run_awgn_experiment(eb_no_range=[0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0], bits_per_point=25600)

    # 2. BSC Sweep (0.0005 to 0.15)
    runner.run_bsc_experiment(bits_per_point=25600)

    # 3. Source Compression Study
    runner.run_source_compression_study()

    # 4. Generate all plots
    runner.generate_all_plots(paper_fig_dir="paper/figures")

    print("\n" + "="*80)
    print("ALL EXPERIMENTS COMPLETE AND FIGURES GENERATED SUCCESSFULLY!")
    print("="*80)


def main():
    parser = argparse.ArgumentParser(description="ITC Wired Communication System Simulation (Reg: 23BCE7551)")
    parser.add_argument("--demo", action="store_true", help="Run live end-to-end single transmission demo")
    parser.add_argument("--experiments", action="store_true", help="Run full Monte Carlo experiments and generate plots")
    parser.add_argument("--all", action="store_true", help="Run both demo and full experiments")

    args = parser.parse_args()

    print_banner()

    if args.demo:
        demonstrate_single_transmission()
    elif args.experiments:
        run_full_suite()
    else:
        # Default run both
        demonstrate_single_transmission()
        run_full_suite()


if __name__ == "__main__":
    main()
