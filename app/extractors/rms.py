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

STATUS_WORDS = ["non compliant", "non-compliant", "compliant"]


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().lower())


def _find_first_index(lines, predicate):
    for i, l in enumerate(lines):
        if predicate(l):
            return i
    return -1


def extract_rms(text: str) -> dict:
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    # Header values
    property_address = ""
    generated_date = ""
    reference = ""

    for l in lines:
        if not property_address and "Property" in l and "VIC" in l:
            property_address = l.replace("Property", "").strip()
        if not generated_date and "Date:" in l:
            generated_date = l.split("Date:", 1)[-1].strip()
        if not reference and "Compliance Report" in l:
            m = re.search(r"(\d{3,})", l)
            if m:
                reference = m.group(1)

    # Try to locate the summary table region
    start_idx = _find_first_index(lines, lambda x: "Category" in x and "Status" in x)
    if start_idx == -1:
        start_idx = 0

    # Stop before the detailed section if present
    end_idx = _find_first_index(lines, lambda x: "Category assessment details" in x)
    if end_idx == -1:
        end_idx = len(lines)

    summary_lines = lines[start_idx:end_idx]

    categories = {}
    for slug, name in CATEGORIES:
        categories[slug] = {
            "name": name,
            "status": "Compliant",
            "status_class": "ok",
            "note": "",
        }

    # Robust scan: find a category line, then find the nearest status token after it
    for slug, name in CATEGORIES:
        name_norm = _norm(name)

        idx = _find_first_index(summary_lines, lambda x: _norm(x) == name_norm or _norm(x).startswith(name_norm + " "))
        if idx == -1:
            continue

        window = summary_lines[idx: min(idx + 8, len(summary_lines))]

        status = None
        note = ""

        for w in window:
            lw = _norm(w)
            if "non compliant" in lw or "non-compliant" in lw:
                status = "Non compliant"
                # If the note is on the same line after the status, keep it
                note = w
                break
            if lw == "compliant" or lw.endswith(" compliant") or " compliant" in lw:
                # Only accept compliant if it is a standalone status token or close to it
                if lw == "compliant" or lw.endswith(" compliant"):
                    status = "Compliant"
                    break

        # Note cleanup: remove category name and status words
        if note:
            cleaned = note
            cleaned = re.sub(re.escape(name), "", cleaned, flags=re.IGNORECASE).strip()
            cleaned = re.sub(r"\bNon[- ]compliant\b", "", cleaned, flags=re.IGNORECASE).strip()
            cleaned = re.sub(r"\bCompliant\b", "", cleaned, flags=re.IGNORECASE).strip()
            # Remove any leftover separators
            cleaned = cleaned.strip(" :-|")
            note = cleaned

        if status:
            categories[slug]["status"] = status
            categories[slug]["status_class"] = "bad" if status == "Non compliant" else "ok"
            categories[slug]["note"] = note

    non_compliant_count = sum(1 for c in categories.values() if c["status"] == "Non compliant")

    # Build the summary table HTML
    category_table = ""
    for slug, name in CATEGORIES:
        c = categories[slug]
        status_td_class = "status-bad" if c["status"] == "Non compliant" else "status-ok"
        category_table += f"""
        <tr>
          <td>{c['name']}</td>
          <td class="{status_td_class}">{c['status']}</td>
          <td>{c['note']}</td>
        </tr>
        """

    overall_status = "Compliant"
    if non_compliant_count > 0:
        overall_status = "One non compliant category identified"

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
