# IEEE Research Paper: Wireless Digital Communication System Simulation

**Paper Title:** Wireless Digital Communication System Simulation Using Source Coding, LDPC Error Correction, and TCP/IP Networking  
**Authors:**  
* **Aravind M** (Registration No.: 23BCE7551)  
* **Sai Chandu** (Registration No.: 23BCE20304)  
* **Rahul L** (Registration No.: 23BCE7890)  

**Department & Institution:**  
School of Computer Science and Engineering  
VIT-AP University, Amaravati, Andhra Pradesh, India  

---

## 1. Directory Structure

```text
outputs/IEEE_Wireless_Communication_Paper/
├── IEEE_Wireless_Communication_Paper.pdf      # Final compiled IEEE conference paper (PDF)
├── IEEE_Wireless_Communication_Paper.docx     # Editable version in Microsoft Word format (DOCX)
├── IEEE_Wireless_Communication_Paper.tex      # Complete IEEEtran-compliant LaTeX source
├── references.bib                             # BibTeX bibliography with 12 verified IEEE citations
├── README.md                                  # Reproduction & build documentation (this file)
└── figures/                                   # High-resolution (300 DPI) publication-grade figures
    ├── fig1_overall_architecture.png          # System architecture (Tx, Transport, Rx)
    ├── fig2_frame_protocol_ack.png            # 36-Byte wire frame header & TCP ACK flow
    ├── fig3_awgn_ber_waterfall.png            # Measured BER vs. Eb/N0 in AWGN (25.6k bits/pt)
    ├── fig4_pre_vs_post_fec.png               # Pre-FEC vs. Post-FEC error suppression & gain
    ├── fig5_source_coding_entropy.png         # Empirical entropy vs. compression ratio trade-off
    └── fig6_socket_latency_overhead.png       # Live socket frame size & round-trip latency
```

---

## 2. Deliverables Summary

1. **`IEEE_Wireless_Communication_Paper.pdf`**:
   * Professional IEEE conference format compiled via ReportLab.
   * Standard 2-column layout, two-pass running header and footer (`Page X of Y`).
   * Explicitly includes all three authors and their registration numbers with no email addresses.
   * Includes all 8 numbered sections, mathematical equations, Tables I-III, and Figures 1-6.
   * 12 verifiable, genuine academic references with DOI citations.

2. **`IEEE_Wireless_Communication_Paper.docx`**:
   * Editable Microsoft Word document generated via `python-docx`.
   * Standard IEEE 2-column body with continuous section break.
   * Embedded high-resolution figures, formatted tables with background shading, and styled equations.

3. **`IEEE_Wireless_Communication_Paper.tex`**:
   * Standard LaTeX conference paper formatted for `IEEEtran.cls`.
   * Full citations matching `references.bib`.

4. **`references.bib`**:
   * 12 genuine academic citations (Shannon 1948, Gallager 1962, MacKay & Neal 1996, Arıkan 2009, Welch 1984, Rissanen & Langdon 1979, Witten et al. 1987, IEEE Std 802.3an-2006, Peterson & Brown 1961, Postel RFC 793, Hamming 1950, Proakis & Salehi 2008).

---

## 3. How to Rebuild the Paper and Figures

From the root project directory (`C:\Users\saamsung\OneDrive\Desktop\ITC project`):

### Step 1: Re-generate All Figures
```powershell
python outputs/generate_figures.py
```
This updates all 6 high-resolution figures in `outputs/IEEE_Wireless_Communication_Paper/figures/`.

### Step 2: Re-compile the PDF Document
```powershell
python outputs/generate_pdf.py
```
Compiles `outputs/IEEE_Wireless_Communication_Paper/IEEE_Wireless_Communication_Paper.pdf`.

### Step 3: Re-compile the DOCX Document
```powershell
python outputs/generate_docx.py
```
Compiles `outputs/IEEE_Wireless_Communication_Paper/IEEE_Wireless_Communication_Paper.docx`.

### Step 4 (Optional): Compile LaTeX via pdflatex
If a TeX distribution (e.g., TeX Live or MiKTeX) is installed:
```powershell
cd outputs/IEEE_Wireless_Communication_Paper
pdflatex IEEE_Wireless_Communication_Paper.tex
bibtex IEEE_Wireless_Communication_Paper
pdflatex IEEE_Wireless_Communication_Paper.tex
pdflatex IEEE_Wireless_Communication_Paper.tex
```

---

## 4. Verification and Empirical Source of Truth

The paper content and results are directly derived from the codebase and empirical measurements:

* **Source Code Modules:**
  * `src/source_coding/arithmetic_codec.py`: Finite-precision 32-bit register Arithmetic coder.
  * `src/source_coding/lzw_codec.py`: Universal 12-bit adaptive LZW dictionary codec.
  * `src/channel_coding/ldpc_codec.py`: Systematic rate-1/2 $(64, 32)$ LDPC code with Log-Domain Belief Propagation (Sum-Product) and Min-Sum.
  * `src/channel_coding/polar_codec.py`: Systematic $(64, 32)$ Polar code with Successive Cancellation.
  * `src/channel_coding/linear_block_codec.py`: Systematic Hamming $(7, 4)$ baseline.
  * `src/wireless/frame_protocol.py`: 36-byte versioned binary frame header with IEEE 802.3 CRC32 checksum.
  * `src/wireless/network_transceiver.py`: `WirelessSender` and `WirelessReceiver` TCP socket classes with sequence confirmation.
  * `src/wireless/channel_sim.py`: BPSK baseband modulation ($s = 1 - 2b$), AWGN noise scaling $\sigma = 1/\sqrt{2 R \cdot 10^{E_b/N_0/10}}$, and channel LLR computation $L_i = 2y_i/\sigma^2$.

* **Empirical Benchmarks:**
  * `results/csv/awgn_ber_comparison.csv`: BER versus $E_b/N_0$ sweep across 25,600 bits per test point.
  * `results/csv/source_compression_study.csv`: Empirical entropy and compression ratios across diverse source models.
  * Live Socket Transmission: Demonstrated via `python main.py --wireless-demo`.
  * Multi-Trial Simulation: Demonstrated via `python main.py --multi-trial --snr 4.0 --trials 10` ($43.3\times$ gain) and `python main.py --multi-trial --snr 7.0 --trials 10` ($100\%$ exact recovery).
