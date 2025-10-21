import requests
import os
from PIL import Image
import io
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class ImageSearch:
    def __init__(self, google_api_key: str, cse_id: str):
        self.api_key = google_api_key
        self.cse_id = cse_id
        self.search_url = "https://www.googleapis.com/customsearch/v1"
        
    def search_and_download(self, query: str, course_id: str, image_name: str) -> Optional[str]:
        """Search image and download to local storage"""
        try:
            # Clean query for educational content
            educational_query = f"educational diagram {query} learning study"
            
            params = {
                'q': educational_query,
                'key': self.api_key,
                'cx': self.cse_id,
                'searchType': 'image',
                'num': 3,  # Get multiple results for better selection
                'imgSize': 'medium',
                'rights': 'cc_publicdomain'  # Prefer public domain images
            }
            
            response = requests.get(self.search_url, params=params, timeout=10)
            response.raise_for_status()
            results = response.json()
            
            if 'items' in results:
                # Try each result until we find one that works
                for item in results['items']:
                    image_url = item['link']
                    
                    # Skip GIFs and very small images
                    if (image_url.lower().endswith('.gif') or 
                        item.get('image', {}).get('byteSize', 0) < 10000):
                        continue
                    
                    try:
                        # Download image
                        img_response = requests.get(image_url, timeout=15)
                        img_response.raise_for_status()
                        
                        # Verify it's a valid image
                        image = Image.open(io.BytesIO(img_response.content))
                        image.verify()  # Verify it's a valid image file
                        
                        # Save image
                        image_dir = f"courses/images"
                        os.makedirs(image_dir, exist_ok=True)
                        
                        image_path = f"{image_dir}/{course_id}_{image_name}.jpg"
                        
                        # Convert and save as JPEG
                        image = Image.open(io.BytesIO(img_response.content))
                        image = image.convert('RGB')
                        image.save(image_path, 'JPEG', quality=85)
                        
                        logger.info(f"Downloaded image: {image_path}")
                        return image_path
                        
                    except Exception as e:
                        logger.warning(f"Failed to download image from {image_url}: {str(e)}")
                        continue
            
            logger.warning(f"No suitable images found for query: {query}")
            return None
            
        except Exception as e:
            logger.error(f"Image search failed for '{query}': {str(e)}")
            return None
    
    def validate_credentials(self) -> bool:
        """Validate Google API credentials"""
        try:
            params = {
                'q': 'test',
                'key': self.api_key,
                'cx': self.cse_id,
                'num': 1
            }
            response = requests.get(self.search_url, params=params, timeout=10)
            return response.status_code == 200
        except:
            return False
