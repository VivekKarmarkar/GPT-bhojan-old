from openai import OpenAI

from app.config import settings
from app.utils.image import image_bytes_to_data_uri
from app.utils.parsing import parse_gpt_response

FOOD_ANALYSIS_PROMPT = (
    "You are GPT Bhojan, a food and nutrition assistant.\n\n"
    "Please analyze the food in this image and return a structured analysis in this format:\n\n"
    "1. **Description**: A short paragraph describing the food.\n"
    "2. **Items**: A list of distinct items on the plate.\n"
    "3. **Calories**: Estimate calories for each item and the total.\n"
    "4. **Total Calories**: Tell me the total calorie estimate.\n"
    "5. **Health Score**: Give a score from 0 to 10 (real number).\n"
    "6. **Rationale**: Explain why this score was given.\n"
    "7. **Macronutrient Estimate**: Rough protein (g), fat (g), carbs (g).\n"
    "8. **Eat Frequency**: Label as one of ['Can eat daily', 'Occasional treat', 'Avoid except rarely'].\n"
    "9. **Comparison to Ideal Meal**: Brief comment on how this compares to a typical healthy benchmark meal.\n"
    "10. **Mood/Energy Impact**: What short-term effects might this food have (e.g., energy crash, satiety)?\n"
    "11. **Satiety Score**: Score from 0 to 10 based on how full this meal is likely to make the person feel.\n"
    "12. **Bloat Score**: Score from 0 to 10 based on how much bloating this meal might cause.\n"
    "13. **Tasty Score**: Score from 0 to 10 based on how tasty this meal is likely to be.\n"
    "14. **Addiction Score**: Score from 0 to 10 based on how likely this meal is to trigger addictive eating patterns.\n"
    "15. **Summary**: Total calorie estimate with final health score and brief closing note."
)

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=settings.openai_api_key)
    return _client


def analyze_food_image(image_bytes: bytes) -> tuple[dict[str, str], str]:
    client = _get_client()
    data_uri = image_bytes_to_data_uri(image_bytes)

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": FOOD_ANALYSIS_PROMPT},
                    {"type": "image_url", "image_url": {"url": data_uri}},
                ],
            }
        ],
    )
    raw_text = response.choices[0].message.content
    parsed = parse_gpt_response(raw_text)
    return parsed, raw_text


def check_api_key() -> bool:
    try:
        client = _get_client()
        client.models.list()
        return True
    except Exception:
        return False


def classify_food_crop(crop_bytes: bytes, description: str) -> str | None:
    """Ask GPT-4o if a cropped image matches a food item from the plate description.

    Returns the food label string, or None if not a described food item.
    """
    try:
        client = _get_client()
        data_uri = image_bytes_to_data_uri(crop_bytes)

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                f"Given this description of the full plate: {description}. "
                                "Is this crop one of the described food items? "
                                "Reply with just the food name or 'None'."
                            ),
                        },
                        {"type": "image_url", "image_url": {"url": data_uri}},
                    ],
                }
            ],
            max_tokens=50,
        )

        answer = response.choices[0].message.content.strip()
        if answer.lower() == "none":
            return None
        return answer
    except Exception:
        return None
