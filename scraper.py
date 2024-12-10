import requests
from PIL import Image
from io import BytesIO
import os
import shutil
import random
import time
from datetime import datetime, timedelta
import flickrapi
import urllib3
from requests.exceptions import RequestException

# Configuration
TARGET_WIDTH = 1024
TARGET_HEIGHT = 768
API_RATE_LIMIT = 2500  # Maximum safe API calls per hour
API_CALL_INTERVAL = 1800 / API_RATE_LIMIT  # Time in seconds between each API call

key = os.getenv('flickr_key')
secret = os.getenv('flickr_secret')

save_dir = 'images'
flickr = flickrapi.FlickrAPI(key, secret, format='parsed-json')

if os.path.exists(save_dir):
    shutil.rmtree(save_dir)
os.makedirs(save_dir, exist_ok=True)

def get_random_date():
    """Generate a random date within Flickr's history range."""
    start_date = datetime(2004, 2, 1)  # Flickr launch date
    end_date = datetime.now()
    random_days = random.randint(0, (end_date - start_date).days)
    return (start_date + timedelta(days=random_days)).strftime('%Y-%m-%d')

def get_random_image():
    """Fetch one random image URL based on a random date and a random page."""
    while True:
        random_date = get_random_date()
        try:
            # Step 1: Initial search to get total pages
            response = flickr.photos.search(
                min_taken_date=random_date,
                max_taken_date=random_date,
                per_page=1,
                page=1
            )
            
            total_pages = response['photos']['pages']
            
            if total_pages == 0:
                continue

            # Step 2: Randomly select a page within the available range
            random_page = random.randint(1, total_pages)
            
            # Fetch one photo from the randomly selected page
            response = flickr.photos.search(
                min_taken_date=random_date,
                max_taken_date=random_date,
                per_page=1,
                page=random_page
            )
            photos = response['photos']['photo']

            if photos:
                photo = photos[0]
                image_url = f"https://live.staticflickr.com/{photo['server']}/{photo['id']}_{photo['secret']}_b.jpg"
                return image_url

        except flickrapi.exceptions.FlickrError as e:
            print(f"Error fetching photos: {e}")
            continue

def download_image(image_url, retries=3):
    """Download the image with retry mechanism."""
    for attempt in range(retries):
        try:
            response = requests.get(image_url, timeout=10)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            if isinstance(e, urllib3.exceptions.NameResolutionError):
                print(f"Name resolution failed for {image_url}: {e}")
                break  # Skip if domain resolution fails
            print(f"Attempt {attempt + 1} failed: {e}")
            time.sleep(2)  # Wait a bit before retrying
    return None

def download_and_save_images(num_images=100):
    """Download and save a specified number of images with the desired resolution."""
    saved_image_count = 0
    total_api_calls = 0

    while saved_image_count < num_images:
        image_url = get_random_image()
        total_api_calls += 2  # Each get_random_image call makes 2 API calls
        
        time.sleep(API_CALL_INTERVAL)

        if not image_url:
            continue
        
        response = download_image(image_url)
        if not response:
            continue  # Skip if download failed
        
        try:
            # Step 1: Open the image and check its resolution
            img = Image.open(BytesIO(response.content))
            width, height = img.size

            # Step 2: Save the image only if it matches the target resolution
            if width == TARGET_WIDTH and height == TARGET_HEIGHT:
                img_format = img.format.lower()
                saved_image_count += 1
                img.save(f"{save_dir}/image_{saved_image_count}.{img_format}")
                print(f"Downloaded and saved image {saved_image_count} with resolution {width}x{height}")
            # else:
            #     print(f"Image does not match the target resolution {TARGET_WIDTH}x{TARGET_HEIGHT}, resolution is {width}x{height}, skipping.")
        
        except IOError as e:
            print(f"Failed to process image from {image_url}: {e}")

        # Stop if we've hit the API rate limit for the hour
        if total_api_calls >= API_RATE_LIMIT:
            print("API rate limit reached. Pausing for an hour...")
            time.sleep(1200)
            total_api_calls = 0

# Run with nohup python3 -u scraper.py > output.log 2>&1 & (unix) or Start-Process -NoNewWindow -FilePath "python" -ArgumentList "-u", "scraper.py", ">", "output.log", "2>&1" -RedirectStandardOutput "output.log" -RedirectStandardError "error.log" (windows)
# Check ongoing processes with ps aux | grep scraper.py
download_and_save_images(10000)