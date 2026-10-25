"""
Streamlit Web Application: Wireless Communication System Simulation.
Information Theory, Source Coding, LDPC Error Correction and BER Analysis.
Provides 3 Distinct Modes:
  Mode A: Live Wireless Message Transmission (TCP over Wi-Fi with ACK)
  Mode B: Continuous Wireless Source Streamer (Bounded Queue & Backpressure)
  Mode C: Wireless Physical Channel Simulation (BPSK, AWGN, Soft Demod, LDPC Decoding, BER vs SNR)
"""

import os
import sys
import time
import math
import io
import json
import socket
import numpy as np
import pandas as pd
import streamlit as st
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Ensure local workspace is importable
APP_DIR = os.path.dirname(os.path.abspath(__file__))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

from src.source_coding import SaturatedSource, BinaryConverter, LZWCodec, ArithmeticCodec
from src.channel_coding import LDPCCodec, PolarCodec, HammingCodec
from src.channel_model import WiredChannel, ChannelAnalyzer
from src.metrics import PerformanceEvaluator
from src.wireless import (
    WirelessFrame,
    FrameType,
    StatusCode,
    WirelessSender,
    WirelessReceiver,
    ContinuousSourceStreamer,
    WirelessPhysicalChannel,
    WirelessSimulationPipeline
)

