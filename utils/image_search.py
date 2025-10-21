
import requests
import os
from PIL import Image
import io

class ImageSearch:
    def __init__(self, google_api_key: str, cse_id: str):
        self.api_key = google_api_key
        self.cse_id = cse_id
    
    def search_and_download(self, query: str, course_id: str, image_name: str) -> str:
        """Search image and download to local storage"""
        search_url = "https://www.googleapis.com/customsearch/v1"
        params = {
            'q': query,
            'key': self.api_key,
            'cx': self.cse_id,
            'searchType': 'image',
            'num': 1
        }
        
        response = requests.get(search_url, params=params)
        results = response.json()
        
        if 'items' in results:
            image_url = results['items'][0]['link']
            # Download and save image
            img_data = requests.get(image_url).content
            image_path = f"courses/images/{course_id}_{image_name}.jpg"
            with open(image_path, 'wb') as handler:
                handler.write(img_data)
            return image_path
        return None
