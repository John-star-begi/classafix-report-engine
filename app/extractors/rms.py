import re

# Order must match RMS legislation and template
CATEGORIES = [
    ("bathroom", "Bathroom"),
    ("electrical_safety", "Electrical Safety"),
    ("lighting", "Lighting"),
    ("kitchen", "Kitchen"),
    ("laundry", "Laundry"),
    ("locks", "Locks"),
    ("heating", "Heating"),
    ("mould_and_damp", "Mould & damp"),
    ("structural_soundness", "Structural soundness"),
    ("toilets", "Toilets"),
    ("ventilation", "Ventilation"),
    ("vermin_proof_bins", "Vermin-proof bins"),
    ("window_coverings", "Window coverings"),
    ("windows", "Windows"),
]


def extract_rms(text: str) -> dict:
    """
    FINAL RMS extractor.

    Source of truth:
    - Detailed category section
    - Explicit text: COMPLIANT / NON COMPLIANT

    Summary table is GENERATED, not read.
    Checklist text is ignored.
    """

    lines = [l.strip() for l in text.splitlines() if l.strip()]
    lower_lines = [l.lower() for l in lines]

    # -------------------------------------------------
    # HEADER EXTRACTION (best effort)
    # -------------------------------------------------
    property_address = ""
    generated_date = ""
    reference = ""

    for l in lines:
        if not property_address and "attended:" in l.lower():
            property_address = l.split("attended:", 1)[-1].strip()

        if not generated_date and "date:" in l.lower():
            generated_date = l.split("date:", 1)[-1].strip()

        if not reference and "compliance report" in l.lower():
            m = re.search(r"\d+", l)
            if m:
                reference = m.group(0)

    # -------------------------------------------------
    # INIT CATEGORIES
    # -------------------------------------------------
    categories = {}
    for slug, name in CATEGORIES:
        categories[slug] = {
            "name": name,
            "status": "Compliant",   # default
            "status_class": "ok",
            "note": "",              # manual only
        }

    # -------------------------------------------------
    # FIND DETAILED SECTION START
    # -------------------------------------------------
    try:
        start_idx = next(
            i for i, l in enumerate(lower_lines)
            if "category assessment" in l
        )
    except StopIteration:
        # Fallback: scan entire document
        start_idx = 0

    detail_lines = lines[start_idx:]

    # -------------------------------------------------
    # EXTRACT STATUS FROM CATEGORY HEADERS
    # -------------------------------------------------
    for i, line in enumerate(detail_lines):
        for slug, name in CATEGORIES:
            if name.lower() in line.lower():
                # Check same line + next line for status text
                window = " ".join(detail_lines[i:i+2]).upper()

                if "NON COMPLIANT" in window:
                    categories[slug]["status"] = "Non compliant"
                    categories[slug]["status_class"] = "bad"

                elif "COMPLIANT" in window:
                    categories[slug]["status"] = "Compliant"
                    categories[slug]["status_class"] = "ok"

    # -------------------------------------------------
    # COUNTS
    # -------------------------------------------------
    non_compliant_count = sum(
        1 for c in categories.values()
        if c["status"] == "Non compliant"
    )

    overall_status = (
        "One non compliant category identified"
        if non_compliant_count > 0
        else "Compliant"
    )

    # -------------------------------------------------
    # BUILD SUMMARY TABLE (GENERATED)
    # -------------------------------------------------
    category_table = ""
    for slug, name in CATEGORIES:
        c = categories[slug]
        td_class = "status-bad" if c["status"] == "Non compliant" else "status-ok"

        category_table += f"""
        <tr>
          <td>{name}</td>
          <td class="{td_class}">{c['status']}</td>
          <td></td>
        </tr>
        """

    # -------------------------------------------------
    # FINAL PAYLOAD
    # -------------------------------------------------
    return {
        "property_address": property_address,
        "overall_status": overall_status,
        "generated_date": generated_date,
        "reference": reference,
        "non_compliant_count": non_compliant_count,
        "actions_required": non_compliant_count,
        "category_table": category_table,
        "categories": categories,
    }
