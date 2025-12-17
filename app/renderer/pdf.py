from weasyprint import HTML
import tempfile
import os
from jinja2 import Template
import uuid

def render_pdf(template_name: str, data: dict, photos: list) -> bytes:
    template_path = f"app/templates/{template_name}"
    with open(template_path) as f:
        template_html = f.read()

    photo_html = ""
    temp_files = []

    for photo in photos:
        suffix = os.path.splitext(photo.filename)[1]
        tmp_path = f"/tmp/{uuid.uuid4()}{suffix}"
        with open(tmp_path, "wb") as f:
            f.write(photo.file.read())
        temp_files.append(tmp_path)
        photo_html += f"<img src='file://{tmp_path}' style='width:100%;margin-bottom:10px;'>"

    data["photos"] = photo_html

    html = Template(template_html).render(**data)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        HTML(string=html).write_pdf(tmp.name)
        pdf_bytes = open(tmp.name, "rb").read()

    os.unlink(tmp.name)
    for f in temp_files:
        os.unlink(f)

    return pdf_bytes
