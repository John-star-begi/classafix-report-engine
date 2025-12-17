from weasyprint import HTML
from jinja2 import Template
import tempfile
import os
import uuid


def render_pdf(template_name: str, data: dict, photos: list) -> bytes:
    template_path = f"app/templates/{template_name}"

    with open(template_path, "r") as f:
        template_html = f.read()

    photo_html = ""
    temp_files = []

    for photo in photos:
        if not photo.filename:
            continue

        ext = os.path.splitext(photo.filename)[1]
        tmp_path = f"/tmp/{uuid.uuid4()}{ext}"

        with open(tmp_path, "wb") as f:
            f.write(photo.file.read())

        temp_files.append(tmp_path)

        photo_html += f"""
        <div style="margin-bottom:10px;">
          <img src="file://{tmp_path}" style="width:100%;">
        </div>
        """

    data["photos"] = photo_html

    html = Template(template_html).render(**data)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        HTML(string=html).write_pdf(tmp.name)
        pdf_bytes = open(tmp.name, "rb").read()

    os.unlink(tmp.name)

    for f in temp_files:
        if os.path.exists(f):
            os.unlink(f)

    return pdf_bytes
