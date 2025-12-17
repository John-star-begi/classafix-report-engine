import re

CATEGORIES = [
    ("bathroom", "Bathroom"),
    ("electrical_safety", "Electrical safety"),
    ("lighting", "Lighting"),
    ("kitchen", "Kitchen"),
    ("laundry", "Laundry"),
    ("locks", "Locks"),
    ("heating", "Heating"),
    ("mould_and_damp", "Mould and damp"),
    ("structural_soundness", "Structural soundness"),
    ("toilets", "Toilets"),
    ("ventilation", "Ventilation"),
    ("vermin_proof_bins", "Vermin-proof bins"),
    ("window_coverings", "Window coverings"),
    ("windows", "Windows"),
]


def extract_rms(text: str) -> dict:
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    # ---------------- HEADER ----------------
    property_address = ""
    generated_date = ""
    reference = ""

    for l in lines:
        if not property_address and "Property" in l and "VIC" in l:
            property_address = l.replace("Property", "").strip()

        if not generated_date and "Date:" in l:
            generated_date = l.split("Date:", 1)[-1].strip()

        if not reference and "Compliance Report" in l:
            m = re.search(r"\d+", l)
            if m:
                reference = m.group(0)

    # ---------------- SUMMARY EXTRACTION ----------------
    categories = {}
    for slug, name in CATEGORIES:
        categories[slug] = {
            "name": name,
            "status": "Compliant",
            "status_class": "ok",
            "note": "",
        }

    # Look for category rows and detect X symbol
    for i, line in enumerate(lines):
        for slug, name in CATEGORIES:
            if name.lower() in line.lower():
                # Check same line + next line for X
                window = " ".join(lines[i:i+2])

                if " X " in f" {window} " or " x " in f" {window} ":
                    categories[slug]["status"] = "Non compliant"
                    categories[slug]["status_class"] = "bad"

    non_compliant_count = sum(
        1 for c in categories.values() if c["status"] == "Non compliant"
    )

    # ---------------- SUMMARY TABLE HTML ----------------
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

    overall_status = (
        "One non compliant category identified"
        if non_compliant_count > 0
        else "Compliant"
    )

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
