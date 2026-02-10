# GPT-Bhojan Progress Tracker

**Project**: Strava for Food — Personal Gamified Food Tracking App
**Started**: February 9, 2026
**Last Updated**: February 9, 2026

---

## Overall Status

| Phase | Name | Status | Notes |
|-------|------|--------|-------|
| 0 | Infrastructure & ML Setup | COMPLETE | Replicate-powered pipeline working |
| 1 | Core Backend API | IN PROGRESS | `/api/analyze` done, CRUD endpoints pending |
| 2 | React PWA Frontend — Core Screens | COMPLETE | 4 screens, end-to-end tested |
| 3 | Dashboard & Analytics | NOT STARTED | — |
| 4 | Strava Integration | NOT STARTED | — |
| 5 | Polish & Mobile Deployment | NOT STARTED | — |

---

## Phase 0: Infrastructure & ML Setup — COMPLETE

**Completed**: Feb 9, 2026

### What was built
- FastAPI backend skeleton at `backend/`
- Full AI pipeline: GPT-4o Vision → YOLO-World (Replicate) → NMS → GPT classification → lang-segment-anything (Replicate) → post-processing → visualization
- Pipeline timing: ~16-25s per image (GPT ~13s + segmentation ~3s parallel)
- Endpoints: `/api/analyze` (POST), `/api/health` (GET)
- Media serving via StaticFiles (`/media/visualizations/`, `/media/crops/`)

### Key decisions
- **Replicate cloud API** for all ML inference — no local GPU, CUDA, or torch needed
- `tmappdev/lang-segment-anything` for segmentation — combines Grounding DINO + SAM in one call (text prompt → pixel mask)
- `gpt-4o` for vision (not `gpt-4-turbo`) — better results
- Replicate `FileOutput` needs `str()` cast for URL extraction
- YOLO-World kept in pipeline for bounding box detection; lang-SAM does text-grounded segmentation per crop

### Files
- `backend/app/services/pipeline.py` — orchestrates full 6-step pipeline
- `backend/app/services/gpt_service.py` — GPT-4o vision analysis + per-crop classification
- `backend/app/services/detection.py` — YOLO-World via Replicate
- `backend/app/services/segmentation.py` — lang-SAM via Replicate, visualization builder
- `backend/app/services/nms.py` — cross-class IoU NMS
- `backend/app/services/image_store.py` — saves visualizations + crops to `/media/`
- `backend/app/models/schemas.py` — Pydantic response models
- `backend/app/utils/image.py` — resize, bytes↔numpy, JPEG encoding
- `backend/app/utils/parsing.py` — extract item names from GPT text
- `backend/app/config.py` — settings (API keys from env)
- `backend/app/main.py` — FastAPI app, CORS, routes

---

## Post-Processing Filters — COMPLETE

**Completed**: Feb 9, 2026
**File**: `backend/app/services/post_processing.py`

### What was built
4 quality filters running after segmentation, before visualization. Ordered cheapest-first to minimize API costs:

| # | Filter | Type | Cost | What it catches |
|---|--------|------|------|-----------------|
| 1 | Brightness | Local (PIL) | ~0ms | Failed SAM masks (mostly black crops) |
| 2 | Duplicate label merge | Local | ~0ms | "Pizza" detected 4x → keep 1 |
| 3 | Containment resolution | GPT text-only | ~0.5s/pair | "pistachio" inside "rasmalai" → keep rasmalai |
| 4 | GPT quality check | GPT-4o vision | ~1-2s parallel | Crop doesn't match label |

### Results
- **62 test images, 0 failures**
- Reduces raw segments from 1-19 down to 0-7 clean items per image
- Key wins: sushi 5→1, pizza 10→1, breakfast 18→4, donuts 12→1
- Adds only 1-4s to total pipeline time
- All filters are fail-open (keep item on error)

### Test suite
- 62 diverse food images across 5 categories (Indian, Asian, Western, Desserts, Edge cases)
- `backend/batch_test.py` — batch runner, saves input+result screenshots
- `test_results/batch_test_results.md` — full results table
- `test_results/screenshots/` — 111 files (62 inputs + 49 results)

---

## Phase 2: React PWA Frontend — COMPLETE

