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
| AI / Vision | Anthropic Claude (`claude-haiku-4-5`) |
| Frontend | Plain HTML/CSS/JS (no framework) |
| Server | Uvicorn |

**Why `claude-haiku-4-5`?** Speed. Stakeholder interviews emphasized < 5 second response time. Haiku consistently returns in 2–4 seconds per label while maintaining strong OCR accuracy.

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

Or create a `.env` file:
```
ANTHROPIC_API_KEY=sk-ant-...
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
4. Expand each result to review details

**Batch JSON format:**
```json
[
  {
    "brand_name": "OLD TOM DISTILLERY",
    "class_type": "Kentucky Straight Bourbon Whiskey",
    "alcohol_content": "45% Alc./Vol. (90 Proof)",
    "net_contents": "750 mL",
    "producer_name": "Old Tom Distillery LLC",
    "producer_address": "Louisville, KY 40201",
    "country_of_origin": null
  }
]
```

Only `brand_name` is required. Omit or set to `null` any fields not present in the application.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Web UI |
| POST | `/verify` | Single label verification |
| POST | `/verify/batch` | Batch label verification |
| GET | `/health` | Health check |

### POST /verify

**Form data:**
- `label_image` — image file
- `app_data` — JSON string of application data

### POST /verify/batch

**Form data:**
- `label_images` — multiple image files
- `app_data_list` — JSON array string, one entry per image

## Design Decisions & Trade-offs

**Fuzzy matching for field comparisons**: Field comparisons are case-insensitive and whitespace-normalized (per Dave Morrison's feedback about "STONE'S THROW" vs "Stone's Throw"). This avoids false rejections on cosmetic differences while still catching actual mismatches.

**Strict government warning check**: The government warning is checked against the exact TTB-required wording. Capitalization of "GOVERNMENT WARNING:" is specifically verified as a hard requirement (per Jenny Park's feedback).

**Optional fields**: Only `brand_name` and the government warning statement are treated as hard requirements. Other fields are only checked if provided in the application data — if left blank, they show as "SKIPPED" rather than causing a rejection.

**Sequential batch processing**: Labels in a batch are processed sequentially (one API call per label). A future improvement would be async parallel processing for very large batches.

**No persistent storage**: This prototype does not store images or application data. All processing is in-memory per request, consistent with the prototype scope and federal data retention considerations mentioned by IT.

## Government Warning Statement

The tool checks for the exact TTB-required warning:

> GOVERNMENT WARNING: (1) According to the Surgeon General, women should not drink alcoholic beverages during pregnancy because of the risk of birth defects. (2) Consumption of alcoholic beverages impairs your ability to drive a car or operate machinery, and may cause health problems.

Requirements verified:
- `GOVERNMENT WARNING:` must appear in ALL CAPS
- Full wording must match exactly (case-insensitive)

## Limitations

- Accuracy depends on image quality; very low resolution or heavily obscured labels may yield incomplete extractions
- Parallel batch processing not yet implemented (sequential calls add ~3–5s per label)
- No integration with the COLA system (intentional for this prototype scope)
- No authentication / access control (add before any production deployment)
