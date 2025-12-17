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

SUMMARY_HEADER = "Category Status"


def extract_rms(text: str) -> dict:
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    # ---------- HEADER ----------
    property_address = ""
    generated_date = ""
    reference = ""

    for l in lines:
        if "Property" in l and "VIC" in l and not property_address:
            property_address = l.replace("Property", "").strip()
        if "Date:" in l and not generated_date:
            generated_date = l.split("Date:")[-1].strip()
        if "Compliance Report" in l and not reference:
            m = re.search(r"(\d+)", l)
            if m:
                reference = m.group(1)

    # ---------- SUMMARY TABLE ----------
    summary_status = {}
    summary_notes = {}

    for cat in RMS_CATEGORIES:
        for l in lines:
            if l.startswith(cat):
                if "Non compliant" in l:
                    summary_status[cat] = "Non compliant"
                else:
                    summary_status[cat] = "Compliant"

                parts = l.split(cat, 1)
                summary_notes[cat] = parts[1].replace("Compliant", "").replace("Non compliant", "").strip()
                break
        else:
            summary_status[cat] = "Compliant"
            summary_notes[cat] = ""

    non_compliant_count = sum(1 for s in summary_status.values() if s == "Non compliant")

    # ---------- CHECKLIST ----------
    checklist_blocks = {c: [] for c in RMS_CATEGORIES}
    current = None

    for l in lines:
        if l in RMS_CATEGORIES:
            current = l
            continue

        if current:
            if any(l.startswith(c) for c in RMS_CATEGORIES):
                current = None
            elif "COMPLIANCE REPORT" in l or "Page" in l:
                continue
            else:
                checklist_blocks[current].append(l)

    # ---------- HTML BUILD ----------
    category_table = ""
    category_details = ""

    for cat in RMS_CATEGORIES:
        status = summary_status[cat]
        status_class = "status-ok" if status == "Compliant" else "status-bad"

        category_table += f"""
        <tr>
          <td>{cat}</td>
          <td class="{status_class}">{status}</td>
          <td>{summary_notes[cat]}</td>
        </tr>
        """

        checklist_html = ""
        for item in checklist_blocks.get(cat, []):
            if len(item) < 4:
                continue
            checklist_html += f"<li>{item}</li>"

        status_class_short = "ok" if status == "Compliant" else "bad"

        category_details += f"""
        <div class="category">
          <div class="category-header">
            <div>{cat}</div>
            <div class="category-status {status_class_short}">{status}</div>
          </div>
          <ul class="checklist">
            {checklist_html}
          </ul>
        </div>
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
        "category_details": category_details,
    }
