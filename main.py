from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse, Response
import pdfplumber
from weasyprint import HTML
import tempfile
import os

app = FastAPI()

HTML_TEMPLATE = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{
      font-family: Arial, sans-serif;
      font-size: 12px;
    }}
    h1 {{
      color: #1f4fd8;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin-top: 10px;
    }}
    td, th {{
      border-bottom: 1px solid #ddd;
      padding: 6px;
    }}
  </style>
</head>
<body>
  <h1>Class A Fix Compliance Report</h1>

  <p><strong>Report type:</strong> {report_type}</p>

  <h3>Extracted content</h3>
  <table>
    <tr><th>Sample Text</th></tr>
    <tr><td>{text}</td></tr>
  </table>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <h2>Class A Fix PDF Generator</h2>

    <form action="/generate" method="post" enctype="multipart/form-data">
      <label>Report type</label><br>
      <select name="report_type">
        <option value="Smoke Alarm">Smoke Alarm</option>
        <option value="Electrical">Electrical</option>
        <option value="Gas">Gas</option>
        <option value="RMS">Rental Minimum Standards</option>
      </select>
      <br><br>

      <label>Upload PDF</label><br>
      <input type="file" name="pdf" required>
      <br><br>

      <button type="submit">Generate PDF</button>
    </form>
    """

@app.post("/generate")
async def generate_pdf(
    report_type: str = Form(...),
    pdf: UploadFile = File(...)
):
    extracted_text = ""

    with pdfplumber.open(pdf.file) as doc:
        for page in doc.pages:
            t = page.extract_text()
            if t:
                extracted_text += t + "\n"

    extracted_text = extracted_text[:1500]

    html = HTML_TEMPLATE.format(
        report_type=report_type,
        text=extracted_text.replace("\n", "<br>")
    )

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        HTML(string=html).write_pdf(tmp.name)
        pdf_bytes = open(tmp.name, "rb").read()
        os.unlink(tmp.name)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": "attachment; filename=classafix_report.pdf"
        }
    )
