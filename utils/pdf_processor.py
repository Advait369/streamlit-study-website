import pdfplumber
import hashlib
from typing import Dict, List

class PDFProcessor:
    def extract_text(self, pdf_file) -> str:
        """Extract all text from PDF"""
        with pdfplumber.open(pdf_file) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() + "\n"
        return text
    
    def generate_file_hash(self, pdf_file) -> str:
        """Generate unique hash for PDF file"""
        return hashlib.sha256(pdf_file.getvalue()).hexdigest()
