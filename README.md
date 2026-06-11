# TTB Alcohol Label Verifier

An AI-powered web application for TTB (Alcohol and Tobacco Tax and Trade Bureau) compliance agents to verify alcohol beverage labels against application data.

## What It Does

Upload a label image and provide application data — the tool uses Claude's vision AI to:
- Extract all text from the label image
- Compare extracted fields against the submitted application data (brand name, ABV, class/type, net contents, producer info, country of origin)
- Verify the mandatory **Government Warning Statement** for exact TTB wording and correct capitalization
- Return a clear APPROVED / REJECTED verdict per field with explanations

Supports **single label** and **batch upload** (200+ labels at once).

## Tech Stack

| Layer | Choice |
|-------|--------|
| Backend | Python + FastAPI |
| AI / Vision | Anthropic Claude (claude-haiku-4-5) |
| Frontend | Plain HTML/CSS/JS (no framework) |
| Server | Uvicorn |

## Setup

### 1. Prerequisites

- Python 3.11+
- An [Anthropic API key](https://console.anthropic.com/)

### 2. Install dependencies

```bash
cd alcohol-label-verifier
pip install -r requirements.txt
```

### 3. Set your API key

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

### 4. Run the app

```bash
uvicorn main:app --reload
```

Open **http://localhost:8000** in your browser.

## Usage

### Single Label
1. Upload a label image (JPEG/PNG/WebP)
2. Fill in the application data fields (only Brand Name is required)
3. Click **Verify Label**
4. Review the field-by-field results

### Batch Upload
1. Upload multiple label images
2. Paste a JSON array with one application data object per image (same order)
3. Click **Verify All Labels**

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Web UI |
| POST | `/verify` | Single label verification |
| POST | `/verify/batch` | Batch label verification |
| GET | `/health` | Health check |

## Government Warning Statement

The tool checks for the exact TTB-required warning (GOVERNMENT WARNING: must appear in ALL CAPS with exact wording).

## Design Decisions

- **Fuzzy matching**: Case-insensitive, whitespace-normalized field comparisons avoid false rejections on cosmetic differences
- **Strict government warning**: Exact wording + all-caps GOVERNMENT WARNING: enforced as a hard requirement
- **claude-haiku-4-5**: Chosen for speed (targets <5s response per label per stakeholder requirements)
- **No persistent storage**: All processing is in-memory per request
