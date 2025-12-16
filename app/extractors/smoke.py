def extract_smoke(text: str) -> dict:
    return {
        "title": "Smoke Alarm Safety Check",
        "content": text[:1500]
    }
