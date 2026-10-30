# Wireless Digital Communication System Simulation
## IEEE Conference Research Paper Package

**Paper Title:**  
*Performance Analysis and Implementation of a Wireless Digital Communication System Using Source Coding, LDPC Error Correction, and Channel Simulation*

---

### Authors
1. **Aravind M** — Registration Number: `23BCE7551`
2. **Sai Chandu** — Registration Number: `23BCE20304`
3. **Rahul L** — Registration Number: `23BCE7890`

**Affiliation:**  
School of Computer Science and Engineering  
VIT-AP University, Amaravati, Andhra Pradesh, India

---

## 1. Directory Structure

```
outputs/IEEE_Wireless_Conference_Paper/
├── IEEE_Wireless_Conference_Paper.pdf     # Final compiled 6-page IEEE two-column paper (ReportLab)
├── IEEE_Wireless_Conference_Paper.docx    # Fully editable Word document (.docx) with embedded tables and figures
├── IEEE_Wireless_Conference_Paper.tex     # Complete LaTeX source (IEEEtran document class)
├── references.bib                         # 14 verified academic references in BibTeX format (all with DOIs)
├── README.md                              # This documentation file
├── generate_pdf.py                        # Python script to compile the PDF using ReportLab
├── generate_docx.py                       # Python script to generate the DOCX using python-docx
├── generate_figures.py                    # Python script to regenerate all 7 publication-grade figures (300 DPI)
├── generate_csvs.py                       # Python script to execute live simulation and export CSV benchmarks
├── figures/                               # Publication-grade vector-clear figures (300 DPI PNGs)
│   ├── fig1_overall_architecture.png      # End-to-end communication system architecture diagram
│   ├── fig2_frame_protocol_ack.png        # Binary frame format & ARQ stop-and-wait protocol diagram
│   ├── fig3_awgn_ber_waterfall.png        # Waterfall BER curves: Uncoded vs Hamming vs Polar vs LDPC
│   ├── fig4_pre_vs_post_fec.png           # Pre-FEC vs Post-FEC BER and coding gain across SNRs
│   ├── fig5_source_coding_entropy.png     # Source coding compression ratio vs message entropy
│   ├── fig6_socket_latency_overhead.png   # TCP/IP transmission RTT latency and packet framing overhead
│   └── fig7_bpsk_awgn_simulation.png      # Simulated BPSK-AWGN physical layer block diagram
└── results/                               # Empirical simulation data and benchmark CSV logs
    ├── awgn_ber_comparison.csv            # Monte Carlo AWGN channel BER across codecs (0 to 10 dB)
    ├── bsc_ber_comparison.csv             # Binary Symmetric Channel crossover vs BER
    ├── source_compression_study.csv       # Compression metrics across text corpora
    ├── wireless_multitrial_benchmark.csv  # Multi-trial statistical wireless simulation results
    └── wireless_socket_benchmark.csv      # Empirical TCP/IP socket latency and throughput measurements
```

---

## 2. Reproduction and Build Instructions

### Prerequisites
Ensure Python 3.10+ is installed along with the required scientific and document generation libraries:
```bash
pip install -r requirements.txt
pip install reportlab python-docx matplotlib numpy
```

### Step 1: Run Project Unit Tests
Verify the algorithmic correctness of the underlying communication modules:
```bash
python -m pytest tests/
```
*(68 of 69 tests pass synchronously; the 1 web test `test_streamlit_server_online` tests live HTTP connectivity to port 8501/8502 when the dashboard is running).*

### Step 2: Regenerate Raw Simulation CSV Results
Execute the empirical benchmark suite to collect physical-layer BER and TCP latency metrics:
```bash
python outputs/IEEE_Wireless_Conference_Paper/generate_csvs.py
```
This populates:
- `results/wireless_socket_benchmark.csv`
- `results/wireless_multitrial_benchmark.csv`

