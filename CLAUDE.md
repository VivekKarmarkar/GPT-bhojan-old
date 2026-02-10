# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Vision

GPT-Bhojan is being rebuilt as a **"Strava for Food"** — a personal, gamified food tracking app with a feedback loop between eating well and running. It is NOT a macro-tracking app. The user is an intuitive eater and runner.

**The existing v0-v12 Streamlit code is REFERENCE ONLY** — it communicates the core AI architecture (GPT-4 Vision + YOLO + SAM pipeline) but should NOT guide the actual build beyond that. The app is being rebuilt from scratch.

### Target Product
- Mobile-first app (must work on older 2017 Android phone) + desktop/tablet
- Strava API integration for running data
- Gamification: streaks, badges ("Healthy Legend"), combined food+exercise scores
- Visual dashboards and analytics (Strava-inspired), NOT text-heavy output
- Food library with "like" functionality and per-item analytics
- Meal timing analytics (when meals happen, clustering, patterns)
- Personal app — no social media features

### Key Architecture Changes from Prototype
- **Local ML inference → Replicate cloud API** for YOLO and SAM (no local GPU/CUDA needed)
- **Streamlit → React PWA + FastAPI** backend
- FastAPI calls Replicate API (YOLO-World, SAM) + OpenAI API (GPT-4 Vision)
- Optimize for **inference speed** over peak accuracy — mobile latency is priority
- Simple, insightful metrics over complex macro tracking

### ML Inference via Replicate (Feb 9 2026 pivot)
- All ML model inference (detection, segmentation) runs on Replicate cloud GPUs via API
- No local CUDA, torch, or GPU setup required — eliminates hardware blockers
- Pipeline: Phone → FastAPI → Replicate API → results
- Models being evaluated: YOLO-World (detection), SAM 2/3 (segmentation)
- Claude uses Chrome extension to browse Replicate playground, test models, grab boilerplate code

See `VISION.md` for the full product spec, phased development plan, and design principles.

## Prototype Reference (v0-v12)

## Running the App

```bash
# Install dependencies
pip install -r requirements.txt
pip install segment-anything   # Not in requirements.txt but required by v10+

# Run latest version
streamlit run gpt_bhojan_app_v12.py --server.enableCORS false --server.enableXsrfProtection false

# Run via dev container (GitHub Codespaces) — auto-runs v0 on port 8501
```

## Testing

```bash
# Standalone SAM + YOLO pipeline test (requires manual config of image path and API key inside file)
python test_sam.py
```

There is no automated test suite, linter, or formatter configured.

## Required Secrets

Secrets are loaded via `st.secrets` from `.streamlit/secrets.toml`:

```
OPENAI_API_KEY   — OpenAI API key (GPT-4 Vision)
SUPABASE_URL     — Supabase project URL
SUPABASE_KEY     — Supabase anon/service key
```

## Architecture

The app is a single-file Streamlit application. The latest version is `gpt_bhojan_app_v12.py`.

### Processing Pipeline (v12)

1. **Image Upload** — Streamlit `file_uploader`, image stored in Supabase Storage (`foodimages` bucket)
2. **GPT-4 Vision Analysis** — Base64-encoded image sent with a 15-point structured prompt; response parsed via regex (`re.findall` on numbered markdown fields)
3. **YOLO Detection** — `yolov8m.pt` finds bounding boxes for individual food items
4. **Per-box Processing Loop** — For each YOLO detection:
   - Crop bounding box region, encode to base64
   - GPT-4 identifies if crop matches a food item from the plate description
   - SAM segments the item using the bounding box as prompt (`SamPredictor.predict(box=...)`)
   - Both mask and complement are cropped, encoded, and sent to GPT-4 for A/B verification
   - Winning segment saved to `food_library/` with incremental naming (`{label}_{n}.jpg`)
5. **Visualization** — SAM masks overlaid with color transparency on the original image, bounding boxes and labels drawn, displayed via matplotlib
6. **Supabase Logging** — All 15 parsed fields + image URL inserted into `food_logs` table

### Key Dependencies (New Build)

| Component | Library/Service | Notes |
|-----------|----------------|-------|
| Backend | FastAPI | Calls Replicate + OpenAI APIs |
| Food analysis | OpenAI GPT-4-turbo | Vision analysis, verification |
| Object detection | Replicate (YOLO-World) | Zero-shot text-prompt detection |
| Segmentation | Replicate (SAM 2/3) | Cloud GPU inference |
| Image processing | Pillow, NumPy | Base64 encoding, resizing |
| Database/Storage | Supabase | PostgreSQL + Storage |
| ML Infra | Replicate API | No local GPU needed |

### Key Dependencies (Prototype — reference only)

| Component | Library | Model/Service |
|-----------|---------|---------------|
| UI | Streamlit | — |
| Food analysis | openai | GPT-4-turbo (vision) |
| Object detection | ultralytics | YOLOv8m |
| Segmentation | segment-anything | SAM ViT-H |
| Image processing | OpenCV, Pillow, NumPy | — |
| Backend/Storage | supabase-py | Supabase (PostgreSQL + Storage) |

### Database Schema

Defined in `supabase_schema.sql`. Single table `food_logs` with 19 text columns for all analysis fields, timestamp, and image URL. RLS enabled with permissive "allow all" policy.

### Output Directories

- `food_library/` — Segmented individual food items (`{label}_{n}.jpg`)
- `favorite_meals/` — User-saved full plate images

## Version History

Versioned files (`gpt_bhojan_app_v0.py` through `v12.py`) represent the evolution:
- **v0-v7**: GPT-4 Vision analysis only, iterative prompt refinement
- **v8**: Added Supabase persistence
- **v9**: Added YOLO object detection
- **v10-v12**: Added SAM segmentation, food library extraction, mask complement verification

The latest version is always the highest-numbered file. Older versions are kept for reference.

## Known Constraints

- SAM checkpoint path is hardcoded to a Windows path (`C:/Users/naren/...`) — must be updated per environment
- SAM requires CUDA GPU (`sam.to("cuda")`) — will fail on CPU-only systems without modification
- `segment-anything` is imported but missing from `requirements.txt`
- GPT response parsing assumes exact numbered markdown format — non-conforming responses will cause index errors
- Each YOLO detection triggers a separate GPT-4 API call (cost scales with detection count)
