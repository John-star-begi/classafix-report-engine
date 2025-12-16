from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse
import pdfplumber

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <h2>Class A Fix. Compliance Report Engine</h2>

    <form action="/upload" method="post" enctype="multipart/form-data">
      <label>Report type</label><br>
      <select name="report_type">
        <option value="smoke_alarm">Smoke Alarm</option>
        <option value="electrical">Electrical</option>
        <option value="gas">Gas</option>
        <option value="rms">Rental Minimum Standards</option>
      </select>

      <br><br>

      <label>Upload subcontractor PDF</label><br>
      <input type="file" name="report_file" required>

      <br><br>

      <button type="submit">Upload</button>
    </form>
    """

@app.post("/upload")
async def upload(report_type: str = Form(...), report_file: UploadFile = File(...)):
    text = ""

    with pdfplumber.open(report_file.file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

    data = {
        "report_type": report_type,
        "meta": {
            "status": "Compliant" if "compliant" in text.lower() else "",
        },
        "raw_text_sample": text[:2000]
    }

    return data
