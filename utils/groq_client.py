from groq import Groq
import json
from typing import List, Dict

class GroqClient:
    def __init__(self, api_key: str):
        self.client = Groq(api_key=api_key)
    
    def generate_toc(self, pdf_text: str) -> List[Dict]:
        """Generate table of contents from PDF text"""
        prompt = f"""
        Analyze this document and create a hierarchical table of contents.
        Return ONLY valid JSON array with structure: [{{"title": "Section Title", "pages": "1-5", "subtopics": []}}]
        
        Document:
        {pdf_text[:8000]}  # Limit context size
        """
        
        response = self.client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        return json.loads(response.choices[0].message.content)
    
    def generate_slide_content(self, section_title: str, section_text: str) -> Dict:
        """Generate slides, quizzes, and media for a section"""
        prompt = f"""
        Create educational content for: {section_title}
        
        Section Content:
        {section_text}
        
        Return JSON with:
        - slides: array of {{title, content, image_prompt}}
        - quizzes: array of {{question, type, options, correct_answer, ideal_answer}}
        - youtube_queries: array of search queries for videos
        
        Types: multiple_choice, multi_select, short_answer
        """
        # Implementation similar to TOC generation
