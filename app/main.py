from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse, Response
import pdfplumber

from app.extractors.smoke import extract_smoke
from app.extractors.electrical import extract_electrical
from app.extractors.gas import extract_gas
from app.extractors.rms import extract_rms

from app.renderer.pdf import render_pdf

app = FastAPI()


@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <h2>Class A Fix PDF Generator</h2>

    <form action="/generate" method="post" enctype="multipart/form-data">
      <label>Report type</label><br>
      <select name="report_type">
        <option value="smoke">Smoke Alarm</option>
        <option value="electrical">Electrical</option>
        <option value="gas">Gas</option>
        <option value="rms">Rental Minimum Standards</option>
      </select><br><br>

      <label>Upload PDF</label><br>
      <input type="file" name="pdf" required><br><br>

      <label>Upload photos</label><br>
      <input type="file" name="photos" multiple><br><br>

      <button type="submit">Generate PDF</button>
    </form>
    """


@app.post("/generate")
async def generate(
    report_type: str = Form(...),
    pdf: UploadFile = File(...),
    photos: list[UploadFile] = File(default=[])
):
    text = ""

    with pdfplumber.open(pdf.file) as doc:
        for page in doc.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

    if report_type == "smoke":
        data = extract_smoke(text)
        template = "smoke.html"

    elif report_type == "electrical":
        data = extract_electrical(text)
        template = "electrical.html"

    elif report_type == "gas":
        data = extract_gas(text)
        template = "gas.html"

    elif report_type == "rms":
        data = extract_rms(text)
        template = "rms.html"

    else:
        return {"error": "Invalid report type"}

    pdf_bytes = render_pdf(template, data, photos)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": "attachment; filename=classafix_report.pdf"
        }
    )
