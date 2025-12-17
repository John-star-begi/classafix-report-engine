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


def normalize(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().lower())


def extract_rms(text: str) -> dict:
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    # --------------------------------------------------
    # HEADER
    # --------------------------------------------------
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

    # --------------------------------------------------
    # SPLIT DOCUMENT INTO SECTIONS
    # --------------------------------------------------
    summary_lines = []
    detail_lines = []

    in_details = False
    for l in lines:
        if "Category assessment details" in l:
            in_details = True
            continue

        if in_details:
            detail_lines.append(l)
        else:
            summary_lines.append(l)

    # --------------------------------------------------
    # SUMMARY TABLE → COMPLIANCE STATUS
    # --------------------------------------------------
    status_map = {}
    note_map = {}

    for cat in RMS_CATEGORIES:
        status_map[cat] = "Compliant"
        note_map[cat] = ""

    for i, l in enumerate(summary_lines):
        for cat in RMS_CATEGORIES:
            if normalize(cat) == normalize(l):
                # Look ahead for status
                for j in range(i + 1, min(i + 6, len(summary_lines))):
                    if "non compliant" in summary_lines[j].lower():
                        status_map[cat] = "Non compliant"
                        # optional note
                        note_map[cat] = summary_lines[j]
                        break
                    if "compliant" in summary_lines[j].lower():
                        status_map[cat] = "Compliant"
                        break

    non_compliant_count = sum(
        1 for s in status_map.values() if s == "Non compliant"
    )

    # --------------------------------------------------
    # DETAIL SECTION → CHECKLIST
    # --------------------------------------------------
    checklist = {c: [] for c in RMS_CATEGORIES}
    current_cat = None

    for l in detail_lines:
        for cat in RMS_CATEGORIES:
            if re.match(rf"^{cat}\b", l, re.IGNORECASE):
                current_cat = cat
                break
        else:
            if current_cat:
                # Ignore boilerplate
                if any(x in l for x in ["COMPLIANCE REPORT", "Page"]):
                    continue
                # Ignore pure status words
                if l.lower() in ["compliant", "non compliant"]:
                    continue
                checklist[current_cat].append(l)

    # --------------------------------------------------
    # HTML BUILD
    # --------------------------------------------------
    category_table = ""
    category_details = ""

    for cat in RMS_CATEGORIES:
        status = status_map[cat]
        status_class = "status-ok" if status == "Compliant" else "status-bad"

        category_table += f"""
        <tr>
          <td>{cat}</td>
          <td class="{status_class}">{status}</td>
          <td>{note_map.get(cat, "")}</td>
        </tr>
        """

        checklist_html = ""
        for item in checklist[cat]:
            checklist_html += f"<li>{item}</li>"

        short_class = "ok" if status == "Compliant" else "bad"

        category_details += f"""
        <div class="category">
          <div class="category-header">
            <div>{cat}</div>
            <div class="category-status {short_class}">{status}</div>
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
