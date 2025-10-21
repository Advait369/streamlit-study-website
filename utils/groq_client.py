from groq import Groq
import json
import time
import logging
from typing import List, Dict, Any
import re

logger = logging.getLogger(__name__)

class GroqClient:
    def __init__(self, api_key: str):
        self.client = Groq(api_key=api_key)
        # Updated model: using llama-3.3-70b-versatile as recommended replacement
        self.model = "llama-3.3-70b-versatile"
        self.max_retries = 3
        self.retry_delay = 2
    
    def make_request(self, prompt: str, system_message: str = None, temperature: float = 0.3) -> str:
        """Make API request with retry logic"""
        messages = []
        
        if system_message:
            messages.append({"role": "system", "content": system_message})
        
        messages.append({"role": "user", "content": prompt})
        
        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=4000
                )
                return response.choices[0].message.content
                
            except Exception as e:
                logger.warning(f"API request attempt {attempt + 1} failed: {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                else:
                    raise
    
    def generate_toc(self, pdf_text: str, user_prompt: str = "") -> List[Dict]:
        """Generate table of contents from PDF text"""
        system_msg = """You are an expert educational content analyzer. Create a clear, logical table of contents from document text. Return ONLY valid JSON, no other text."""
        
        prompt = f"""
        USER REQUEST: {user_prompt if user_prompt else "Create a comprehensive study guide"}
        
        DOCUMENT TEXT (first 10k chars):
        {pdf_text[:10000]}
        
        Analyze this document and create a hierarchical table of contents.
        Focus on creating a learning-friendly structure.
        
        Return ONLY valid JSON array with this structure:
        [
          {{
            "title": "Main Section Title",
            "pages": "1-5",
            "subtopics": ["Subtopic 1", "Subtopic 2"],
            "estimated_slides": 3,
            "key_concepts": ["concept1", "concept2"]
          }}
        ]
        
        Guidelines:
        - Create 5-15 main sections
        - Each section should have 2-5 subtopics
        - Estimate slides based on content density
        - Focus on learning progression
        - Return ONLY JSON, no other text
        """
        
        response = self.make_request(prompt, system_msg, temperature=0.4)
        
        # Clean and parse JSON response
        try:
            # Extract JSON from response if there's extra text
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                toc_data = json.loads(json_match.group())
            else:
                toc_data = json.loads(response)
            
            # Validate and add start_slide positions
            if isinstance(toc_data, list):
                current_slide = 0
                for section in toc_data:
                    if isinstance(section, dict):
                        section['start_slide'] = current_slide
                        current_slide += section.get('estimated_slides', 3)
            
            logger.info(f"Generated TOC with {len(toc_data)} sections")
            return toc_data
            
        except (json.JSONDecodeError, AttributeError) as e:
            logger.error(f"Failed to parse TOC JSON: {response}")
            # Return a fallback TOC structure
            return [
                {
                    "title": "Introduction",
                    "pages": "1-3",
                    "subtopics": ["Overview", "Key Concepts"],
                    "estimated_slides": 3,
                    "key_concepts": ["basic concepts"],
                    "start_slide": 0
                }
            ]
    
    def generate_section_content(self, section: Dict, section_text: str, user_prompt: str) -> Dict:
        """Generate educational content for a section"""
        system_msg = """You are an expert educational content creator. Create engaging, informative slides with assessments. Return ONLY valid JSON, no other text."""
        
        prompt = f"""
        USER STUDY PREFERENCES: {user_prompt}
        
        CREATE CONTENT FOR SECTION: {section['title']}
        Key Concepts: {', '.join(section.get('key_concepts', []))}
        
        SECTION CONTENT:
        {section_text[:6000]}
        
        Create comprehensive educational slides for this section.
        
        Return ONLY valid JSON with this exact structure:
        {{
          "slides": [
            {{
              "title": "Slide Title",
              "content": "Educational content in markdown...",
              "image_prompt": "Description for relevant image",
              "key_points": ["point1", "point2"]
            }}
          ],
          "quizzes": [
            {{
              "question": "Clear question text",
              "type": "multiple_choice|multi_select|short_answer",
              "options": ["A", "B", "C"],
              "correct_answer": "A or ['A','B'] or ideal text",
              "ideal_answer": "Detailed explanation of correct answer",
              "difficulty": "easy|medium|hard"
            }}
          ],
          "youtube_queries": ["search query 1", "query 2"]
        }}
        
        Guidelines:
        - Create {section.get('estimated_slides', 3)} slides
        - Make content engaging and easy to understand
        - Include 1-2 quizzes per section
        - Use markdown for better formatting
        - Focus on key concepts from the section
        - Return ONLY JSON, no other text
        """
        
        response = self.make_request(prompt, system_msg, temperature=0.7)
        
        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                content_data = json.loads(json_match.group())
            else:
                content_data = json.loads(response)
            
            # Validate the structure
            if not isinstance(content_data, dict):
                raise ValueError("Response is not a dictionary")
                
            return content_data
            
        except (json.JSONDecodeError, ValueError, AttributeError) as e:
            logger.error(f"Failed to parse section content JSON: {response}")
            # Return fallback structure
            return {
                "slides": [
                    {
                        "title": f"{section['title']} - Overview",
                        "content": f"Content for {section['title']}. This section covers key concepts from the document.",
                        "image_prompt": f"educational diagram for {section['title']}",
                        "key_points": ["Key concept 1", "Key concept 2"]
                    }
                ],
                "quizzes": [
                    {
                        "question": f"What is the main topic of {section['title']}?",
                        "type": "multiple_choice",
                        "options": ["Option A", "Option B", "Option C", "Option D"],
                        "correct_answer": "Option A",
                        "ideal_answer": f"The main topic is {section['title']} as covered in this section.",
                        "difficulty": "easy"
                    }
                ],
                "youtube_queries": [f"{section['title']} educational video"]
            }