### Step 3: Regenerate Publication Figures (300 DPI)
Re-render all architectural flowcharts, protocol timing diagrams, and BER waterfall plots:
```bash
python outputs/IEEE_Wireless_Conference_Paper/generate_figures.py
```
This saves all 7 figures into the `figures/` directory.

### Step 4: Recompile the PDF Paper
Compile the two-column IEEE format PDF directly using ReportLab:
```bash
python outputs/IEEE_Wireless_Conference_Paper/generate_pdf.py
```
Output generated: `outputs/IEEE_Wireless_Conference_Paper/IEEE_Wireless_Conference_Paper.pdf` (6 pages, 300 DPI figures, running headers, two-pass `Page X of Y` footers, professional styling matching `paper/IEEE_Conference_Paper_23BCE7551.pdf`).

### Step 5: Regenerate the DOCX Document
Rebuild the editable Word document:
```bash
python outputs/IEEE_Wireless_Conference_Paper/generate_docx.py
```
Output generated: `outputs/IEEE_Wireless_Conference_Paper/IEEE_Wireless_Conference_Paper.docx`.

### Step 6: LaTeX Compilation (Alternative)
The LaTeX source file `IEEE_Wireless_Conference_Paper.tex` can be compiled using standard `pdflatex` or uploaded directly to [Overleaf](https://www.overleaf.com):
```bash
pdflatex IEEE_Wireless_Conference_Paper.tex
bibtex IEEE_Wireless_Conference_Paper
pdflatex IEEE_Wireless_Conference_Paper.tex
pdflatex IEEE_Wireless_Conference_Paper.tex
```

---

## 3. Key Empirical Findings Summary

| Metric / Configuration | Theoretical Uncoded | Hamming(7,4) | Polar Code | LDPC Code (SPA) |
| :--- | :---: | :---: | :---: | :---: |
| **Code Rate ($R$)** | 1.000 | 0.571 | 0.500 | 0.500 |
| **BER at $E_b/N_0 = 4.0$ dB** | $1.250 \times 10^{-2}$ | $4.210 \times 10^{-2}$ | $1.150 \times 10^{-2}$ | $7.350 \times 10^{-3}$ |
| **BER at $E_b/N_0 = 6.0$ dB** | $2.388 \times 10^{-3}$ | $8.400 \times 10^{-3}$ | $8.200 \times 10^{-4}$ | $2.100 \times 10^{-4}$ |
| **BER at $E_b/N_0 = 8.0$ dB** | $1.909 \times 10^{-4}$ | $6.200 \times 10^{-4}$ | $1.200 \times 10^{-5}$ | $< 1.17 \times 10^{-4}$ ($0$ in $25.6\text{k}$) |
| **Coding Gain @ $10^{-3}$ BER**| Baseline (0 dB) | $-1.8$ dB (Rate loss) | $+1.4$ dB | $+2.4$ dB |
| **Frame Error Rate ($8.0$ dB)**| N/A | $0.082$ | $0.004$ | $0.000$ |

### Physical Layer vs. Network Transport Distinction
1. **Mode A (TCP/IP Network Transmission):** Operates over real OS network sockets (Wi-Fi/Ethernet). TCP guarantees $100\%$ packet delivery and $0\%$ residual bit errors through kernel-level ARQ and retransmission, while CRC32 provides frame-level integrity verification.
2. **Mode C (Physical-Layer AWGN Simulation):** Strictly isolates the wireless propagation channel using baseband BPSK mapping, additive Gaussian noise ($\sigma = 1/\sqrt{2 R \cdot 10^{SNR/10}}$), log-likelihood ratio (LLR) computation, and iterative Belief Propagation decoding without network retransmission.
3. **Statistical Rule of Three:** Observing zero bit errors over $N = 25,600$ transmitted bits at $E_b/N_0 \ge 8.0\text{ dB}$ establishes a $95\%$ confidence upper bound:
   $$\text{BER}_{95\%} < \frac{3}{25,600} \approx 1.17 \times 10^{-4}$$
   rather than implying that the true BER is identically zero.
