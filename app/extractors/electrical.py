def extract_electrical(text: str) -> dict:
    return {
        "title": "Electrical Safety Check",
        "content": text[:1500]
    }
