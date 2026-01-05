#!/usr/bin/env python3
from pypdf import PdfReader
import sys

def count_words(pdf_path):
    reader = PdfReader(pdf_path)
    total_words = 0
    for page in reader.pages:
        text = page.extract_text()
        if text:
            total_words += len(text.split())
    return total_words

# Usage
print(f"{count_words(sys.argv[1])}")

