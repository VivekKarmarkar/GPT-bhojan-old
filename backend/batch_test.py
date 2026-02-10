"""Batch test — run pipeline on ALL images in test_images/, save results.

Usage:
    cd backend/
    python batch_test.py
"""

import os
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.services.pipeline import run_pipeline
from app.utils.image import resize_if_needed

TEST_DIR = Path(__file__).resolve().parent.parent / "test_images"
RESULTS_DIR = Path(__file__).resolve().parent.parent / "test_results"
SCREENSHOTS_DIR = RESULTS_DIR / "screenshots"
MEDIA_DIR = Path(__file__).resolve().parent / "media"


def get_all_images() -> list[Path]:
    images = []
    for ext in ("*.jpg", "*.jpeg", "*.png"):
        images.extend(TEST_DIR.glob(ext))
    return sorted(images)


def run_single(img_path: Path) -> dict:
    """Run pipeline on one image, return result dict."""
    stem = img_path.stem
    print(f"\n{'='*60}")
    print(f"  {stem}")
    print(f"{'='*60}")

    image_bytes = img_path.read_bytes()
    image_bytes = resize_if_needed(image_bytes, max_dim=2048)

    t0 = time.time()
    try:
        response = run_pipeline(image_bytes)
        elapsed = time.time() - t0

        seg = response.segmentation
        timing = response.timing

        # Copy visualization to screenshots
        if seg.visualization_url:
            vis_filename = seg.visualization_url.split("/")[-1]
            vis_src = MEDIA_DIR / "visualizations" / vis_filename
            if vis_src.exists():
                shutil.copy2(vis_src, SCREENSHOTS_DIR / f"{stem}_result.jpg")

        # Copy input image to screenshots
        shutil.copy2(img_path, SCREENSHOTS_DIR / f"{stem}_input.jpg")

        items = [item.label for item in seg.segmented_items]
        pp_input = timing.get("pp_input_count", "?")
        pp_output = timing.get("pp_output_count", "?")

        result = {
            "image": stem,
            "status": "OK",
            "total_s": round(elapsed, 1),
            "items_before_pp": pp_input,
            "items_after_pp": pp_output,
            "final_items": items,
            "seg_count": seg.item_count,
            "has_visualization": bool(seg.visualization_url),
        }

        print(f"  OK — {seg.item_count} items in {elapsed:.1f}s: {items}")
        return result

    except Exception as exc:
        elapsed = time.time() - t0
        # Still copy input
        shutil.copy2(img_path, SCREENSHOTS_DIR / f"{stem}_input.jpg")
        print(f"  FAIL — {exc}")
        return {
            "image": stem,
            "status": f"FAIL: {exc}",
            "total_s": round(elapsed, 1),
            "items_before_pp": 0,
            "items_after_pp": 0,
            "final_items": [],
            "seg_count": 0,
            "has_visualization": False,
        }


def write_summary(results: list[dict]):
    """Write markdown summary of all results."""
    summary_path = RESULTS_DIR / "batch_test_results.md"

    ok = [r for r in results if r["status"] == "OK"]
    fail = [r for r in results if r["status"] != "OK"]

    lines = [
        "# Batch Pipeline Test Results",
        "",
        f"**Date**: {time.strftime('%Y-%m-%d %H:%M')}",
        f"**Images tested**: {len(results)}",
        f"**Passed**: {len(ok)} | **Failed**: {len(fail)}",
        f"**Total time**: {sum(r['total_s'] for r in results):.0f}s",
        "",
        "## Results",
        "",
        "| # | Image | Status | Time | Before PP | After PP | Final Items |",
        "|---|-------|--------|------|-----------|----------|-------------|",
    ]

    for i, r in enumerate(results, 1):
        items_str = ", ".join(r["final_items"]) if r["final_items"] else "—"
        if len(items_str) > 60:
            items_str = items_str[:57] + "..."
        lines.append(
            f"| {i} | {r['image']} | {r['status'][:4]} | {r['total_s']}s "
            f"| {r['items_before_pp']} | {r['items_after_pp']} | {items_str} |"
        )

    if fail:
        lines.extend(["", "## Failures", ""])
        for r in fail:
            lines.append(f"- **{r['image']}**: {r['status']}")

    lines.extend(["", "## Screenshots", ""])
    lines.append(f"All input/result pairs saved to `test_results/screenshots/`")
    lines.append(f"- `{{name}}_input.jpg` — original image")
    lines.append(f"- `{{name}}_result.jpg` — pipeline visualization with mask overlays")

    summary_path.write_text("\n".join(lines))
    print(f"\nSummary written to {summary_path}")


def main():
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

    images = get_all_images()
    print(f"Found {len(images)} test images in {TEST_DIR}")

    results = []
    for i, img_path in enumerate(images, 1):
        print(f"\n[{i}/{len(images)}]", end="")
        result = run_single(img_path)
        results.append(result)

    write_summary(results)

    print(f"\n{'='*60}")
    print(f"DONE: {len(results)} images tested")
    ok = sum(1 for r in results if r["status"] == "OK")
    print(f"  Passed: {ok}/{len(results)}")
    print(f"  Screenshots: {SCREENSHOTS_DIR}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