# -----------------------------------------------------------------------------
# Page Configuration & Professional Technical Styling
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Wireless Communication System Simulation",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Theme CSS (Navy, Indigo, Cyan, Lavender/Blue-Gray surfaces, Crisp contrast)
st.markdown("""
<style>
    .main-header {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        background: linear-gradient(135deg, #002B49 0%, #0B3C65 50%, #164E78 100%);
        color: white;
        padding: 24px 30px;
        border-radius: 12px;
        margin-bottom: 24px;
        box-shadow: 0 4px 16px rgba(0, 43, 73, 0.2);
    }
    .badge {
        display: inline-block;
        padding: 5px 12px;
        border-radius: 6px;
        font-size: 13px;
        font-weight: 600;
        margin-right: 8px;
        margin-top: 4px;
    }
    .badge-primary { background: #e0f2fe; color: #0369a1; border: 1px solid #bae6fd; }
    .badge-accent { background: #fef3c7; color: #b45309; border: 1px solid #fde68a; }
    .badge-success { background: #dcfce7; color: #15803d; border: 1px solid #bbf7d0; }
    .badge-info { background: #ede9fe; color: #6d28d9; border: 1px solid #ddd6fe; }
    .metric-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 16px;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    .metric-value {
        font-size: 26px;
        font-weight: 700;
        color: #0f172a;
    }
    .metric-label {
        font-size: 12px;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-top: 4px;
    }
    .stButton>button {
        background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%);
        color: white;
        font-weight: 600;
        border-radius: 8px;
        padding: 10px 20px;
        border: none;
        box-shadow: 0 3px 6px rgba(2, 132, 199, 0.25);
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #0369a1 0%, #075985 100%);
        color: white;
    }
    .status-pill {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 9999px;
        font-size: 12px;
        font-weight: 600;
    }
    .status-ok { background: #dcfce7; color: #166534; }
    .status-err { background: #fee2e2; color: #991b1b; }
    .status-warn { background: #fef3c7; color: #92400e; }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Top Banner
# -----------------------------------------------------------------------------
st.markdown("""
<div class="main-header">
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
        <div>
            <h1 style="margin: 0; font-size: 28px; font-weight: 700; color: white; letter-spacing: -0.5px;">
                Wireless Communication System Simulation
            </h1>
            <p style="margin: 6px 0 0 0; font-size: 15px; color: #cbd5e1;">
                Information Theory, Source Coding, LDPC Error Correction and BER Analysis
            </p>
        </div>
        <div style="margin-top: 10px;">
            <span class="badge badge-primary">Mode: Wi-Fi Sockets & Physical Simulation</span>
            <span class="badge badge-info">Source: Arithmetic / LZW</span>
            <span class="badge badge-accent">FEC: IEEE 802.3an LDPC (64, 32)</span>
            <span class="badge badge-success">Assignment: Wired Network</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# Persistent Session State Initialization
# -----------------------------------------------------------------------------
if "sender" not in st.session_state:
    st.session_state.sender = WirelessSender()

if "receiver" not in st.session_state:
    st.session_state.receiver = WirelessReceiver(host="0.0.0.0", port=8550)

if "streamer" not in st.session_state:
    st.session_state.streamer = ContinuousSourceStreamer(sender=st.session_state.sender)

if "sim_pipeline" not in st.session_state:
    st.session_state.sim_pipeline = WirelessSimulationPipeline(seed=42)

if "last_sim_result" not in st.session_state:
    st.session_state.last_sim_result = None

if "sweep_data" not in st.session_state:
    st.session_state.sweep_data = None


# Helper to get local private IP
def get_local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


local_private_ip = get_local_ip()


# -----------------------------------------------------------------------------
# Sidebar: System Status & Networking Guide
# -----------------------------------------------------------------------------
st.sidebar.header("📡 Network & System Status")

rx_status = "🟢 Active (Listening)" if st.session_state.receiver.is_running() else "⚪ Stopped"
st.sidebar.markdown(f"**Receiver Daemon:** {rx_status}")
st.sidebar.markdown(f"**Local IP (Wi-Fi):** `{local_private_ip}`")
st.sidebar.markdown(f"**Default Port:** `8550`")

st.sidebar.markdown("---")
st.sidebar.subheader("💡 Wi-Fi Setup Instructions")
st.sidebar.markdown("""
* **Same PC Test:** Connect to `127.0.0.1:8550`.
* **Two Computers:**
  1. Both machines connect to the same Wi-Fi.
  2. On receiver PC, run app and click **Start Listening**.
  3. Find receiver IP (e.g. `192.168.1.X`).
  4. On sender PC, enter receiver's IP in TAB A.
  5. Ensure Windows Firewall allows port `8550`.
""")


# -----------------------------------------------------------------------------
# Five Required Tabs
# -----------------------------------------------------------------------------
tab_sender, tab_receiver, tab_stream, tab_sim, tab_analysis = st.tabs([
    "📤 TAB A — Live Message Sender",
    "📥 TAB B — Live Receiver",
    "🔄 TAB C — Continuous Source",
    "🔬 TAB D — Wireless Channel Simulation",
    "📊 TAB E — Coding Analysis"
])


# =============================================================================
# TAB A: Live Message Sender
# =============================================================================
with tab_sender:
    st.subheader("📤 Mode A: Live Wireless Message Transmission")
    st.markdown("""
    Enter a message to encode using **Lossless Source Coding** (Arithmetic or LZW) and **LDPC Forward Error Correction**,
    frame with a **CRC32 Checksum**, and transmit across the local Wi-Fi network over a TCP stream socket.
    The sender waits for the receiver to verify and acknowledge the matching sequence number.
    """)

    col_cfg1, col_cfg2, col_cfg3 = st.columns([2, 1, 1])
    with col_cfg1:
        dest_host = st.text_input("Receiver Host / IPv4 Address", value="127.0.0.1", help="Enter 127.0.0.1 for local test or the receiver's private Wi-Fi IP.")
    with col_cfg2:
        dest_port = st.number_input("Receiver Port", value=8550, step=1)
    with col_cfg3:
        timeout_s = st.number_input("Socket Timeout (s)", value=3.0, step=0.5)

    col_opt1, col_opt2 = st.columns([1, 1])
    with col_opt1:
        use_source = st.checkbox("Enable Lossless Source Coding", value=True)
        source_codec_choice = st.radio("Source Codec Algorithm", ["Arithmetic Coding", "LZW Codec"], index=0, horizontal=True, disabled=not use_source)
        selected_codec = "arithmetic" if "Arithmetic" in source_codec_choice else "lzw"
    with col_opt2:
        use_ldpc_fec = st.checkbox("Enable IEEE 802.3an LDPC Channel Coding (N=64, K=32, R=0.5)", value=True)
        st.caption("Pads and segments bitstream into systematic (64, 32) LDPC blocks.")

    # Preset messages
    preset = st.selectbox(
        "Choose Payload Preset or Enter Custom Message",
        [
            "Custom Message",
            "Hello, this is my wireless ITC project!",
            "NODE-VITAP:SENSOR_TEMP=32.4C:VOLT=3.3V:STATUS=OK;PAYLOAD_DATA_FRAME_WIRELESS_STREAM_PACKET;",
            "Unicode & Math Test: 📡 Frequency=2.4GHz | SNR=8.5dB | α=0.05 | Greek: Ω, Hindi: नमस्ते, 日本語: 無線"
        ]
    )

    if preset == "Custom Message":
        msg_input = st.text_area("Message Input (UTF-8)", value="Hello, this is my wireless ITC project!", height=100)
    else:
        msg_input = st.text_area("Message Input (UTF-8)", value=preset, height=100)

    send_btn = st.button("🚀 Send Wireless Message")

    if send_btn:
        if not msg_input:
            st.error("Please enter a message to transmit.")
        else:
            with st.spinner(f"Encoding and transmitting over network to {dest_host}:{dest_port}..."):
                report = st.session_state.sender.send_message(
                    message=msg_input,
                    host=dest_host,
                    port=int(dest_port),
                    use_source_coding=use_source,
                    source_codec=selected_codec,
                    use_ldpc=use_ldpc_fec,
                    timeout=float(timeout_s)
                )

            if report['ack_received'] and report['ack_status'] == StatusCode.OK.name:
                st.success(f"✅ **Message #{report['seq_num']} Successfully Delivered & Reconstructed!** (Receiver ACK Verified in {report['round_trip_ms']:.1f} ms)")
            else:
                st.error(f"❌ **Delivery Incomplete:** {report['status']}. Details: {report['error_message']}")

            # Metrics row
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("Sequence #", f"#{report['seq_num']}")
            c2.metric("Original Size", f"{report['orig_size_bytes']} B")
            c3.metric("Compressed Size", f"{report['src_size_bytes']} B", f"{report['compression_ratio']:.2f}x")
            c4.metric("Coded Frame Size", f"{report['coded_size_bytes']} B")
            c5.metric("Round-Trip RTT", f"{report['round_trip_ms']:.1f} ms")

    # History Table
    st.markdown("### 📋 Sender Transmission History")
    history = st.session_state.sender.history
    if history:
        df_hist = pd.DataFrame(history)
        cols_to_show = ['seq_num', 'timestamp', 'orig_size_bytes', 'src_size_bytes', 'coded_size_bytes', 'compression_ratio', 'status', 'ack_status', 'round_trip_ms']
        st.dataframe(df_hist[cols_to_show].iloc[::-1], use_container_width=True)
        if st.button("🗑️ Clear Sender History"):
            st.session_state.sender.clear_history()
            st.rerun()
    else:
        st.info("No transmission history yet in this session.")


# =============================================================================
# TAB B: Live Receiver
# =============================================================================
with tab_receiver:
    st.subheader("📥 Mode A / B: Live Wireless Receiver")
    st.markdown("""
    The receiver listens on a local network interface, receives incoming binary frames,
    performs **CRC32 Checksum Verification**, executes **LDPC Syndrome Slicing / Decoding**,
    and **Decompresses Source Payload** to reconstruct the exact original text.
    """)

    col_rx1, col_rx2, col_rx3, col_rx4 = st.columns([2, 1, 1, 1])
    with col_rx1:
        rx_host = st.text_input("Listen Interface", value="0.0.0.0", help="0.0.0.0 binds to all local Wi-Fi and Ethernet interfaces.")
    with col_rx2:
        rx_port = st.number_input("Listen Port", value=8550, step=1, key="rx_port_in")
    with col_rx3:
        st.write("")
        st.write("")
        if not st.session_state.receiver.is_running():
            if st.button("▶️ Start Listening"):
                try:
                    st.session_state.receiver.start(host=rx_host, port=int(rx_port))
                    st.success(f"Receiver listening on {rx_host}:{rx_port}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to bind: {e}")
        else:
            if st.button("⏹️ Stop Listening"):
                st.session_state.receiver.stop()
                st.warning("Receiver stopped.")
                st.rerun()
    with col_rx4:
        st.write("")
        st.write("")
        if st.button("🔄 Refresh View"):
            st.rerun()

    # Receiver Status Banner
    if st.session_state.receiver.is_running():
        st.markdown(f'<div class="status-pill status-ok">🟢 LISTENING on {rx_host}:{rx_port} (Ready for incoming Wi-Fi frames)</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="status-pill status-warn">⚪ STOPPED (Click "Start Listening" to accept wireless transmissions)</div>', unsafe_allow_html=True)

    # Receiver Metrics
    r_hist = st.session_state.receiver.get_history()
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Frames Received", f"{st.session_state.receiver.total_received}")
    m2.metric("Decoded Successfully", f"{st.session_state.receiver.total_decoded_ok}")
    m3.metric("Checksum / Decode Errors", f"{st.session_state.receiver.total_errors}")

    st.markdown("### 📬 Received Messages Log")
    if r_hist:
        for item in reversed(r_hist[-15:]):
            is_ok = (item['status_code'] == StatusCode.OK.name)
            border_col = "#22c55e" if is_ok else "#ef4444"
            st.markdown(f"""
            <div style="border-left: 4px solid {border_col}; padding: 12px 16px; background: #f8fafc; border-radius: 6px; margin-bottom: 12px;">
                <div style="display: flex; justify-content: space-between;">
                    <span style="font-weight: 700; color: #0f172a;">Message Sequence #{item['seq_num']}</span>
                    <span style="font-size: 13px; color: #64748b;">{item['timestamp']} &nbsp;|&nbsp; From: {item['sender']}</span>
                </div>
                <div style="margin-top: 6px; font-size: 14px;">
                    <strong>Actual Reconstructed Text:</strong>
                    <div style="background: white; border: 1px solid #e2e8f0; padding: 8px 12px; border-radius: 6px; margin-top: 4px; font-family: monospace;">
                        {item['reconstructed_text']}
                    </div>
                </div>
                <div style="margin-top: 6px; font-size: 12px; color: #475569;">
                    Status: <strong>{item['status']}</strong> &nbsp;|&nbsp;
                    Payload: {item['orig_size']} B &nbsp;|&nbsp;
                    CRC32: {'Verified ✅' if item['checksum_verified'] else 'Failed ❌'} &nbsp;|&nbsp;
                    Processing: {item['processing_duration_ms']:.2f} ms
                </div>
            </div>
            """, unsafe_allow_html=True)

        if st.button("🗑️ Clear Received Messages"):
            st.session_state.receiver.clear_history()
            st.rerun()
    else:
        st.info("No incoming messages received yet. Send a message from TAB A or continuous stream from TAB C.")


# =============================================================================
# TAB C: Continuous Source
# =============================================================================
with tab_stream:
    st.subheader("🔄 Mode B: Continuous Wireless Source Streamer")
    st.markdown("""
    Generates successive information frames and streams them continuously to the receiver over Wi-Fi/TCP.
    Employs a **bounded FIFO queue** and backpressure monitoring to ensure safe, deterministic execution without memory leaks.
    """)

    col_s1, col_s2, col_s3 = st.columns([2, 1, 1])
    with col_s1:
        st_dest_host = st.text_input("Destination Host", value="127.0.0.1", key="st_host")
    with col_s2:
        st_dest_port = st.number_input("Destination Port", value=8550, step=1, key="st_port")
    with col_s3:
        st_interval = st.slider("Transmission Interval (s)", min_value=0.1, max_value=2.0, value=0.5, step=0.1)

    col_s4, col_s5 = st.columns(2)
    with col_s4:
        st_src_type = st.selectbox("Information Source Type", ["telemetry", "random_bits"], format_func=lambda x: "Structured Saturated Telemetry" if x == "telemetry" else "Uniform Pseudo-Random Bits")
    with col_s5:
        st_frame_sz = st.select_slider("Frame Payload Size (Bytes)", options=[32, 64, 128, 256, 512], value=128)

    # Streamer Controls
    streamer = st.session_state.streamer
    is_streaming = streamer.is_running()

    col_b1, col_b2, col_b3 = st.columns([1, 1, 2])
    with col_b1:
        if not is_streaming:
            if st.button("▶️ Start Streaming"):
                streamer.start(
                    dest_host=st_dest_host,
                    dest_port=int(st_dest_port),
                    source_type=st_src_type,
                    frame_size=int(st_frame_sz),
                    interval_sec=float(st_interval),
                    use_source_coding=True,
                    source_codec="arithmetic",
                    use_ldpc=True
                )
                st.rerun()
        else:
            if st.button("⏹️ Stop Streaming"):
                streamer.stop()
                st.rerun()
    with col_b2:
        if st.button("🔄 Refresh Stream Stats"):
            st.rerun()

    # Streaming Metrics
    m = streamer.get_metrics()
    c_m1, c_m2, c_m3, c_m4, c_m5 = st.columns(5)
    c_m1.metric("Status", "🟢 STREAMING" if m['is_running'] else "⚪ IDLE")
    c_m2.metric("Generated", f"{m['frames_generated']}")
    c_m3.metric("Transmitted (ACK OK)", f"{m['frames_acknowledged']}")
    c_m4.metric("Backpressure Dropped", f"{m['frames_dropped_backpressure']}")
    c_m5.metric("Throughput", f"{m['throughput_bps']:.0f} bps", f"{m['throughput_fps']:.1f} fps")

    # Recent frame stream table
    st.markdown("### 📜 Real-time Stream Frame Log (Last 20 Frames)")
    if m['recent_frames']:
        df_recent = pd.DataFrame(m['recent_frames'])
        st.dataframe(df_recent.iloc[::-1], use_container_width=True)
    else:
        st.info("Continuous source is idle. Click 'Start Streaming' above to initiate successive frame transmission.")


# =============================================================================
# TAB D: Wireless Channel Simulation
# =============================================================================
with tab_sim:
    st.subheader("🔬 Mode C: Wireless Physical-Layer Channel Simulation")
    st.markdown("""
    > **Architectural Note:** This mode simulates the **raw physical wireless channel** using baseband **BPSK modulation**,
    > **AWGN thermal noise**, and **Iterative LDPC Log-Domain Belief Propagation decoding**.
    > This physical-layer noise injection is completely separated from the reliable TCP socket transport used in Modes A & B.
    """)

    col_sim1, col_sim2, col_sim3 = st.columns([1, 1, 1])
    with col_sim1:
        sim_snr = st.slider("Channel SNR (Eb/N0 in dB)", min_value=0.0, max_value=10.0, value=4.0, step=0.5)
    with col_sim2:
        sim_codec = st.selectbox("Source Codec", ["Arithmetic Coding", "LZW Codec"], index=0, key="sim_src_codec")
        src_name = "arithmetic" if "Arithmetic" in sim_codec else "lzw"
    with col_sim3:
        sim_iters = st.slider("LDPC Max Iterations", min_value=5, max_value=50, value=25, step=5)

    sim_payload = st.text_input(
        "Payload String for Simulation",
        value="NODE-VITAP-WIRELESS:TEMP=31.8C:VOLT=3.3V:STATUS=OK;PAYLOAD_DATA_FRAME_WIRELESS_STREAM_PACKET;"
    )

    if st.button("🚀 Run Wireless Channel Simulation"):
        with st.spinner("Modulating symbols and simulating iterative belief-propagation decoding..."):
            res = st.session_state.sim_pipeline.run_simulation(
                message=sim_payload,
                eb_no_db=float(sim_snr),
                source_codec=src_name,
                ldpc_max_iter=int(sim_iters)
            )
            st.session_state.last_sim_result = res

    # Display Simulation Result
    res = st.session_state.last_sim_result
    if res is not None:
        if res['exact_recovery']:
            st.success(f"✅ **100% EXACT BIT-FOR-BIT RECONSTRUCTION VERIFIED!** (Zero post-FEC residual errors out of {res['info_bits']} information bits)")
        else:
            st.warning(f"⚠️ **PARTIAL ERROR SUPPRESSION (Waterfall Region at {res['eb_no_db']:.1f} dB):** Suppressed errors by {res['error_suppression_gain']:.1f}x ({res['pre_fec_errors']} pre-FEC errors reduced to {res['post_fec_errors']} post-FEC errors). Exact recovery requires Eb/N0 >= 7.0 dB.")

        # Metric cards
        sm1, sm2, sm3, sm4 = st.columns(4)
        sm1.metric("Pre-FEC Slicer BER", f"{res['pre_fec_ber']:.3e}", f"{res['pre_fec_errors']} errors")
        sm2.metric("Post-FEC Residual BER", f"{res['post_fec_ber']:.3e}", f"{res['post_fec_errors']} errors")
        sm3.metric("Error Suppression Gain", f"{res['error_suppression_gain']:.1f}x" if res['error_suppression_gain'] < 1e6 else "Infinite")
        sm4.metric("Frame Error Rate (FER)", f"{res['fer']:.3f}", f"{res['frame_errors']} / {res['num_ldpc_blocks']} blocks")

        # Coded vs Uncoded comparison table
        st.markdown("#### ⚖️ Coded vs Uncoded Performance Comparison")
        comp_data = {
            "Metric": ["Channel Noise σ", "Information Bits Tested", "Observed Bit Errors", "Bit Error Rate (BER)", "Exact Recovery", "Reconstructed Excerpt"],
            "Coded (IEEE 802.3an LDPC Rate-1/2)": [
                f"{res['noise_sigma_coded']:.4f}",
                f"{res['info_bits']} bits",
                f"{res['post_fec_errors']}",
                f"{res['post_fec_ber']:.4e}",
                "True ✅" if res['exact_recovery'] else "False ❌",
                f'"{res["reconstructed_text"][:50]}..."'
            ],
            "Uncoded Baseline (Rate 1.0)": [
                f"{res['noise_sigma_uncoded']:.4f}",
                f"{res['info_bits']} bits",
                f"{res['uncoded_errors']}",
                f"{res['uncoded_ber']:.4e}",
                "True ✅" if res['uncoded_exact'] else "False ❌",
                f'"{res["uncoded_text"][:50]}..."'
            ],
            "Theoretical BPSK Bound": [
                "-",
                "-",
                "-",
                f"{res['theory_bpsk_ber']:.4e}",
                "-",
                "-"
            ]
        }
        st.table(pd.DataFrame(comp_data))

    # SNR Sweep Section
    st.markdown("---")
    st.markdown("### 📈 Multi-Trial BER vs SNR Waterfall Curve Generator")
    col_sw1, col_sw2 = st.columns([1, 3])
    with col_sw1:
        sweep_trials = st.slider("Trials per SNR Point", min_value=2, max_value=10, value=4)
        sweep_bits = st.select_slider("Bits per Point", options=[6400, 12800, 25600], value=12800)
        run_sweep_btn = st.button("📊 Run SNR Monte Carlo Sweep")

    with col_sw2:
        if run_sweep_btn or st.session_state.sweep_data is not None:
            if run_sweep_btn:
                with st.spinner("Executing Monte Carlo BER sweep (0 to 10 dB)..."):
                    records = st.session_state.sim_pipeline.run_snr_sweep(
                        eb_no_list=[0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
                        bits_per_point=int(sweep_bits),
                        trials_per_point=int(sweep_trials)
                    )
                    st.session_state.sweep_data = pd.DataFrame(records)

            df_sweep = st.session_state.sweep_data
            fig, ax = plt.subplots(figsize=(8, 4.5), dpi=100)
            fig.patch.set_facecolor('#ffffff')
            ax.set_facecolor('#f8fafc')

            ax.semilogy(df_sweep['eb_no_db'], df_sweep['theory_bpsk_ber'], 'k--', label='Theoretical BPSK Uncoded', linewidth=1.5)
            ax.semilogy(df_sweep['eb_no_db'], df_sweep['uncoded_ber'], 'r-s', label='Simulated Uncoded BPSK', markersize=4)
            ax.semilogy(df_sweep['eb_no_db'], df_sweep['pre_fec_ber'], 'y-^', label='Pre-FEC Slicer (R=0.5)', markersize=4)
            ax.semilogy(df_sweep['eb_no_db'], np.maximum(df_sweep['ldpc_post_fec_ber'], 1e-6), 'b-o', label='LDPC (64, 32) Sum-Product', linewidth=2, markersize=5)

            ax.grid(True, which='both', linestyle=':', alpha=0.6)
            ax.set_xlabel('Eb/N0 (dB)', fontweight='bold')
            ax.set_ylabel('Bit Error Rate (BER)', fontweight='bold')
            ax.set_title('BER vs Eb/N0 Waterfall Curves in Wireless AWGN', fontweight='bold')
            ax.set_ylim([1e-6, 1.0])
            ax.legend()
            st.pyplot(fig)

            csv_bytes = df_sweep.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download SNR Sweep Measurements (CSV)",
                data=csv_bytes,
                file_name="wireless_snr_sweep_measurements.csv",
                mime="text/csv"
            )


# =============================================================================
# TAB E: Coding Analysis & Architecture
# =============================================================================
with tab_analysis:
    st.subheader("📊 Information Theory & Coding Analysis")

    col_a1, col_a2 = st.columns(2)
    with col_a1:
        st.markdown("### 🧮 1. Lossless Source Coding Comparison")
        st.markdown("""
        * **Arithmetic / Range Coding:**
          Encodes the entire message into a single fractional interval $[0, 1)$ represented with finite-precision integer registers.
          Approaches the exact Shannon entropy $H(X) = -\\sum p_i \\log_2 p_i$ without the integer-bit constraint of Huffman coding.
        * **LZW Codec (Lempel-Ziv-Welch):**
          Dictionary-based universal source coder. Replaces recurring character sequences with 12-bit tokens.
          Effective on repetitive structured streams.
        """)
        st.markdown("""
        $$\\text{Compression Ratio} = \\frac{\\text{Raw Bytes}}{\\text{Compressed Bytes}}, \\quad \\text{Space Savings} = \\left(1 - \\frac{1}{\\text{Ratio}}\\right) \\times 100\\%$$
        """)

    with col_a2:
        st.markdown("### 🛡️ 2. IEEE 802.3an LDPC Channel Coding")
        st.markdown("""
        * **Code Parameters:** Blocklength $N = 64$, Information length $K = 32$, Code Rate $R = 0.50$.
        * **Parity-Check Matrix:** $H \\in \\mathbb{F}_2^{32 \\times 64}$, satisfying $G \\cdot H^T \\equiv 0 \\pmod 2$.
        * **Decoding Algorithm:** Log-domain Sum-Product Belief Propagation on the bipartite Tanner graph:
        """)
        st.markdown("""
        $$\\tanh\\left(\\frac{r_{mn}}{2}\\right) = \\prod_{j \\in V(m) \\setminus n} \\tanh\\left(\\frac{q_{mj}}{2}\\right), \\quad q_{mn} = L_n + \\sum_{c \\in C(n) \\setminus m} r_{cn}$$
        """)

    st.markdown("---")
    st.markdown("### 📐 3. Shannon Channel Capacity vs SNR")
    st.markdown("""
    According to the Shannon-Hartley theorem, the theoretical maximum channel capacity $C$ for bandwidth $B$ over AWGN is:
    $$C = B \\log_2\\left(1 + \\text{SNR}\\right) = B \\log_2\\left(1 + \\frac{P}{N_0 B}\\right)$$
    In our Rate-1/2 coded system, error-free communication requires $R < C/B$. At $E_b/N_0 \\ge 7.0\\text{ dB}$, our LDPC codec reliably achieves 100% exact source restoration.
    """)

    st.markdown("---")
    st.markdown("### 📥 Academic Research Deliverables")
    paper_pdf = os.path.join(APP_DIR, "paper", "IEEE_Conference_Paper_23BCE7551.pdf")
    if os.path.exists(paper_pdf):
        with open(paper_pdf, "rb") as f:
            pdf_bytes = f.read()
        st.download_button(
            label="📄 Download IEEE Conference Paper (PDF)",
            data=pdf_bytes,
            file_name="IEEE_Conference_Paper_Wireless_Communication.pdf",
            mime="application/pdf"
        )
