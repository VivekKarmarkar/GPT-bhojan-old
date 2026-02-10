# GPT-Bhojan Vision: Strava for Food

## Core Concept

GPT-Bhojan is a personal, gamified food tracking app that creates a positive feedback loop between eating well and running. Eat healthy → motivated to run. Run → motivated to eat healthy. It is **Strava for Food** — visual, gamified, data-driven, and personal.

## User Context

- **Vivek** — intuitive eater (does not track macros), runner getting back into shape
- Uses Strava for running, wants food tracking to integrate with it
- Previous scrappy Streamlit prototype was already providing real value (eating spinach, grilled chicken, going for runs) until it crashed
- Not a lot of food variation — Indian cuisine focused
- Owns an older 2017 Android phone — app must work on it

## What This Is NOT

- Not a macro tracker — no calorie counting UX, no food diary spreadsheet
- Not social media — purely personal
- Not text-heavy — no walls of GPT text dumped on screen
- Not the existing Streamlit prototype — that code is reference for the AI architecture only

---

## Architecture

### AI Pipeline (Replicate-powered)

```
Food Photo Upload (phone/browser)
    ↓
FastAPI Backend receives image
    ↓
GPT-4 Vision Analysis (structured 15-point prompt, OpenAI API)
    ↓
YOLO-World Object Detection (Replicate API — zero-shot text prompts)
    ↓
SAM Segmentation (Replicate API — box or text prompts)
    ↓
GPT-4 Verification (A/B mask check per item, OpenAI API)
    ↓
Results: item labels, health score, metrics, segmented images
```

**Key change (Feb 9 2026):** ML inference (YOLO, SAM) runs on **Replicate cloud GPUs** via API, not locally. This eliminates all local GPU/CUDA/VRAM dependencies and ensures fast, scalable inference suitable for mobile latency requirements.

### ML Inference Strategy

- **Replicate** hosts YOLO-World and SAM models — no local GPU setup needed
- FastAPI backend calls Replicate API — no torch/CUDA dependency on server
- Optimize for **speed over peak accuracy** — mobile latency is the priority
- Models evaluated on Replicate playground by Claude via Chrome extension
- Forward-compatible: same API works whether backend is local or cloud-deployed

### Tech Stack

| Layer | Technology | Notes |
|-------|-----------|-------|
| Frontend | React (PWA) | Mobile-first, Strava-inspired UI |
| Backend | FastAPI | Python — calls Replicate + OpenAI APIs |
| AI/Vision | OpenAI GPT-4-turbo | Food analysis, item verification |
| Detection | YOLO-World (Replicate) | Zero-shot text-prompt detection |
| Segmentation | SAM 2/3 (Replicate) | Best available model on Replicate |
| ML Infra | Replicate API | Cloud GPU inference, no local setup |
| Database | Supabase (PostgreSQL) | Food logs, user data, analytics |
| Storage | Supabase Storage | Food images, segmented items |
| Running Data | Strava API | OAuth, activity pulls |
| Deployment | PWA → TWA (Play Store) | Forward-compatible |

### Data Model (extends existing `food_logs`)

Core entities:
- **Meals** — timestamp, photo, GPT analysis, health score, all metrics
- **Food Items** — segmented items from meals, labels, liked status, frequency
- **Running Activities** — pulled from Strava (distance, duration, pace, date)
- **Streaks & Badges** — earned achievements, streak counters
- **Meal Timing** — derived analytics on when meals happen

---

## Features

### Food Analysis (core pipeline)
- Upload food photo → full AI pipeline runs
- Clean visual display of results (not raw text)
- Health score prominently displayed with visual indicator
- Individual food items shown as segmented cards

### Food Library
- Every segmented food item saved with label
- Ability to "like" / favorite specific food items
- Per-item analytics: how often eaten, health impact over time
- Browse and search your food history

### Gamification
- **Streaks**: consecutive days of healthy eating (e.g., "Healthy Legend" for spinach 5x in a row)
- **Badges**: earned through consistent behavior patterns
- **Combined scores**: food health + running activity = overall wellness score
- Visual reward system inspired by Strava's kudos/achievements

### Strava Integration
- OAuth connection to Strava account
- Pull running activities (distance, pace, duration)
- Combined dashboard: food + running in one view
- Cross-motivation: running boosts your food score multiplier and vice versa

### Meal Timing Analytics
- Automatic timestamp when meals are logged
- Clustering analysis: when do you typically eat?
- Pattern detection: meal regularity, late-night eating, gaps
- Time-of-day health correlation

### Dashboard
- Strava-inspired visual design — clean, graphical, card-based
- Activity feed of recent meals and runs
- Weekly/monthly health trend graphs
- Streak counters and badge showcase
- No walls of text — metrics displayed as visual indicators, icons, and charts

