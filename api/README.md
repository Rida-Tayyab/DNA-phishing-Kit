# Phishing Kit Classifier API

FastAPI backend for classifying uploaded phishing kits using machine learning.

## Features

- Upload ZIP files containing phishing kits
- Extract structural, HTML, PHP, and JavaScript features
- Classify kits using hybrid ML model (structured features + text embeddings)
- Return predicted family, confidence score, and similar kits
- CORS-enabled for web frontend integration

## Setup

1. Install dependencies:
```bash
cd api
pip install -r requirements.txt
```

2. Ensure data files exist:
- `data/kit_index.faiss` - FAISS similarity index
- `data/index_metadata.json` - Kit metadata for index
- `data/features.json` - Feature data for all kits
- `data/normalization_stats.json` - Feature normalization parameters

## Usage

### Start Server
```bash
cd api
python run.py
```

Server runs on http://127.0.0.1:8000

### Classify Kit
```bash
curl -X POST -F "file=@phishing_kit.zip" http://127.0.0.1:8000/classify
```

### Test Script
```bash
python test_api.py path/to/kit.zip
```

## API Endpoints

### POST /classify
Upload and classify a phishing kit ZIP file.

**Request:** Multipart form with `file` field containing ZIP
**Response:** JSON with classification results

```json
{
  "predicted_family": "paypal-phish", 
  "confidence": 0.85,
  "top_5_neighbours": [
    ["paypal-phish", 0.12],
    ["payment-steal", 0.15],
    ["financial-scam", 0.18],
    ["banking-fake", 0.21], 
    ["ecommerce-phish", 0.24]
  ]
}
```

### GET /
Health check endpoint.

**Response:** `{"message": "Phishing Kit Classifier API"}`

## Architecture

The API processes uploaded kits through a 4-step pipeline:

1. **Extract ZIP** - Unpack to temporary directory, handle folder structures
2. **Build Manifest** - Scan files, count types, generate kit hash  
3. **Extract Features** - Run HTML/PHP/JS/structural feature extractors
4. **Classify** - Generate embeddings and find similar kits using FAISS

All existing ML components are reused without modification.