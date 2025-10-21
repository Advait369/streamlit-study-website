import pdfplumber
import hashlib
import re
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)

class PDFProcessor:
    def __init__(self):
        self.section_patterns = [
            r'^\d+\.\s+.+',  # 1. Section Title
            r'^\d+\.\d+\.\s+.+',  # 1.1. Subsection Title
            r'^[A-Z][A-Za-z\s]{10,}',  # CAPITALIZED SECTION
            r'^Chapter\s+\d+',  # Chapter 1
        ]
    
    def extract_text(self, pdf_file) -> Tuple[str, Dict]:
        """Extract text and metadata from PDF"""
        try:
            with pdfplumber.open(pdf_file) as pdf:
                text = ""
                metadata = {
                    'total_pages': len(pdf.pages),
                    'page_details': []
                }
                
                for page_num, page in enumerate(pdf.pages, 1):
                    page_text = page.extract_text() or ""
                    text += f"--- Page {page_num} ---\n{page_text}\n\n"
                    
                    # Extract page metadata
                    metadata['page_details'].append({
                        'page_number': page_num,
                        'char_count': len(page_text),
                        'word_count': len(page_text.split()),
                        'has_images': len(page.images) > 0
                    })
                
                logger.info(f"Extracted {len(text)} characters from {len(pdf.pages)} pages")
                return text, metadata
                
        except Exception as e:
            logger.error(f"Error extracting PDF text: {str(e)}")
            raise
    
    def generate_file_hash(self, pdf_file) -> str:
        """Generate unique hash for PDF file"""
        return hashlib.sha256(pdf_file.getvalue()).hexdigest()[:16]
    
    def detect_sections(self, text: str) -> List[Dict]:
        """Pre-process PDF to detect potential sections"""
        lines = text.split('\n')
        sections = []
        
        for i, line in enumerate(lines):
            line = line.strip()
            if len(line) > 20 and any(re.match(pattern, line) for pattern in self.section_patterns):
                sections.append({
                    'title': line,
                    'line_number': i,
                    'confidence': 'high'
                })
        
        return sections
