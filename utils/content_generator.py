import logging
import time
from typing import List, Dict, Any
from .groq_client import GroqClient
from .image_search import ImageSearch

logger = logging.getLogger(__name__)

class ContentGenerator:
    def __init__(self, groq_client: GroqClient):
        self.groq_client = groq_client
    
    def extract_section_text(self, section: Dict, full_text: str, window_size: int = 1000) -> str:
        """Extract relevant text for a section using title matching"""
        section_title = section['title'].lower()
        lines = full_text.split('\n')
        
        # Find lines that might contain the section content
        relevant_lines = []
        found_section = False
        
        for i, line in enumerate(lines):
            line_lower = line.lower().strip()
            
            # Check if this line matches our section title
            if (section_title in line_lower or 
                any(keyword in line_lower for keyword in section_title.split()[:3])):
                found_section = True
                continue
            
            # Collect content after finding the section
            if found_section and line.strip():
                # Stop if we find a new section
                if (len(line.strip()) > 10 and 
                    any(pattern in line_lower for pattern in ['--- page', 'chapter', 'section'])):
                    if len(relevant_lines) > 5:  # Ensure we have enough content
                        break
                
                relevant_lines.append(line)
                
                # Limit the amount of text extracted
                if len('\n'.join(relevant_lines)) > window_size:
                    break
        
        result = '\n'.join(relevant_lines) if relevant_lines else full_text[:window_size]
        logger.info(f"Extracted {len(result)} chars for section: {section['title']}")
        return result
    
    def generate_course_content(self, toc: List[Dict], full_text: str, user_prompt: str, 
                              course_id: str, image_search: ImageSearch = None) -> List[Dict]:
        """Generate complete course content from TOC"""
        all_slides = []
        slide_counter = 0
        
        for section_idx, section in enumerate(toc):
            logger.info(f"Processing section {section_idx + 1}/{len(toc)}: {section['title']}")
            
            # Extract relevant text for this section
            section_text = self.extract_section_text(section, full_text)
            
            # Generate content using Groq
            section_content = self.groq_client.generate_section_content(
                section, section_text, user_prompt
            )
            
            # Process slides for this section
            for slide_idx, slide_data in enumerate(section_content.get('slides', [])):
                slide_obj = {
                    'id': slide_counter,
                    'section_id': section_idx,
                    'section_title': section['title'],
                    'title': slide_data.get('title', f"Slide {slide_idx + 1}"),
                    'content': slide_data.get('content', ''),
                    'key_points': slide_data.get('key_points', []),
                    'image_prompt': slide_data.get('image_prompt', ''),
                    'image_path': None,
                    'quiz': None
                }
                
                # Add image if available and image search is enabled
                if image_search and slide_data.get('image_prompt'):
                    try:
                        image_path = image_search.search_and_download(
                            slide_data['image_prompt'], 
                            course_id, 
                            f"slide_{slide_counter}"
                        )
                        slide_obj['image_path'] = image_path
                    except Exception as e:
                        logger.warning(f"Failed to download image: {str(e)}")
                
                all_slides.append(slide_obj)
                slide_counter += 1
            
            # Add quizzes to appropriate slides
            quizzes = section_content.get('quizzes', [])
            if quizzes:
                # Distribute quizzes to slides in this section
                quiz_slides = [s for s in all_slides if s['section_id'] == section_idx]
                if quiz_slides:
                    # Put first quiz on last slide of section
                    quiz_slides[-1]['quiz'] = quizzes[0]
                    
                    # Put additional quizzes on middle slides if available
                    if len(quizzes) > 1 and len(quiz_slides) > 2:
                        mid_index = len(quiz_slides) // 2
                        quiz_slides[mid_index]['quiz'] = quizzes[1]
            
            # Small delay to prevent rate limiting
            time.sleep(1)
        
        logger.info(f"Generated {len(all_slides)} total slides")
        return all_slides
    
    def estimate_processing_time(self, toc: List[Dict]) -> str:
        """Estimate processing time based on content complexity"""
        total_slides = sum(section.get('estimated_slides', 3) for section in toc)
        
        if total_slides <= 10:
            return "1-2 minutes"
        elif total_slides <= 25:
            return "3-5 minutes" 
        else:
            return "5-10 minutes"
