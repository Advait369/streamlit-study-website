import json
import os
from typing import Dict, Any

class StorageManager:
    def __init__(self, base_path="courses"):
        self.base_path = base_path
        os.makedirs(base_path, exist_ok=True)
        os.makedirs(f"{base_path}/images", exist_ok=True)
    
    def save_course(self, course_id: str, course_data: Dict):
        """Save course data to JSON file"""
        file_path = f"{self.base_path}/{course_id}.json"
        with open(file_path, 'w') as f:
            json.dump(course_data, f, indent=2)
    
    def load_course(self, course_id: str) -> Dict:
        """Load course data from JSON file"""
        file_path = f"{self.base_path}/{course_id}.json"
        with open(file_path, 'r') as f:
            return json.load(f)
    
    def get_user_progress(self, course_id: str, user_id: str) -> Dict:
        """Load user progress for a course"""
        progress_path = f"{self.base_path}/{course_id}_{user_id}_progress.json"
        if os.path.exists(progress_path):
            with open(progress_path, 'r') as f:
                return json.load(f)
        return {"current_slide": 0, "quiz_answers": {}, "bookmarks": []}
    
    def save_user_progress(self, course_id: str, user_id: str, progress: Dict):
        """Save user progress"""
        progress_path = f"{self.base_path}/{course_id}_{user_id}_progress.json"
        with open(progress_path, 'w') as f:
            json.dump(progress, f, indent=2)