---

## Development Phases

### Phase 0: Infrastructure & ML Setup
**Goal**: Set up Replicate-powered ML pipeline and FastAPI skeleton.

Tasks:
- Explore Replicate models via Chrome extension: test YOLO-World, SAM 2/3 for speed and quality
- Benchmark inference latency on Replicate (target: fast enough for mobile)
- Extract boilerplate API code from Replicate playground
- Set up FastAPI project skeleton that calls Replicate API
- Confirm Supabase connection and schema
- Create `.env` with Replicate API key, OpenAI key, Supabase creds

Testing:
- Run pipeline on 3-5 diverse food images via Replicate API
- Compare model options: speed vs quality trade-offs
- Test edge cases: poorly lit image, single-item plate, crowded plate
- Measure end-to-end latency: image upload → Replicate inference → results back

### Phase 1: Core Backend API
**Goal**: FastAPI backend that accepts a food photo and returns full analysis.

Tasks:
- `/api/analyze` endpoint: accepts image, runs full pipeline, returns structured JSON
- `/api/meals` CRUD endpoints for meal history
- `/api/food-items` endpoints for the food library
- Supabase integration for persistence
- Image upload to Supabase Storage
- Health score computation and metric extraction

Testing:
- API tests with curl/httpie for all endpoints
- Test with adversarial images: non-food image, blurry photo, empty plate
- Verify Supabase records are created correctly
- Test concurrent requests (two uploads at once)

### Phase 2: React PWA Frontend — Core Screens
**Goal**: Mobile-first UI with the core meal logging flow.

Tasks:
- PWA scaffold with React + service worker + manifest
- Camera/upload screen for food photos
- Analysis results screen (visual, not text-heavy)
- Meal history feed (Strava activity feed style)
- Food library browse screen with like/favorite
- Responsive layout that works on old Android Chrome

Testing:
- Chrome extension browser testing on laptop
- Test on multiple viewport sizes (phone, tablet, desktop)
- Test camera upload flow
- Verify PWA install prompt works
- Test offline behavior (service worker caching)
- Adversarial: rapid successive uploads, very large image file

### Phase 3: Dashboard & Analytics
**Goal**: Visual dashboard with trends, streaks, and meal timing.

Tasks:
- Dashboard home screen with weekly summary
- Health trend charts (line graphs, bar charts)
- Streak tracking system and display
- Badge/achievement system ("Healthy Legend", etc.)
- Meal timing analytics and clustering visualization
- Food frequency analysis

Testing:
- Populate with 2 weeks of mock data, verify charts render correctly
- Test streak logic: does it reset properly? Edge cases around midnight?
- Test with no data (empty state), single entry, many entries
- Visual testing via Chrome extension

### Phase 4: Strava Integration
**Goal**: Connect to Strava, pull running data, unified dashboard.

Tasks:
- Strava OAuth flow (register app, handle tokens)
- Pull activity data (runs, distance, pace, duration)
- Combined food + running dashboard view
- Cross-scoring: running boosts food multiplier and vice versa
- Activity feed showing both meals and runs chronologically

Testing:
- OAuth flow end-to-end (authorize, callback, token storage)
- Verify activity data pulls correctly
- Test with no Strava data, lots of Strava data
- Combined score calculation with various food + run combinations
- Token refresh handling

### Phase 5: Polish & Mobile Deployment
**Goal**: Production-ready app that works on Vivek's Android phone.

Tasks:
- Performance optimization for older devices
- PWA "Add to Home Screen" verification on Android Chrome
- Push notifications for streak reminders (optional)
- Loading states, error handling, edge case UX
- TWA wrapper for Play Store (optional, future)

Testing:
- Test on actual 2017 Android phone
- Performance profiling: load times, image upload speed
- Test with poor network connectivity
- Full end-to-end user journey: upload → analyze → view dashboard → check Strava

---

## Design Principles

1. **Visual over textual** — Show, don't tell. Health scores as colored rings, not paragraphs.
2. **Simple metrics** — No macro counting. Health score, streaks, badges, meal timing.
3. **Forward compatible** — Works in browser today, Play Store tomorrow.
4. **One phase at a time** — Build, test with adversarial examples, verify, then move on.
5. **Strava aesthetic** — Clean, sporty, card-based, activity-feed-driven.

## Development Workflow

1. Swarm agents work in parallel within each phase (bypass permissions for speed)
2. Team lead (Claude) integrates and tests via Chrome extension browser automation
3. Results reported to Vivek before advancing to next phase
4. No phase runs until the previous phase is tested and approved
