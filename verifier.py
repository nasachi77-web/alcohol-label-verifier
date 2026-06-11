import anthropic
import base64
import re
from models import ApplicationData, FieldResult, VerificationResult

# Standard TTB Government Warning Statement
GOVERNMENT_WARNING = (
    "GOVERNMENT WARNING: (1) According to the Surgeon General, women should not drink "
    "alcoholic beverages during pregnancy because of the risk of birth defects. "
    "(2) Consumption of alcoholic beverages impairs your ability to drive a car or "
    "operate machinery, and may cause health problems."
)

def _get_client() -> anthropic.Anthropic:
    """Lazy singleton created on first call so module import does not require the key."""
    if not hasattr(_get_client, "_instance"):
        _get_client._instance = anthropic.Anthropic()
    return _get_client._instance


def encode_image(image_bytes: bytes, media_type: str) -> str:
    return base64.standard_b64encode(image_bytes).decode("utf-8")


def normalize(text: str) -> str:
    """Normalize text for fuzzy comparison (lowercase, collapse whitespace)."""
    return re.sub(r"\s+", " ", text.strip().lower())


def fuzzy_match(expected: str, extracted: str) -> bool:
    """Case-insensitive, whitespace-normalized comparison."""
    return normalize(expected) == normalize(extracted)


def check_government_warning(extracted_text: str) -> tuple[bool, bool]:
    """Returns (present, exact_match)."""
    present = "GOVERNMENT WARNING:" in extracted_text
    normalized_extracted = normalize(extracted_text)
    normalized_required = normalize(GOVERNMENT_WARNING)
    exact = normalized_required in normalized_extracted
    return present, exact


def verify_label(
    image_bytes: bytes,
    media_type: str,
    filename: str,
    app_data: ApplicationData,
) -> VerificationResult:
    """Send label image to Claude, extract fields, compare against application data."""
    import json

    image_b64 = encode_image(image_bytes, media_type)

    prompt = (
        "You are an alcohol label compliance reviewer for the TTB.\n\n"
        "Carefully examine this alcohol beverage label image and extract ALL text you can see.\n\n"
        "Return ONLY valid JSON with these fields:\n"
        "brand_name, class_type, alcohol_content, net_contents, producer_name, "
        "producer_address, country_of_origin, government_warning_full_text, all_text"
    )

    try:
        message = _get_client().messages.create(
            model="claude-haiku-4-5",
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": image_b64}},
                    {"type": "text", "text": prompt},
                ],
            }],
        )

        raw_response = message.content[0].text.strip()
        if raw_response.startswith("```"):
            raw_response = re.sub(r"^```[a-z]*\n?", "", raw_response)
            raw_response = re.sub(r"\n?```$", "", raw_response)
        extracted = json.loads(raw_response)

    except Exception as e:
        return VerificationResult(
            filename=filename, overall_passed=False, fields=[],
            government_warning_present=False, government_warning_exact=False,
            error=f"Failed to analyze image: {str(e)}",
        )

    field_results: list[FieldResult] = []

    def check_field(field_key, label, expected_val, extracted_val):
        if expected_val is None:
            return FieldResult(field=field_key, expected=None, extracted=extracted_val,
                               passed=True, note="Not provided in application — not checked")
        if extracted_val is None:
            return FieldResult(field=field_key, expected=expected_val, extracted=None,
                               passed=False, note="Field not found on label")
        passed = fuzzy_match(expected_val, extracted_val)
        return FieldResult(field=field_key, expected=expected_val, extracted=extracted_val,
                           passed=passed, note=None if passed else "Value does not match application data")

    field_results.append(check_field("brand_name", "Brand Name", app_data.brand_name, extracted.get("brand_name")))
    field_results.append(check_field("class_type", "Class/Type", app_data.class_type, extracted.get("class_type")))
    field_results.append(check_field("alcohol_content", "Alcohol Content", app_data.alcohol_content, extracted.get("alcohol_content")))
    field_results.append(check_field("net_contents", "Net Contents", app_data.net_contents, extracted.get("net_contents")))
    field_results.append(check_field("producer_name", "Producer Name", app_data.producer_name, extracted.get("producer_name")))
    field_results.append(check_field("producer_address", "Producer Address", app_data.producer_address, extracted.get("producer_address")))
    field_results.append(check_field("country_of_origin", "Country of Origin", app_data.country_of_origin, extracted.get("country_of_origin")))

    all_text = extracted.get("all_text", "") or ""
    gov_warning_text = extracted.get("government_warning_full_text", "") or ""
    present, exact = check_government_warning(all_text + " " + gov_warning_text)

    field_results.append(FieldResult(
        field="government_warning", expected=GOVERNMENT_WARNING,
        extracted=gov_warning_text or None, passed=present and exact,
        note=(None if (present and exact)
              else "GOVERNMENT WARNING: must be present in all caps with exact TTB wording"
              if not present else "Warning present but wording does not exactly match TTB requirements"),
    ))

    required_pass = all(r.passed for r in field_results if r.field in ("brand_name", "government_warning"))
    optional_pass = all(r.passed for r in field_results if r.field not in ("brand_name", "government_warning"))

    return VerificationResult(
        filename=filename, overall_passed=required_pass and optional_pass,
        fields=field_results, government_warning_present=present,
        government_warning_exact=exact, raw_extracted_text=all_text,
    )
