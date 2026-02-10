import re


ANALYSIS_FIELDS = [
    "description",
    "items",
    "calories",
    "total_calories",
    "health_score",
    "rationale",
    "macronutrient_estimate",
    "eat_frequency",
    "ideal_comparison",
    "mood_impact",
    "satiety_score",
    "bloat_score",
    "tasty_score",
    "addiction_score",
    "summary",
]


def parse_gpt_response(text: str) -> dict[str, str]:
    matches = re.findall(
        r"\d+\.\s\*\*.*?\*\*:\s*(.*?)(?=\n\d+\.|\Z)", text, re.DOTALL
    )
    return {
        field: matches[i].strip() if i < len(matches) else ""
        for i, field in enumerate(ANALYSIS_FIELDS)
    }


def extract_item_names(items_text: str) -> list[str]:
    lines = items_text.strip().splitlines()
    names = []
    for line in lines:
        cleaned = re.sub(r"^[-*\d.)\s]+", "", line).strip()
        if cleaned:
            names.append(cleaned)
    if not names and items_text.strip():
        names = [s.strip() for s in items_text.split(",") if s.strip()]
    return names
