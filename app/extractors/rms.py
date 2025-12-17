import re

RMS_CATEGORIES = [
    "Bathroom",
    "Electrical safety",
    "Lighting",
    "Kitchen",
    "Laundry",
    "Locks",
    "Heating",
    "Mould and damp",
    "Structural soundness",
    "Toilets",
    "Ventilation",
    "Vermin-proof bins",
    "Window coverings",
    "Windows",
]


def extract_rms(text: str) -> dict:
    clean_text = re.sub(r"\s+", " ", text)

    # --- HEADER FIELDS ---
    address_match = re.search(r"Property\s+(.+?VIC\s+\d{4})", clean_text)
    property_address = address_match.group(1) if address_match else ""

    date_match = re.search(r"Generated\s+on\s+(\d{1,2}\s+\w+\s+\d{4})", clean_text)
    generated_date = date_match.group(1) if date_match else ""

    ref_match = re.search(r"Compliance Report[:\s]+(\d+)", clean_text)
    reference = ref_match.group(1) if ref_match else ""

    overall_status = "Compliant"
    if re.search(r"Non\s+compliant", clean_text, re.IGNORECASE):
        overall_status = "One non compliant category identified"

    # --- CATEGORY EXTRACTION ---
    categories_data = []

    for i, category in enumerate(RMS_CATEGORIES):
        start = clean_text.lower().find(category.lower())
        end = (
            clean_text.lower().find(RMS_CATEGORIES[i + 1].lower())
            if i + 1 < len(RMS_CATEGORIES)
            else len(clean_text)
        )

        block = clean_text[start:end] if start != -1 else ""

        status = "Compliant"
        if re.search(r"non\s+compliant", block, re.IGNORECASE):
            status = "Non compliant"

        notes_match = re.search(
            r"(Compliant|Non compliant)\s*(.*)", block, re.IGNORECASE
        )
        notes = notes_match.group(2).strip() if notes_match else ""

        categories_data.append(
            {
                "name": category,
                "status": status,
                "notes": notes,
            }
        )

    # --- COUNTS ---
    non_compliant_count = sum(
        1 for c in categories_data if c["status"] == "Non compliant"
    )

    # --- SUMMARY TABLE HTML ---
    category_table = ""
    for c in categories_data:
        status_class = "status-ok" if c["status"] == "Compliant" else "status-bad"
        category_table += f"""
        <tr>
          <td>{c['name']}</td>
          <td class="{status_class}">{c['status']}</td>
          <td>{c['notes']}</td>
        </tr>
        """

    # --- DETAILED CATEGORY HTML ---
    category_details = ""
    for c in categories_data:
        status_class = "ok" if c["status"] == "Compliant" else "bad"
        category_details += f"""
        <div class="category">
          <div class="category-name">{c['name']}</div>
          <div class="category-status {status_class}">{c['status']}</div>
          <div class="category-notes">{c['notes']}</div>
        </div>
        """

    return {
        "property_address": property_address,
        "overall_status": overall_status,
        "generated_date": generated_date,
        "reference": reference,

        "non_compliant_count": non_compliant_count,
        "actions_required": non_compliant_count,

        "category_table": category_table,
        "category_details": category_details,
    }