**Completed**: Feb 9, 2026

### What was built
- React PWA at `frontend/` — Vite + Tailwind v4 + React Router + lucide-react
- 4 screens working end-to-end:
  - **Home** — activity feed, stats overview
  - **Upload** — camera/file upload with drag-and-drop
  - **Results** — mask overlay hero image + food item cards with crops
  - **Library** — browse segmented food items
- Strava-inspired dark theme: `#0F0F1A` background, `#FC4C02` orange accent
- Animated score rings (ScoreRing component)
- Bottom nav with raised center camera button (hidden on Results page)
- Full pipeline tested in Chrome: Upload → Loading → Results → Library

### Key files
- `frontend/src/pages/` — Home.jsx, Upload.jsx, Results.jsx, Library.jsx
- `frontend/src/components/` — ScoreRing, StatCard, FoodChip, FoodItemCard, BottomNav, Layout
- `frontend/vite.config.js`, `frontend/tailwind.config.js`

### Running
```bash
cd frontend && npm run dev    # port 5173
cd backend && uvicorn app.main:app --port 8000   # or activate venv first
```

### Gotcha
- `formData.append('file', file)` — param name must match FastAPI endpoint's `file: UploadFile` parameter

---

## Phase 1: Core Backend API — IN PROGRESS

### Done
- `/api/analyze` — full pipeline endpoint (POST image → structured JSON with analysis, detections, segmentation, timing)
- `/api/health` — health check endpoint
- Media serving (visualizations + crops)

### Remaining
- [ ] `/api/meals` CRUD endpoints (create, list, get, delete)
- [ ] `/api/food-items` endpoints for food library (list, get, like/unlike)
- [ ] Supabase integration for meal persistence
- [ ] Image upload to Supabase Storage
- [ ] Health score computation and metric extraction (currently returned raw from GPT)
- [ ] Test concurrent requests

---

## What's Next

### Phase 3: Dashboard & Analytics
- Dashboard home screen with weekly summary
- Health trend charts (line graphs, bar charts)
- Streak tracking system ("Healthy Legend" etc.)
- Badge/achievement system
- Meal timing analytics and clustering
- Food frequency analysis

### Phase 4: Strava Integration
- Strava OAuth flow
- Pull running activities (distance, pace, duration)
- Combined food + running dashboard
- Cross-scoring multipliers

### Phase 5: Polish & Mobile Deployment
- Performance optimization for 2017 Android phone
- PWA "Add to Home Screen" verification
- Push notifications for streaks (optional)
- Loading states, error handling, edge case UX
- TWA wrapper for Play Store (future)

---

## Known Issues & Gotchas

| Issue | Details | Severity |
|-------|---------|----------|
| Some Indian foods fail segmentation | "dal", "rice", "dosa", "chole bhature" — lang-SAM can't find them | Medium |
| Mislabeled results | Biryani → "Calamari, Shrimp, Fish"; Butter chicken → "Glazed chicken wings" | Medium |
| Some images return 0 items | satay, poke bowl, hot dog, pasta — all filtered out by post-processing | Low |
| Pipeline time 16-45s | Acceptable for now, but mobile UX will need loading state polish | Low |
| No Supabase persistence yet | Meals analyzed but not saved — Phase 1 remaining work | High |

---

## Test Results Summary (Feb 9, 2026)

**62 images tested, 62 passed, 0 failures**
**Total test time: 1546s (~26 min)**

| Category | Images | Avg Time | Notes |
|----------|--------|----------|-------|
| Indian | 10 | ~22s | Dosa, chole bhature, pav bhaji, paneer tikka return 0 items |
| Asian | 10 | ~22s | Satay returns 0 items; bibimbap returns 6 (most detail) |
| Western | 10 | ~27s | Hot dog, pasta return 0 items; steak mislabeled as "grilled tofu" |
| Desserts | 11 | ~23s | Jalebi returns 0 items; all others identified correctly |
| Edge cases | 10 | ~27s | Loaded nachos returns 0; charcuterie returns 5 items (best) |
| Other | 11 | ~24s | Non-food correctly returns 0 items |

Full results: `test_results/batch_test_results.md`
Screenshots: `test_results/screenshots/`
