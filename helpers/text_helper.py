import re

def clean_text(raw_text: str) -> str:
    """
    Perform basic text cleaning such as collapsing whitespace.
    """
    # Replace multiple whitespace characters with a single space
    text = re.sub(r"\s+", " ", raw_text)
    return text.strip()
