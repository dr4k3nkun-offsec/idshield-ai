# IDShield AI // Autonomous Forensic Credential Intelligence & Syndicate Defense Engine

[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-3776AB.svg?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI Core](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Computer Vision](https://img.shields.io/badge/OpenCV-ONNX%20Inference-5C3EE8.svg?style=flat-square&logo=opencv&logoColor=white)](https://opencv.org/)
[![Graph Analytics](https://img.shields.io/badge/NetworkX-3.0+-blueviolet.svg?style=flat-square)](https://networkx.org/)
[![Evidentiary Standard](https://img.shields.io/badge/Compliance-Section%2063%20BSA%20(2023)-059669.svg?style=flat-square)](https://www.mha.gov.in/)
[![Frontend Terminal](https://img.shields.io/badge/React-18.0%20Vite-61DAFB.svg?style=flat-square&logo=react&logoColor=black)](https://react.dev/)
[![Security License](https://img.shields.io/badge/Classification-RESTRICTED%20DEFENSE-red.svg?style=flat-square)](LICENSE)

**IDShield AI** is an autonomous digital document forensics and syndicate intelligence platform engineered for border security gates, statutory KYC compliance, and Cyber Security Operations Centers (SOC). 

Unlike legacy OCR solutions that function merely as passive text digitizers, **IDShield AI operates as an active red-team triage engine**. It inspects credentials across the hardware sensor, pixel compression, spectral frequency, and cross-case network layers—pinpointing digital manipulation, synthetic deepfakes, screen recaptures, and coordinated Sybil fraud farms across Indian statutory artifacts (Aadhaar, PAN Card, Passport, and Driving Licences).

---

## Tactical Defense Capabilities & Forensic Vectors

| Forensic Vector | Adversarial Attack Profile | Detection Mechanism / Algorithmic Engine |
| :--- | :--- | :--- |
| **Zero-Trust Access Control** | Unauthorized API screening, unauthenticated tampering | **PBKDF2-HMAC-SHA256 (100k iters) RBAC** with persistent SQLite session validation |
| **Hardware Sensor Fingerprint** | Multi-case fraud fabricated on a single physical camera | **PRNU (Photo-Response Non-Uniformity)** edge-masked silicon sensor residual extraction ($W = I - F(I)$) |
| **Generative AI & Inpainting** | Stable Diffusion, Midjourney, or Flux face/text injection | **2D Fourier Azimuthal Spectral Decay** measuring Peak-to-Average Spectral Ratios (PASR) |
| **Pixel Splice & Cloning** | Localized text splicing, serial editing, date tampering | **12x12 Block Error Level Analysis (ELA)** + DCT high-frequency re-compression variance |
| **Screen Recapture / Replay** | Photos taken off monitors, tablets, or phone screens | **2D-FFT Spatial Fourier Transform** isolating periodic Moiré interference lattice spikes |
| **Biometric Sybil Attacks** | Face swapping, digital masks, multi-identity portrait reuse | **YuNet Quadrant Anchoring + SFace 128D Cosine Proximity** ($\ge 0.40$ threshold) |
| **Dihedral Checksum Spoofing**| Algorithmically synthesized fake identity serials | **Verhoeff Dihedral Group ($D_5$) Permutations** & Regional Transport Office syntax engines |
| **Syndicate Fraud Networks** | Template farms, distributed credential blank reuse | **NetworkX Graph Community Topology** with automated Kingpin Hub degree centrality scoring |
| **Judicial Chain-of-Custody** | Evidence tampering, uncertified digital forensic audits | **Automated Section 63 BSA (2023) Digital Certification** with SHA-256 cryptographic ledgers |

---

## Full-Spectrum Forensic Pipeline

```text
                        [ Physical ID Scan / Optical Payload ]
                                          │
                                          ▼
                         [ Binary Magic-Byte Verification ]
                             (Non-image payload dropped)
                                          │
        ┌─────────────────────────────────┼─────────────────────────────────┐
        ▼                                 ▼                                 ▼
[ Spatial Domain ]              [ Frequency Domain ]             [ Sensor Domain (PRNU) ]
  • 12x12 Block ELA Residue       • 2D-FFT Moiré Replay            • Silicon Imperfection Residual
  • Substrate Noise Smoothing     • Azimuthal Radial Diffusion     • Canny Edge-Masked Noise Floor
  • Tesseract Regex Taxonomy        PASR Generation Anomaly        • Camera Device Hash Signature
        │                                 │                                 │
        └─────────────────────────────────┼─────────────────────────────────┘
                                          │
                                          ▼
                          [ Neural Biometrics (ONNX Engine) ]
                            • YuNet Contextual Face Localization
                            • SFace 128-Dimensional Cosine Embeddings
                                          │
                                          ▼
                       [ NetworkX Syndicate Topology Engine ]
                            • Perceptual Hashing (pHash) Canvas Collisions
                            • Cross-Identity Biometric Edge Generation
                            • Degree Centrality Kingpin / Hub Node Isolation
                                          │
                                          ▼
                         [ Regulatory Masking & Redaction ]
                            • Statutory Citizen PII Redaction
                                          │
                                          ▼
                         [ Cryptographic Chain-of-Custody ]
                            • SHA-256 Forward-Linked Immutable Block Ledger
                                          │
                                          ▼
                    ┌─────────────────────┴─────────────────────┐
                    ▼                                           ▼
      [ Tactical Incident SOC HUD ]            [ Section 63 BSA Court Dossier ]
        • Calibrated Inspection Grids            • Certified Electronic Evidence
        • Network Graph Visualizer               • Examiner Sign-Off (INV-7029 L3)

```

---

## Interactive Syndicate Graph Intelligence

IDShield AI treats fraud as a connected graph rather than isolated uploads. Every processed credential registers its biometric signature, perceptual canvas geometry, and subject identity into an active topological graph $G(V, E)$.

```text
                     [ DOC-2026-DEMO-05 ] (KINGPIN HUB)
                     Risk: 85 // Centrality: 0.75
                               /      \
       (BIOMETRIC COLLISION)  /        \  (TEMPLATE FARM BLANK)
       Cosine Sim: 0.94      /          \  Hamming Dist: 1
                            ▼            ▼
                   [ DOC-2026-A102 ]   [ DOC-2026-B884 ]
                   Identity: Alias A   Identity: Alias B

```

* **Automated Cluster Tagging:** Subgraphs with multi-edge connectivity trigger instant alerts (`CRITICAL: Cross-Identity Biometric Sybil Ring`).
* **Centrality Kingpin Identification:** Calculates node degree centrality ($C_D(v) = \frac{\deg(v)}{\vert V \vert - 1}$) to isolate the root source of document template distribution.
* **Direct Graph API:** Returns ready-to-render graph JSON via `/api/syndicate/graph` for node/link canvas components.

---

## Legal Admissibility: Section 63 BSA (2023) Briefs

Under modern Indian jurisprudence, digital evidence submitted in court must comply with **Section 63 of the Bharatiya Sakshya Adhiniyam, 2023 (BSA)** (superseding Section 65B of the Indian Evidence Act).

IDShield AI's reporting pipeline (`report_generator.py`) produces court-admissible forensic briefs featuring:

1. **Nmap/SOC Reconnaissance Telemetry:** Target classification, processing latency, and diagnostic threat bars.
2. **Dual Evidentiary Grid:** Raw optical capture side-by-side with neural ELA heatmap overlays.
3. **Plugin Diagnostic Matrix:** Itemized vector excursions (`VEC-ELA-02`, `VEC-FOURIER-09`, `VEC-SFACE-07`).
4. **Cryptographic Certificate of Electronic Evidence:** Embedded host node identifier, UTC NTP timestamp, raw SHA-256 payload digest, and Level-3 Forensic Examiner signature block.

---

## Technology Stack

| Architecture Layer | Core Components & Libraries |
| --- | --- |
| **Forensic Backend** | FastAPI, Python 3.11+, Uvicorn, Pydantic v2 |
| **Computer Vision & Math** | OpenCV (Headless), NumPy Fourier, Discrete Cosine Transform (DCT) |
| **Neural Inference** | ONNX Runtime, `FaceDetectorYN` (YuNet), `FaceRecognizerSF` (SFace) |
| **Graph Intelligence** | NetworkX 3.0+ (Topological Community & Centrality Algorithms) |
| **OCR & Text Extraction** | Tesseract OCR, Group Permutation Dihedral $D_5$ Matrix |
| **Evidentiary Publishing** | ReportLab (Two-Pass `NumberedCanvas` Section 63 BSA Briefs) |
| **Frontend Console** | React 18, TypeScript, Vite, Tailwind CSS, Lucide Icons |
| **Ledger & Persistence** | SQLite3 (WAL Mode), SHA-256 Forward-Linked Cryptographic Ledger |
| **Zero-Trust Security** | PBKDF2 Key Derivation, HTTPBearer Token Auth, Strict CORS Allowlist |

---

## Repository Layout

```text
idshield-ai/
├── backend/
│   ├── main.py                 # API router, RBAC session auth, NetworkX syndicate graph engine
│   ├── forensic_service.py     # PRNU sensor attribution, 2D-FFT spectral decay, 12x12 ELA
│   ├── validation_service.py   # Verhoeff D5, PAN/DL/Passport syntax, credential chronology
│   ├── report_generator.py     # Section 63 BSA statutory court dossier engine (ReportLab)
│   ├── masking_engine.py       # Regulatory DPDP / statutory PII redaction engine
│   ├── audit_service.py        # Forward-linked SHA-256 tamper-evident cryptographic ledger
│   ├── database.py             # SQLite schemas, sanctions watchlist & persistent state
│   ├── seed_demo.py            # Syndicate scenario generator & synthetic image builder
│   ├── models/                 # Pre-trained ONNX weights (YuNet, SFace)
│   ├── Dockerfile              # Production container spec for backend runtime
│   └── requirements.txt        # Pinned Python production dependencies
│
└── idshield-ai/                # React HUD Frontend Application
    ├── src/
    │   ├── components/         # Tactical evidence viewers, syndicate graph canvas
    │   ├── pages/              # Screening terminal, Audit Center, Threat Analytics
    │   └── services/           # Axios API connectors & ledger verification hooks
    ├── vite.config.ts          # Reverse-proxy dev pipeline
    └── package.json            # Node module dependencies

```

---

## Quickstart & Operations

### Prerequisites

* Python 3.10+
* Node.js v18+ & npm
* Tesseract OCR installed on the host system

### 1. Environment Configuration

Create a `.env` file in the `backend/` directory:

```env
# Agency secret key for registering new investigator badges
AGENCY_SECRET_KEY=your_secure_agency_secret_key_here

# Initial Admin Bootstrap Credentials
INITIAL_ADMIN_BADGE=INV-7029
INITIAL_ADMIN_PASSWORD=your_secure_admin_password_here

# Strict CORS origin mapping (frontend origins only)
ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,https://<your-app>.vercel.app
```

### 2. Launch Forensic Backend

```powershell
# Navigate to backend
cd backend

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1    # Linux/macOS: source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Launch FastAPI engine
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000

```

Interactive API documentation available at `http://127.0.0.1:8000/docs`.

### 3. Launch Tactical Frontend Terminal

```powershell
# Navigate to frontend in a separate terminal
cd idshield-ai

# Install modules and launch Vite dev server
npm install
npm run dev

```

Navigate to `http://localhost:5173` to access the Command Console.

---

## Testing & Operational Verification

### Seed Simulated Syndicate Network

Populate the database and graph engine with synthetic test dossiers, PRNU edge cases, and cross-dossier Sybil clusters:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/documents/seed-demo" -Method Post
```

### Inspect Live Graph Topology & Hub Centrality

Verify detected clusters, active edges, and the highest-centrality kingpin:

```powershell
(Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/syndicate/graph" -Method Get).metrics
```

### Cryptographically Verify SHA-256 Ledger

Confirm that the forward-linked audit chain remains untampered:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/audit/verify-chain" -Method Get -Headers @{ Authorization = "Bearer sec-token-inv-7029-master" }
```

### Reset System State (L3 Clearance Required)

Clear all session records, memory registries, and perceptual hash banks:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/documents/clear" -Method Delete -Headers @{ Authorization = "Bearer sec-token-inv-7029-master" }
```

---

## Production Deployment Topology

* **Frontend (Vercel):** Edge static distribution. Dynamic API routing connects to the core backend with strict `Authorization: Bearer` session headers.
* **Backend (Render):** Headless Docker container running Python 3.11, OpenCV, ONNX Runtime, and Tesseract OCR with persistent disk storage for uploaded dossiers.

---

## Security & Evidentiary Disclaimer

This software was engineered specifically for identity fraud detection, digital document forensics, and statutory security research. All demonstration identities, artifacts, and scenarios generated by the test harness are simulated entities and do not correspond to actual citizen records.

---

## Operator Contact // Incident Response

For vulnerability disclosures, forensic intelligence sharing, or system deployment queries:

* **Instagram:** [@dr4k3n_kun](https://instagram.com/dr4k3n_kun)
* **Telegram:** [@dr4k3n2007](https://t.me/dr4k3n2007)
* **Command Unit:** CYBER THREAT TRIAGE WING (Badge: `INV-7029`)
