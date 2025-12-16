def extract_gas(text: str) -> dict:
    return {
        "title": "Gas Safety Check",
        "content": text[:1500]
    }
