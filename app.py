"""
Streamlit Web Application for Information Theory & Channel Coding (ITC)
Wired Communication System Simulation
Student: Aravind | Registration Number: 23BCE7551
Institution: School of Computer Science and Engineering, VIT-AP University
Track: Wired Network (Terminal Digit 1)
"""

import os
import sys
import time
import math
import io
import json
import numpy as np
import pandas as pd
import streamlit as st
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Ensure local src is importable regardless of current working directory
APP_DIR = os.path.dirname(os.path.abspath(__file__))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

from src.source_coding import SaturatedSource, BinaryConverter, LZWCodec
from src.channel_coding import LDPCCodec, PolarCodec, HammingCodec
from src.channel_model import WiredChannel, ChannelAnalyzer
from src.metrics import PerformanceEvaluator
from src.simulation import CommunicationPipeline, ExperimentRunner

# -----------------------------------------------------------------------------
# Page Configuration & Modern Theme Styling
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Wired Communication Simulation | 23BCE7551",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main-header {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        background: linear-gradient(135deg, #002B49 0%, #005A9C 100%);
        color: white;
        padding: 24px;
        border-radius: 12px;
        margin-bottom: 24px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    .badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 13px;
        font-weight: 600;
        margin-right: 8px;
    }
    .badge-primary { background: #e0f2fe; color: #0369a1; border: 1px solid #bae6fd; }
    .badge-accent { background: #fef3c7; color: #b45309; border: 1px solid #fde68a; }
    .badge-success { background: #dcfce7; color: #15803d; border: 1px solid #bbf7d0; }
    .metric-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 16px;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.03);
    }
    .metric-value {
        font-size: 26px;
        font-weight: 700;
        color: #0f172a;
    }
    .metric-label {
        font-size: 13px;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .stButton>button {
        background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%);
        color: white;
        font-weight: 600;
        border-radius: 8px;
        padding: 12px 24px;
        border: none;
        width: 100%;
        box-shadow: 0 4px 6px rgba(2, 132, 199, 0.25);
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #0369a1 0%, #075985 100%);
        color: white;
    }
</style>
""", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# Top Banner
# -----------------------------------------------------------------------------
st.markdown("""
<div class="main-header">
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
        <div>
            <h1 style="margin: 0; font-size: 28px; font-weight: 700; color: white;">
                Wired Communication System Simulation
            </h1>
            <p style="margin: 6px 0 0 0; font-size: 15px; color: #cbd5e1;">
                Information Theory and Channel Coding (ITC) &nbsp;|&nbsp; Universal LZW Source Coding & Modern FEC (LDPC / Polar / Hamming)
            </p>
        </div>
        <div style="margin-top: 10px;">
            <span class="badge badge-primary">Student: Aravind</span>
            <span class="badge badge-accent">Reg: 23BCE7551</span>
            <span class="badge badge-success">Assignment: Wired Network (Digit 1)</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# Sidebar: Simulation Controls
# -----------------------------------------------------------------------------
st.sidebar.header("⚙️ Simulation Configuration")

# 1. Source Input Selection
st.sidebar.subheader("1. Information Source")
source_mode = st.sidebar.selectbox(
    "Source Input Type",
    [
        "Structured Telemetry (Saturated)",
        "Custom ASCII Text",
        "Correlated Markov Bitstream",
        "Uniform Random Bits (H ≈ 1.0)"
    ],
    index=0
)

custom_text = ""
telemetry_packets = 3
markov_bits = 1024
random_bits_count = 512

if source_mode == "Custom ASCII Text":
    custom_text = st.sidebar.text_area(
        "Payload Text",
        value="VIT-AP University 23BCE7551: Saturated wireline communication link payload demonstration.",
        height=80
    )
elif source_mode == "Structured Telemetry (Saturated)":
    telemetry_packets = st.sidebar.slider("Number of Telemetry Packets", min_value=1, max_value=8, value=3)
elif source_mode == "Correlated Markov Bitstream":
    markov_bits = st.sidebar.select_slider("Number of Bits", options=[256, 512, 1024, 2048, 4096], value=1024)
    p01 = st.sidebar.slider("P(0 -> 1)", 0.05, 0.45, 0.15, step=0.05)
    p10 = st.sidebar.slider("P(1 -> 0)", 0.05, 0.45, 0.25, step=0.05)
else:
    random_bits_count = st.sidebar.select_slider("Random Bitstream Length", options=[128, 256, 512, 1024, 2048], value=512)

# 2. Source Coding (LZW)
st.sidebar.subheader("2. Source Coding (LZW)")
enable_lzw = st.sidebar.checkbox("Enable LZW Dictionary Coding", value=True)
lzw_bit_depth = st.sidebar.slider("Dictionary Codeword Bit-Depth", min_value=9, max_value=13, value=12)

# 3. Channel Coding (FEC)
st.sidebar.subheader("3. Forward Error Correction (FEC)")
fec_codec_name = st.sidebar.selectbox(
    "Channel Codec",
    [
        "IEEE 802.3an LDPC (64, 32) Sum-Product",
        "IEEE 802.3an LDPC (64, 32) Min-Sum",
        "Polar Code (64, 32) SC",
        "Systematic Hamming (7, 4)",
        "Uncoded Baseline (Rate 1.0)"
    ],
    index=0
)

ldpc_max_iter = 25
if "LDPC" in fec_codec_name:
    ldpc_max_iter = st.sidebar.slider("LDPC Max Iterations", min_value=5, max_value=40, value=25, step=5)

# 4. Physical Wired Channel Model
st.sidebar.subheader("4. Physical Wired Link")
channel_choice = st.sidebar.selectbox(
    "Channel Environment",
    [
        "Ideal Lossless Channel (p = 0, H(X|Y) = 0)",
        "Electrical AWGN Link (BPSK / Thermal Noise)",
        "Binary Symmetric Channel (Parametric BSC)"
    ],
    index=0
)

eb_no_db = 4.0
bsc_p = 0.01

if "AWGN" in channel_choice:
    eb_no_db = st.sidebar.slider(
        "Link Eb/N0 (dB)",
        min_value=0.0,
        max_value=12.0,
        value=5.0,
        step=0.5,
        help="Energy per bit to noise power spectral density ratio."
    )
    th_ber = WiredChannel.theoretical_uncoded_ber_awgn(eb_no_db)
    st.sidebar.caption(f"Theoretical Uncoded BPSK BER: **{th_ber:.3e}**")
elif "BSC" in channel_choice:
    bsc_p = st.sidebar.slider(
        "Bit-Flip Probability (p)",
        min_value=0.0005,
        max_value=0.15,
        value=0.01,
        step=0.002,
        format="%.4f"
    )
    st.sidebar.caption(f"Uncoded Channel Error Rate: **{bsc_p:.4f}**")
else:
    st.sidebar.info("Ideal lossless channel: Raw bit error rate is strictly 0.0.")

# Seed control
sim_seed = st.sidebar.number_input("RNG Reproducibility Seed", value=42, step=1)

# Execute Simulation Button
run_simulation_clicked = st.sidebar.button("🚀 Run End-to-End Simulation")


# -----------------------------------------------------------------------------
# Main Page Navigation Tabs
# -----------------------------------------------------------------------------
tab_sim, tab_curves, tab_arch, tab_downloads = st.tabs([
    "📡 Live Pipeline Simulation",
    "📊 Empirical BER & Waterfall Curves",
    "📐 System Architecture & Math",
    "📥 Downloads & IEEE Paper"
])


# -----------------------------------------------------------------------------
# TAB 1: Live Simulation Dashboard
# -----------------------------------------------------------------------------
with tab_sim:
    # Build the codec instance based on user selection
    if "LDPC" in fec_codec_name:
        algo = "min_sum" if "Min-Sum" in fec_codec_name else "sum_product"
        codec = LDPCCodec(n=64, k=32, max_iter=ldpc_max_iter, algorithm=algo, seed=int(sim_seed))
    elif "Polar" in fec_codec_name:
        codec = PolarCodec(n=64, k=32, design_snr_db=3.0)
    elif "Hamming" in fec_codec_name:
        codec = HammingCodec()
    else:
        codec = None

    # Instantiate pipeline
    pipeline = CommunicationPipeline(
        channel_codec=codec,
        use_source_coding=enable_lzw,
        lzw_bit_depth=lzw_bit_depth,
        seed=int(sim_seed)
    )

    # Prepare input payload
    if source_mode == "Custom ASCII Text":
        payload = custom_text if custom_text.strip() else "Empty payload fallback"
    elif source_mode == "Structured Telemetry (Saturated)":
        source = SaturatedSource(seed=int(sim_seed))
        payload = source.generate_text_stream(num_packets=telemetry_packets)
    elif source_mode == "Correlated Markov Bitstream":
        source = SaturatedSource(seed=int(sim_seed))
        payload = source.generate_markov_bits(num_bits=markov_bits, p01=p01, p10=p10)
    else:
        source = SaturatedSource(seed=int(sim_seed))
        payload = source.generate_random_bits(num_bits=random_bits_count, p_one=0.5)

    # Determine channel mode and parameter
    if "Lossless" in channel_choice:
        ch_mode = "lossless"
        ch_param = 0.0
    elif "AWGN" in channel_choice:
        ch_mode = "awgn"
        ch_param = float(eb_no_db)
    else:
        ch_mode = "bsc"
        ch_param = float(bsc_p)

    # Execute simulation
    with st.spinner("Simulating full transmitter -> physical channel -> iterative receiver pipeline..."):
        t_start = time.perf_counter()
        sim_result = pipeline.run_single_transmission(
            input_data=payload,
            channel_mode=ch_mode,
            channel_param=ch_param
        )
        sim_elapsed_ms = (time.perf_counter() - t_start) * 1000.0

    # 1. Recovery Status Alert Banner
    is_exact = sim_result['exact_recovery']
    post_fec_ber = sim_result['post_fec_ber']
    pre_fec_ber = sim_result['pre_fec_ber']

    if is_exact:
        st.success(f"✅ **EXACT BIT-FOR-BIT RECONSTRUCTION VERIFIED!** (Original symbols reconstructed with 100% fidelity. Residual Errors: {sim_result['post_fec_errors']} bits | Post-FEC BER = 0.0000)")
    elif post_fec_ber < pre_fec_ber:
        gain = (pre_fec_ber / max(post_fec_ber, 1e-12))
        st.warning(f"⚠️ **PARTIAL ERROR CORRECTION:** Channel perturbations reduced from {sim_result['pre_fec_errors']} pre-FEC errors to {sim_result['post_fec_errors']} post-FEC errors ({gain:.1f}x error suppression gain). Higher SNR or lower bit-flip rate recommended for 100% exact reconstruction.")
    else:
        st.error(f"❌ **CHANNEL DISTORTION EXCEEDED FEC CAPACITY:** Raw channel noise overwhelmed the decoder. Pre-FEC errors: {sim_result['pre_fec_errors']} | Post-FEC errors: {sim_result['post_fec_errors']}.")

    # 2. Key Performance Metric Cards
    src_stats = sim_result['source_stats']
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        cr_val = src_stats.get('compression_ratio', 1.0)
        saving_pct = src_stats.get('space_saving_pct', 0.0)
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{cr_val:.2f}x</div>
            <div class="metric-label">LZW Compression Ratio</div>
            <div style="font-size: 12px; color: {'#16a34a' if saving_pct > 0 else '#dc2626'}; margin-top: 4px;">
                Space Savings: {saving_pct:+.1f}%
            </div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        code_rate = codec.rate if codec else 1.0
        redundancy = codec.redundancy_overhead * 100.0 if codec else 0.0
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{code_rate:.2f}</div>
            <div class="metric-label">FEC Code Rate (R = K/N)</div>
            <div style="font-size: 12px; color: #475569; margin-top: 4px;">
                Redundancy: {redundancy:.0f}% overhead
            </div>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{pre_fec_ber:.3e}</div>
            <div class="metric-label">Raw Pre-FEC BER</div>
            <div style="font-size: 12px; color: #475569; margin-top: 4px;">
                Slicer Errors: {sim_result['pre_fec_errors']} / {sim_result['tx_bits_count']}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with c4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value" style="color: {'#16a34a' if post_fec_ber == 0 else '#ea580c'};">{post_fec_ber:.3e}</div>
            <div class="metric-label">Decoded Post-FEC BER</div>
            <div style="font-size: 12px; color: #475569; margin-top: 4px;">
                Residual Errors: {sim_result['post_fec_errors']} bits
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.write("")

    # 3. Step-by-Step Pipeline Inspector
    st.subheader("🔍 Discrete Pipeline Stage Inspection")

    with st.expander("Stage 1 & 2: Saturated Source Information & LZW Compression", expanded=True):
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            st.markdown("**Original Information Source:**")
            if isinstance(payload, str):
                st.code(payload[:300] + ("..." if len(payload) > 300 else ""), language="text")
                st.caption(f"Source length: {len(payload)} characters ({len(payload.encode('utf-8')) * 8} raw bits)")
            else:
                st.code(f"Binary Vector: {list(payload[:64])}... (total {len(payload)} bits)", language="text")
                st.caption(f"Bitstream Length: {len(payload)} bits | Unique symbols: {len(np.unique(payload))}")

            ent = SaturatedSource.compute_empirical_entropy(payload)
            st.write(f"Empirical Shannon Entropy $H(X)$: **{ent:.4f} bits/symbol**")

        with col_s2:
            st.markdown("**LZW Universal Source Coding Output:**")
            if enable_lzw:
                st.write(f"- Raw Input Size: **{src_stats.get('raw_bits', 0)} bits** ({src_stats.get('raw_bytes', 0)} bytes)")
                st.write(f"- Compressed Size: **{src_stats.get('compressed_bits', 0)} bits** ({src_stats.get('num_codes', 0)} codes)")
                st.write(f"- Active Dictionary Entries: **{src_stats.get('dictionary_entries_used', 256)} / {1 << lzw_bit_depth}**")
                st.write(f"- Codeword Bit-Depth: **{lzw_bit_depth} bits**")
            else:
                st.info("LZW Source Coding is bypassed. Raw bitstream passed directly to channel coder.")

    with st.expander("Stage 3 & 4: Forward Error Correction & Wired Link Propagation"):
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            st.markdown("**Channel Encoder Configuration:**")
            st.write(f"- Codec Architecture: **{sim_result['codec_name']}**")
            if codec:
                st.write(f"- Codeword Block Length (N): **{codec.n} bits**")
                st.write(f"- Message Block Length (K): **{codec.k} bits**")
                st.write(f"- Total Transmitted Bits: **{sim_result['tx_bits_count']} bits**")
            else:
                st.write("- Uncoded Direct Transmission (N=1, K=1, Rate=1.0)")

        with col_c2:
            st.markdown("**Physical Channel Distortion:**")
            st.write(f"- Channel Model: **{channel_choice}**")
            ch_info = sim_result['channel_info']
            if ch_info['mode'] == 'awgn':
                st.write(f"- Wired Link $E_b/N_0$: **{ch_info['eb_no_db']:.1f} dB**")
                st.write(f"- Gaussian Noise Std Dev $\\sigma$: **{ch_info['sigma']:.4f}**")
            elif ch_info['mode'] == 'bsc':
                st.write(f"- Bit-Flip Transition Probability $p$: **{ch_info['p']:.4f}**")
            else:
                st.write("- Ideal Lossless: Thermal noise $\\sigma = 0$, Perturbation $p = 0$.")

    with st.expander("Stage 5 & 6: Iterative Decoding & Final Reconstructed Payload", expanded=True):
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            st.markdown("**Original Payload Excerpt:**")
            st.code(sim_result['original_input_excerpt'], language="text")

        with col_d2:
            st.markdown("**Reconstructed Payload Excerpt:**")
            st.code(sim_result['reconstructed_output_excerpt'], language="text")

        st.caption(f"Total Simulation Execution Time: {sim_elapsed_ms:.2f} ms")


# -----------------------------------------------------------------------------
# TAB 2: Empirical Performance Curves (Monte Carlo Benchmarks)
# -----------------------------------------------------------------------------
with tab_curves:
    st.subheader("📈 Verified Empirical Performance Curves (Monte Carlo Sweeps)")
    st.markdown("""
    These curves were generated by Monte Carlo sweeps across **281,600 coded bits per condition**
    and validated against analytical Shannon and BPSK theoretical limits.
    """)

    curve_type = st.radio(
        "Select Figure View",
        [
            "AWGN BER Waterfall (Eb/N0 Sweep: Uncoded vs Hamming vs Polar vs LDPC)",
            "BSC Bit-Flip Suppression (p Sweep: Error Thresholds)",
            "Pre-FEC vs. Post-FEC Waterfall Behavior",
            "Saturated Source Compression vs. Entropy Tradeoff"
        ],
        horizontal=True
    )

    plot_dir = os.path.join(APP_DIR, "results", "plots")
    csv_dir = os.path.join(APP_DIR, "results", "csv")

    if "AWGN" in curve_type:
        fig_path = os.path.join(plot_dir, "fig1_awgn_ber_curves.png")
        csv_path = os.path.join(csv_dir, "awgn_ber_comparison.csv")
        st.image(fig_path, caption="Fig. 1: Bit Error Rate (BER) vs Eb/N0 over Baseband Wired AWGN Link (IEEE 802.3an LDPC vs Polar vs Hamming)", use_container_width=True)
        if os.path.exists(csv_path):
            df_awgn = pd.read_csv(csv_path)
            with st.expander("View Empirical AWGN Measurement Data (CSV)"):
                st.dataframe(df_awgn, use_container_width=True)

    elif "BSC" in curve_type:
        fig_path = os.path.join(plot_dir, "fig2_bsc_ber_curves.png")
        csv_path = os.path.join(csv_dir, "bsc_ber_comparison.csv")
        st.image(fig_path, caption="Fig. 2: Post-Decoding Bit Error Rate vs Channel Bit-Flip Probability p over Binary Symmetric Channel", use_container_width=True)
        if os.path.exists(csv_path):
            df_bsc = pd.read_csv(csv_path)
            with st.expander("View Empirical BSC Measurement Data (CSV)"):
                st.dataframe(df_bsc, use_container_width=True)

    elif "Pre-FEC" in curve_type:
        fig_path = os.path.join(plot_dir, "fig3_pre_vs_post_fec.png")
        st.image(fig_path, caption="Fig. 3: Pre-FEC vs Post-FEC BER Waterfall Behavior Demonstrating Sharp Coding Gains", use_container_width=True)

    else:
        fig_path = os.path.join(plot_dir, "fig4_source_compression_tradeoff.png")
        csv_path = os.path.join(csv_dir, "source_compression_study.csv")
        st.image(fig_path, caption="Fig. 4: Adaptive LZW Compression Efficiency vs Saturated Source Empirical Entropy", use_container_width=True)
        if os.path.exists(csv_path):
            df_src = pd.read_csv(csv_path)
            with st.expander("View Source Coding Empirical Data (CSV)"):
                st.dataframe(df_src, use_container_width=True)


# -----------------------------------------------------------------------------
# TAB 3: System Architecture & Mathematical Formulation
# -----------------------------------------------------------------------------
with tab_arch:
    st.subheader("📐 System Architecture & Information Theoretic Principles")

    arch_fig = os.path.join(APP_DIR, "results", "plots", "fig5_pipeline_architecture.png")
    if os.path.exists(arch_fig):
        st.image(arch_fig, caption="System Architecture Pipeline Diagram", use_container_width=True)

    st.markdown(r"""
    ### 1. Assignment Topic & Teacher Instruction Resolution
    * **Student Assignment:** Registration number ending in odd digit `1` &rarr; **Wired Network Track**.
    * **Saturated Source:** Continuously generates information packets without idle gaps.
    * **Universal Source Coding:** Modern Lempel-Ziv-Welch (LZW) adaptive dictionary coding replaces obsolete static Huffman/Shannon-Fano codes.
    * **Lossless vs Physical Channel Reconciliation:**
      * In Shannon theory, an ideal lossless channel exhibits zero equivocation ($H(X|Y)=0 \implies \text{BER}=0$).
      * Physical wireline transmission lines (such as **10GBASE-T Ethernet IEEE 802.3an** copper twisted-pair and backplanes) suffer from high-frequency attenuation, thermal noise, and crosstalk ($10^{-3}$ to $10^{-1}$ raw slicer errors).
      * Modern channel coding (LDPC / Polar) transforms the noisy physical link into a **logically lossless channel** ($\text{post-FEC BER} < 10^{-12}$).
      * This simulation supports both: an ideal lossless channel baseline verifying exact 100% data recovery, alongside realistic AWGN and BSC models exhibiting waterfall error correction.

    ---

    ### 2. Key Mathematical Formulations
    * **Shannon Empirical Entropy:**
      $$H(X) = -\\sum_{i} P(x_i) \\log_2 P(x_i) \\quad \\text{[bits/symbol]}$$
    * **LDPC Parity-Check Orthogonality:**
      $$(G \\cdot H^T) \\pmod 2 = 0_{k \\times m}$$
    * **AWGN Theoretical Uncoded BPSK Bit Error Rate:**
      $$P_b = Q\\left(\\sqrt{2 \\frac{E_b}{N_0}}\\right) = \\frac{1}{2} \\text{erfc}\\left(\\sqrt{\\frac{E_b}{N_0}}\\right)$$
    * **AWGN Noise Standard Deviation with FEC Code Rate $R$:**
      $$\\sigma = \\frac{1}{\\sqrt{2 R \\cdot 10^{(E_b/N_0)/10}}}$$
    * **Log-Domain Belief Propagation Check-to-Variable Update:**
      $$r_{mn} = 2 \\tanh^{-1}\\left( \\prod_{n' \\in V(m) \\setminus n} \\tanh\\left(\\frac{q_{mn'}}{2}\\right) \\right)$$
    * **Statistical Rule of Three (for 0 observed bit errors in $N$ samples):**
      $$\\text{BER}_{95\\%} < \\frac{3}{N}$$
    """)


# -----------------------------------------------------------------------------
# TAB 4: Downloads & Verified Academic Artifacts
# -----------------------------------------------------------------------------
with tab_downloads:
    st.subheader("📥 Downloads & Verified Academic Deliverables")

    col_p1, col_p2 = st.columns([1, 1])

    with col_p1:
        st.markdown("### 📄 IEEE Conference Research Paper (PDF)")
        st.markdown("""
        * **Paper Title:** *Performance Analysis and Implementation of Modern Channel Coding for High-Speed Saturated Wired Communication Systems*
        * **Author:** Aravind (Registration Number: 23BCE7551)
        * **Institution:** School of Computer Science and Engineering, VIT-AP University
        * **Format:** IEEE Conference 2-Column Standard (Compiled with ReportLab)
        * **Status:** Verified, compiled, and matches experimental curves.
        """)

        paper_pdf_path = os.path.join(APP_DIR, "paper", "IEEE_Conference_Paper_23BCE7551.pdf")
        if os.path.exists(paper_pdf_path):
            with open(paper_pdf_path, "rb") as f:
                pdf_bytes = f.read()
            st.download_button(
                label="📥 Download 6-Page IEEE Conference Paper (PDF)",
                data=pdf_bytes,
                file_name="IEEE_Conference_Paper_23BCE7551_Aravind.pdf",
                mime="application/pdf"
            )
        else:
            st.error("Paper PDF file not found at paper/IEEE_Conference_Paper_23BCE7551.pdf")

    with col_p2:
        st.markdown("### 📊 Empirical CSV Measurement Datasets")
        st.markdown("Download raw empirical Monte Carlo measurement datasets:")

        for fname, label in [
            ("awgn_ber_comparison.csv", "AWGN Eb/N0 Sweep (Uncoded, Hamming, Polar, LDPC)"),
            ("bsc_ber_comparison.csv", "Binary Symmetric Channel Bit-Flip Sweep"),
            ("source_compression_study.csv", "Saturated Source Compression Study")
        ]:
            cpath = os.path.join(APP_DIR, "results", "csv", fname)
            if os.path.exists(cpath):
                with open(cpath, "rb") as f:
                    csv_data = f.read()
                st.download_button(
                    label=f"📥 Download {fname} ({label})",
                    data=csv_data,
                    file_name=fname,
                    mime="text/csv",
                    key=f"dl_{fname}"
                )

    st.markdown("---")
    st.markdown("### 📋 Audit & Test Report")
    report_path = os.path.join(APP_DIR, "PROJECT_TEST_REPORT.md")
    if os.path.exists(report_path):
        with open(report_path, "r", encoding="utf-8") as f:
            rep_text = f.read()
        st.download_button(
            label="📥 Download Comprehensive Audit & Test Report (PROJECT_TEST_REPORT.md)",
            data=rep_text,
            file_name="PROJECT_TEST_REPORT.md",
            mime="text/markdown"
        )
