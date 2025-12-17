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

FOOTER_KEYWORDS = [
    "COMPLIANCE REPORT",
    "Rental Minimum Standards",
    "Property:",
    "Date:",
    "Page",
]


def extract_rms(text: str) -> dict:
    # --- PRESERVE STRUCTURE ---
    raw_lines = text.splitlines()
    lines = [l.strip() for l in raw_lines if l.strip()]

    # --- HEADER EXTRACTION ---
    property_address = ""
    generated_date = ""
    reference = ""

    for line in lines:
        if "Property" in line and "VIC" in line and not property_address:
            property_address = line.replace("Property", "").strip()
        if "Date:" in line and not generated_date:
            generated_date = line.split("Date:")[-1].strip()
        if "Compliance Report" in line and not reference:
            ref_match = re.search(r"Compliance Report\s*(\d+)", line)
            if ref_match:
                reference = ref_match.group(1)

    # --- CATEGORY BLOCKS ---
    category_blocks = {}
    current_category = None

    for line in lines:
        # Detect category header (exact match only)
        for cat in RMS_CATEGORIES:
            if line.lower() == cat.lower():
                current_category = cat
                category_blocks[current_category] = []
                break
        else:
            if current_category:
                # Skip boilerplate
                if any(k.lower() in line.lower() for k in FOOTER_KEYWORDS):
                    continue
                category_blocks[current_category].append(line)

    categories = []
    non_compliant_count = 0

    for cat in RMS_CATEGORIES:
        block_lines = category_blocks.get(cat, [])

        status = "Compliant"
        notes_lines = []

        for line in block_lines:
            if "non compliant" in line.lower():
                status = "Non compliant"
            elif line.lower().startswith("compliant"):
                status = "Compliant"
            else:
                notes_lines.append(line)

        notes = " ".join(notes_lines).strip()

        if status == "Non compliant":
            non_compliant_count += 1

        categories.append({
            "name": cat,
            "status": status,
            "notes": notes,
        })

    # --- SUMMARY TABLE HTML ---
    category_table = ""
    for c in categories:
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
    for c in categories:
        status_class = "ok" if c["status"] == "Compliant" else "bad"
        category_details += f"""
        <div class="category">
          <div class="category-name">{c['name']}</div>
          <div class="category-status {status_class}">{c['status']}</div>
          <div class="category-notes">{c['notes']}</div>
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
