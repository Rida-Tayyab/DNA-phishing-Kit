# Phishing Kit DNA - Feature Engineering

This project extracts behavioral fingerprints from phishing kits to enable similarity detection, clustering, and attribution analysis.

## Overview

We extract **55 structured features** + **384-dimensional text embeddings** from each phishing kit to create a comprehensive "DNA fingerprint" that captures both operational behavior and authorship patterns.

## Feature Categories

### 1. HTML Features (25 features)
**File**: `html_extractor.py`

- **Form Analysis**: Form counts, input field types (password, email, card, OTP)
- **Brand Detection**: Keyword matching against 15+ major brands (PayPal, Microsoft, Chase, etc.)
- **Page Structure**: Mobile viewport, CAPTCHA detection, external scripts
- **Form Behavior**: Action targets (internal/external), PHP endpoints

### 2. PHP Features (25 features)  
**File**: `php_extractor.py`

- **Exfiltration Methods**: Telegram API, email, file storage, cURL usage
- **Anti-Analysis**: Bot detection, IP logging, country filtering
- **Credential Targeting**: Password, card, CVV, OTP, SSN, DOB extraction
- **Author Fingerprints**: Token generation styles, Telegram chat IDs
- **Sophistication Scoring**: Combined metric (0-10 scale)

### 3. JavaScript Features (19 features)
**File**: `js_extractor.py`

- **Obfuscation**: `eval()`, `atob()`, minified code detection
- **Frameworks**: jQuery, Vue.js, webpack usage
- **Exfiltration**: `fetch()`, `XMLHttpRequest`, `FormData` usage
- **Targeting**: DOM manipulation of credential fields
- **Validation**: Form submission and validation patterns

### 4. Structural Features (8 features)
**File**: `structural-features-extract.py`

- **File Composition**: PHP/JS ratios, multi-page detection
- **Infrastructure**: Admin panels, config files, directory depth
- **Configuration**: .htaccess, Telegram integration flags

### 5. Text Embeddings (384 dimensions)
**File**: `text_embedder.py`

- **Semantic Analysis**: First 512 characters of combined PHP/JS source
- **Authorship Detection**: Variable naming, code style, comment patterns
- **Model**: SentenceTransformer 'all-MiniLM-L6-v2'

## Pipeline Architecture

```
dataset_manifest.json → pipeline.py → features.json
                          ↓
    ┌─────────────────────────────────────┐
    │ Extract Features (parallel)         │
    ├─────────────────────────────────────┤
    │ • html_extractor.py                 │
    │ • php_extractor.py                  │
    │ • js_extractor.py                   │
    │ • structural-features-extract.py    │
    └─────────────────────────────────────┘
                          ↓
    ┌─────────────────────────────────────┐
    │ Feature Encoding                    │
    ├─────────────────────────────────────┤
    │ • embedder.py (55-dim vectors)      │
    │ • text_embedder.py (384-dim)        │
    └─────────────────────────────────────┘
```

## Key Design Decisions

### Why 512-character truncation?
The first 512 characters capture core authorship signals (variable naming, code structure, initial comments) while avoiding repetitive boilerplate that dilutes semantic fingerprints.

### Why structured + text features?
- **Structured features**: Capture operational behavior (exfiltration, targeting, sophistication)
- **Text embeddings**: Capture authorship patterns (coding style, variable names)

### Performance optimizations:
- HTML files >300KB skipped (avoid parsing massive files)
- PHP files >200KB truncated (keep core patterns)
- Max 10 HTML/JS files per kit (diminishing returns)
- Checkpointing every 500 kits (fault tolerance)

## Usage

### Extract Features
```bash
python data_exploration/pipeline.py
# Processes 7,016 kits → features.json (6,831 successful)
```

### Analyze Results  
```bash
python data_exploration/eda.py
# Shows exfiltration methods, sophistication scores, brand targeting
```

### Generate Vectors
```python
from embedder import build_all_vectors

vectors, labels, hashes = build_all_vectors("features.json")
# Returns: 55-dim numerical vectors + family labels + kit hashes
```

### Text Embeddings
```python
from text_embedder import embed_kit_source

embedding = embed_kit_source(kit_root, kit_data)  
# Returns: 384-dim semantic vector
```

## Validation Results

### Family Consistency
Family "53" (206 kits): **Perfect consistency** - 0.0 standard deviation across all features, proving our DNA extraction captures family-specific patterns.

### Discriminative Power
Most distinctive features (by variance):
1. `php_file_count` (92,657 variance)
2. `js_file_count` (35,185 variance)  
3. `external_script_count` (144 variance)

### Distribution Insights
- **Exfiltration**: 47% email, 45% Telegram, 6% unknown, 3% file
- **Sophistication**: Mean 4.8/10, range 0-10
- **Top brands**: Facebook (23%), Banking (6%), Google (5%)

## Applications

1. **Similarity Detection**: Find kits with similar behavioral patterns
2. **Clustering**: Group kits by operational characteristics  
3. **Attribution**: Link kits to threat actors via code patterns
4. **Evolution Tracking**: Monitor how families change over time
5. **Detection Evasion**: Identify anti-analysis techniques

## File Structure

```
data_exploration/
├── pipeline.py              # Main feature extraction pipeline
├── html_extractor.py        # HTML/form analysis  
├── php_extractor.py         # Backend behavior analysis
├── js_extractor.py          # JavaScript analysis
├── structural-features-extract.py  # File structure analysis
├── embedder.py              # Numerical vector encoding
├── text_embedder.py         # Semantic text embedding
├── eda.py                   # Exploratory data analysis
└── dataset_manifest.json    # Kit metadata input

features.json                # Extracted features (output)
features_checkpoint.json     # Progress checkpoint
```