import json
import os
import shutil
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class StorageManager:
    def __init__(self, base_path="courses"):
        self.base_path = base_path
        self.ensure_directories()
    
    def ensure_directories(self):
        """Create necessary directories"""
        os.makedirs(self.base_path, exist_ok=True)
        os.makedirs(f"{self.base_path}/images", exist_ok=True)
        os.makedirs(f"{self.base_path}/progress", exist_ok=True)
    
    def save_course(self, course_id: str, course_data: Dict):
        """Save course data to JSON file"""
        try:
            file_path = f"{self.base_path}/{course_id}.json"
            
            # Add metadata if not present
            if 'storage_info' not in course_data:
                course_data['storage_info'] = {
                    'file_size': len(json.dumps(course_data)),
                    'slide_count': len(course_data.get('slides', [])),
                    'quiz_count': sum(1 for slide in course_data.get('slides', []) if slide.get('quiz'))
                }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(course_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Course saved: {file_path} ({course_data['storage_info']['slide_count']} slides)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save course {course_id}: {str(e)}")
            return False
    
    def load_course(self, course_id: str) -> Optional[Dict]:
        """Load course data from JSON file"""
        try:
            file_path = f"{self.base_path}/{course_id}.json"
            with open(file_path, 'r', encoding='utf-8') as f:
                course_data = json.load(f)
            
            logger.info(f"Course loaded: {file_path}")
            return course_data
            
        except FileNotFoundError:
            logger.warning(f"Course file not found: {course_id}")
            return None
        except Exception as e:
            logger.error(f"Failed to load course {course_id}: {str(e)}")
            return None
    
    def save_user_progress(self, course_id: str, user_id: str, progress: Dict):
        """Save user progress for a course"""
        try:
            progress_path = f"{self.base_path}/progress/{course_id}_{user_id}.json"
            
            # Add timestamp
            progress['last_updated'] = self._current_timestamp()
            
            with open(progress_path, 'w') as f:
                json.dump(progress, f, indent=2)
            
            logger.info(f"Progress saved for user {user_id} on course {course_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save progress: {str(e)}")
            return False
    
    def load_user_progress(self, course_id: str, user_id: str) -> Dict:
        """Load user progress for a course"""
        try:
            progress_path = f"{self.base_path}/progress/{course_id}_{user_id}.json"
            with open(progress_path, 'r') as f:
                progress = json.load(f)
            
            logger.info(f"Progress loaded for user {user_id} on course {course_id}")
            return progress
            
        except FileNotFoundError:
            # Return default progress structure
            return {
                "current_slide": 0,
                "quiz_answers": {},
                "bookmarks": [],
                "quiz_scores": {},
                "time_spent": 0,
                "last_accessed": self._current_timestamp()
            }
        except Exception as e:
            logger.error(f"Failed to load progress: {str(e)}")
            return {
                "current_slide": 0,
                "quiz_answers": {},
                "bookmarks": [],
                "quiz_scores": {},
                "time_spent": 0
            }
    
    def list_user_courses(self, user_id: str) -> List[Dict]:
        """List all courses with user progress"""
        courses = []
        
        try:
            for filename in os.listdir(self.base_path):
                if filename.endswith('.json') and not filename.startswith('.'):
                    course_id = filename[:-5]  # Remove .json extension
                    
                    # Skip progress files
                    if 'progress' in course_id:
                        continue
                    
                    course_data = self.load_course(course_id)
                    if course_data:
                        progress = self.load_user_progress(course_id, user_id)
                        
                        courses.append({
                            'course_id': course_id,
                            'course_data': course_data,
                            'progress': progress,
                            'last_accessed': progress.get('last_accessed', 0)
                        })
            
            # Sort by last accessed
            courses.sort(key=lambda x: x['last_accessed'], reverse=True)
            return courses
            
        except Exception as e:
            logger.error(f"Failed to list user courses: {str(e)}")
            return []
    
    def export_course(self, course_id: str, export_path: str) -> bool:
        """Export course to a specified path"""
        try:
            course_data = self.load_course(course_id)
            if not course_data:
                return False
            
            with open(export_path, 'w') as f:
                json.dump(course_data, f, indent=2)
            
            logger.info(f"Course exported to: {export_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export course: {str(e)}")
            return False
    
    def cleanup_orphaned_images(self, valid_course_ids: set):
        """Remove images for deleted courses"""
        try:
            image_dir = f"{self.base_path}/images"
            for filename in os.listdir(image_dir):
                if filename.endswith('.jpg'):
                    file_course_id = filename.split('_')[0]
                    if file_course_id not in valid_course_ids:
                        os.remove(f"{image_dir}/{filename}")
                        logger.info(f"Removed orphaned image: {filename}")
        except Exception as e:
            logger.error(f"Failed to cleanup images: {str(e)}")
    
    def _current_timestamp(self) -> str:
        """Get current timestamp string"""
        from datetime import datetime
        return datetime.now().isoformat()
