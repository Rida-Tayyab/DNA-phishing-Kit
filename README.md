# Phishing Kit DNA Fingerprinter

A machine learning system that classifies phishing kits by their behavioral and structural "DNA" — extracting 55 structured features and 384-dimensional semantic embeddings from ZIP archives to identify kit families, detect clones, and attribute campaigns to threat actors.

**Live demo:** [https://dna-phishing-4axzbnew9-rida-tayyabs-projects.vercel.app](https://dna-phishing-4axzbnew9-rida-tayyabs-projects.vercel.app)  
**API:** [https://web-production-56949.up.railway.app](https://web-production-56949.up.railway.app)

---

## What it does

Upload any phishing kit ZIP file and the system will:

- Identify which known malware family it belongs to
- Return a confidence score based on nearest-neighbor agreement
- Show the 5 most similar kits from the indexed dataset
- Plot the kit's position on an interactive UMAP threat landscape map

The classifier reaches **88.0% top-1 accuracy** on families with 5+ known instances, using a hybrid vector that combines structured behavioral features with semantic code embeddings.

---

## How it works

### Feature extraction pipeline

Every kit goes through four extractors in parallel:

| Extractor | Features | What it captures |
|-----------|----------|-----------------|
| `html_extractor.py` | 25 features | Form structure, brand targeting, input field types, CAPTCHA, mobile viewport |
| `php_extractor.py` | 25 features | Exfiltration method (Telegram/email/file), bot detection, credential targeting (card/CVV/OTP/SSN), token generation style |
| `js_extractor.py` | 19 features | Obfuscation (`eval`, `atob`), framework usage, fetch/XHR exfiltration, form validation |
| `structural_features_extract.py` | 8 features | PHP/JS file ratios, admin panels, config files, `.htaccess`, directory depth |

These 55 structured features are min-max normalized using stats computed from the full training corpus (`data/normalization_stats.json`) and concatenated with a 384-dimensional semantic embedding of the kit's PHP/JS source code, produced by `all-MiniLM-L6-v2` via `sentence-transformers`.

The final 439-dimensional hybrid vector is L2-normalized and searched against a FAISS flat index of 6,831 labeled kits. The predicted family is the majority vote of the 5 nearest neighbors, and confidence is that majority proportion.

### Why hybrid vectors?

Structured features capture **what a kit does** — how it steals credentials, how it evades detection, what brand it impersonates. The text embedding captures **how it was written** — variable naming conventions, code style, comment patterns, authorship fingerprints. Neither alone is sufficient. Together they form a DNA fingerprint that's robust to surface-level code changes while remaining sensitive to family-level behavioral patterns.

### The normalization fix

During development, a critical bug was found and fixed: the 384-dim text embedding comes out L2-normalized (norm ≈ 1.0) by default, but the 55-dim structured feature vector had raw magnitudes in the thousands (e.g. `php_line_count`, `total_files`). When concatenated, the structured features completely swamped the text signal — reducing its contribution to roughly 1/17,000th of the final vector. The fix was to apply min-max normalization to structured features before concatenation, bringing both components to the same scale. Accuracy on families with 5+ kits improved from 82.9% → 88.0%.

---

## Dataset

- **6,831 phishing kits** indexed across hundreds of families
- **421 families** where every instance is an exact clone (byte-for-byte identical feature fingerprint), totaling 1,955 instances — evidence of the real-world kit distribution/resale ecosystem
- Top exfiltration split: 46% email (`mail()`), 44% Telegram bot API
- Sophistication scores range 0–10, mean 4.8
- Top impersonated brands: Facebook (23%), generic banking (6%), Google (5%)

---

## Accuracy

| Scope | Accuracy |
|-------|----------|
| Families with 5+ instances (top-1) | **88.0%** |
| High-confidence predictions (4/5 or 5/5 neighbors agree) | **86.2%** |
| Full dataset including rare families | 59.0% |

The confidence score is a real signal — when the model says it's confident, it's right more often. Low confidence (e.g. 2/5 neighbors agree) is a genuine indicator that the kit may be from a rare or novel family not well-represented in the index.

---

## Project structure

```
├── api/
│   ├── main.py                  # FastAPI app — /classify endpoint
│   ├── upload_handler.py        # ZIP extraction + feature orchestration
│   └── requirements.txt         # API-specific deps (subset)
├── embedders/
│   ├── embedder.py              # 55-dim structured vector builder + normalizer
│   └── text_embedder.py         # SentenceTransformer semantic embedder
├── extractors/
│   ├── html_extractor.py        # Form/brand/input analysis
│   ├── php_extractor.py         # Exfiltration/evasion/credential analysis
│   ├── js_extractor.py          # Obfuscation/framework/fetch analysis
│   └── structural_features_extract.py
├── m1/
│   ├── classifier.py            # FAISS kNN classifier
│   ├── evaluate.py              # Accuracy evaluation
│   ├── eda.py                   # Exploratory data analysis
│   └── duplicate_check.py       # Clone detection
├── pipeline/
│   ├── pipeline.py              # Batch feature extraction
│   ├── build_index.py           # FAISS index builder
│   └── run_extractor.py
├── data/
│   ├── kit_index.faiss          # FAISS flat index (6,831 kits)
│   ├── index_metadata.json      # Kit hash → family label mapping
│   ├── normalization_stats.json # col_min/col_max for structured features
│   ├── features.json            # Extracted features per kit
│   └── dataset_manifest.json   # Kit inventory with file lists
├── frontend/
│   └── phishing-classifier/     # React + TypeScript frontend
├── requirements.txt             # Root requirements for Railway deployment
└── Procfile                     # Railway process definition
```

---

## Running locally

### Backend

```bash
# From project root
pip install -r requirements.txt

# Run from the api/ directory
cd api
python run.py
# API available at http://127.0.0.1:8000
```

### Frontend

```bash
cd frontend/phishing-classifier
npm install
npm start
# App available at http://localhost:3000
```

Set `REACT_APP_API_URL=http://127.0.0.1:8000` in a `.env` file in `frontend/phishing-classifier/` if needed.

### Rebuild the FAISS index (optional)

```bash
# Extract features from a new dataset
python pipeline/pipeline.py

# Build the index
python pipeline/build_index.py
```

---

## API reference

### `POST /classify`

Accepts a ZIP file upload and returns a classification result.

**Request:** `multipart/form-data` with field `file` (`.zip` only)

**Response:**
```json
{
  "predicted_family": "dhl-cryptre-news",
  "confidence": 0.8,
  "top_5_neighbours": [
    ["dhl-cryptre-news", 0.12],
    ["dhl-cryptre-news", 0.13],
    ["dhl-cryptre-news", 0.14],
    ["newPost", 0.18],
    ["dhl-cryptre-news", 0.19]
  ]
}
```

**Error responses:**
- `400` — file is not a ZIP
- `500` — extraction or classification failed (detail message included)

---

## Deployment

The system is split across two services:

| Service | Platform | Purpose |
|---------|----------|---------|
| FastAPI backend | Railway | Feature extraction + FAISS classification |
| React frontend | Vercel | Interactive UI + threat map visualization |

### Environment variables

**Railway (backend service):**
```
ALLOWED_ORIGINS=https://your-app.vercel.app
NIXPACKS_PYTHON_VERSION=3.11
```

**Vercel (frontend):**
```
REACT_APP_API_URL=https://your-app.up.railway.app
```

---

## Key findings

**Kit cloning is rampant.** 421 families in the dataset are exact byte-for-byte clones, with family `53` alone having 206 identical instances. Phishing kits are not hand-crafted per attack — they're built once and distributed widely. This cloning behavior is precisely what makes DNA fingerprinting effective.

**The exfiltration split is nearly 50/50.** 46% of kits use `mail()`, 44% use Telegram bot API. This binary split makes exfiltration method one of the strongest single features for family attribution.

**Confidence is calibrated.** A 4/5 or 5/5 neighbor agreement translates to 86.2% accuracy in practice. If the model returns low confidence, treat it as genuine uncertainty — the kit may be from a family with too few examples to form a reliable cluster, or from a novel family not in the index.

---

## Tech stack

- **ML:** FAISS (flat L2 index), sentence-transformers (`all-MiniLM-L6-v2`), numpy
- **Backend:** FastAPI, uvicorn, Python 3.11
- **Frontend:** React 19, TypeScript, plotly.js, framer-motion, Tailwind
- **Infra:** Railway (backend), Vercel (frontend)

---

## Dataset credit

Built on the [DynaPD dataset](https://drive.google.com/file/d/1o2Hgr3SvtcsVsMiB4gnSafMezc_4FSLa/view):

```bibtex
@inproceedings{liu2023knowledge,
  author = {Ruofan Liu and Yun Lin and Yifan Zhang and Penn Han Lee and Jin Song Dong},
  title = {Knowledge Expansion and Counterfactual Interaction for Reference-Based Phishing Detection},
  booktitle = {32nd USENIX Security Symposium (USENIX Security 23)},
  year = {2023},
  pages = {4139--4156}
}
```
