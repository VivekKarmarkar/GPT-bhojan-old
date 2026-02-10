# Phase 0 Test Report — GPT-Bhojan Backend

**Date:** Feb 9, 2026
**Server:** FastAPI at localhost:8000
**Pipeline:** GPT-4o (OpenAI) + Grounding DINO (Replicate)

---

## Test 1: Health Check

**Endpoint:** `GET /api/health`
**Result:** 200 OK
```json
{"status": "ok", "openai": true, "replicate": true}
```

---

## Test 2: Single Item — Grilled Salmon with Salad

**Endpoint:** `POST /api/analyze`
**Image:** `test_images/single_item.jpg`

| Field | Result |
|-------|--------|
| Description | Grilled salmon with fresh side salad, tomatoes, onions, cucumber, lemon wedge |
| Health Score | 9/10 |
| Total Calories | ~473 |
| Eat Frequency | Can eat daily |
| Satiety | 8/10 |
| Bloat | 2/10 |
| Tasty | 8/10 |
| Addiction | 3/10 |

**Detections (16):**
- Grilled salmon (0.63), Lemon wedge (0.70), Tomatoes (0.57), Red onions (0.57), Mixed green salad (0.45), Cucumber (0.37), Lettuce (0.29), Spinach (0.35)

**Timing:** GPT-4o=24.45s, DINO=1.55s, Total=26.0s

**Full results:** `analyze_single_item.json`

---

## Test 3: Crowded Plate — Grilled Meats & Seafood Spread

**Endpoint:** `POST /api/analyze`
**Image:** `test_images/crowded_plate.jpg`

| Field | Result |
|-------|--------|
| Description | Lavish spread of grilled meats, seafood, fresh fruits, roasted vegetables |
| Health Score | 6.5/10 |
| Total Calories | ~1575 |
| Eat Frequency | Occasional treat |

**Detections (22):**
- French fries (0.68), Grilled meats (0.62), Red wine (0.61), Carrots (0.56), Grapes (0.52), Bread rolls (0.50), Fresh fruits (0.49), Sauces (0.48), Pineapple (0.42), Mushrooms (0.38), Shrimp (0.29)

**Timing:** GPT-4o=23.35s, DINO=1.87s, Total=25.22s

**Full results:** `analyze_crowded_plate.json`

---

## Test 4: CLI Pipeline Test — Pizza

**Script:** `backend/test_pipeline.py`
**Image:** `test_images/indian_thali.jpg` (actually a pizza image)

| Field | Result |
|-------|--------|
| Health Score | 5/10 |
| Total Calories | ~1600 |
| Detections | 20 (pizza crust, olives, bell peppers, onions, tomato sauce, cheese) |

**Timing:** GPT-4o=17.86s, DINO=1.47s, Total=19.33s

---

## Summary

| Metric | Result |
|--------|--------|
| All endpoints working | Yes |
| API keys valid | OpenAI: Yes, Replicate: Yes |
| GPT-4o latency | 17-25s |
| Grounding DINO latency | 1.5-1.9s |
| Total pipeline latency | 19-26s |
| Detection accuracy | Good — correctly identifies food items with bounding boxes |
| Multi-item handling | Works well (22 detections on crowded plate) |

### Gotchas Found
1. Use `gpt-4o` not `gpt-4-turbo` — the latter doesn't support image_url in newer SDK
2. Replicate `FileOutput` must be cast to `str()` for Pydantic validation
