import os
import requests
import json
from metadata_parser import add_metadata, check_ffmpeg_installed, convert_webp_to_jpeg
from pocketfm import get_show_image_url, get_show_name, get_author_name

def download_episodes(json_filename, pattern, download_folder, show_id):
    os.makedirs(download_folder, exist_ok=True)
    
    ffmpeg_path = os.path.join(os.getcwd(), 'ffmpeg')
    if check_ffmpeg_installed(ffmpeg_path):
        meta=True
        image_name = f"{show_id}.webp"
        image_url = get_show_image_url(show_id)
        if not image_url:
            print(f"Could not fetch image for show_id: {show_id}")
            return
        
        try:
            image_data = requests.get(image_url).content
            image_path = os.path.join(download_folder, image_name)
            with open(image_path, 'wb') as img_file:
                img_file.write(image_data)
            jpeg_path = image_path.replace(".webp", ".jpeg")
            convert_webp_to_jpeg(image_path, jpeg_path)
            os.remove(image_path)
        except requests.RequestException as e:
            print(f"Failed to download image: {e}")
            return
    else:
        meta=False
        print("FFmpeg not found. Metadata embedding is not possible.")

    author = get_author_name(show_id)
    album_name = get_show_name(show_id)

    with open(json_filename, 'r', encoding='utf-8') as f:
        stories = json.load(f)

    download_range = determine_download_range(pattern, len(stories))

    for i in download_range:
        if i < len(stories):
            story = stories[i]
            story_title = story.get("story_title", f"episode_{i}")
            media_url = story.get("media_url")
            if media_url:
                try:
                    try:
                        response = requests.get(media_url.replace("low", "high"))
                    except requests.RequestException:
                        response = requests.get(media_url)
                    response.raise_for_status()
                    filename = f"{story_title.strip()}.mp3".replace("’", "'").replace("/", "_").replace("–", "-").replace("?", "")
                    filepath = os.path.join(download_folder, filename)
                    with open(filepath, 'wb') as f:
                        f.write(response.content)
                    print(f"Downloaded '{story_title}' successfully.")
                    if meta:
                        add_metadata(filepath, story_title, author, album_name, jpeg_path)
                except requests.RequestException as e:
                    print(f"Failed to download '{story_title}': {e}")
            else:
                print(f"Looks like you haven't unlocked '{story_title}'. Skipping...")
        else:
            print(f"Story index {i} out of range. Skipping...")
    
    if os.path.isfile(jpeg_path):
        os.remove(jpeg_path)
    
    print("Download complete.")

def determine_download_range(pattern, total_stories):
    if pattern == '*':
        return range(total_stories)
    elif pattern.startswith('*'):
        num = int(pattern[1:])
        return range(num)
    elif pattern.endswith('*'):
        num = int(pattern[:-1])
        return range(num, total_stories)
    elif '*' in pattern:
        start, end = map(int, pattern.split('*'))
        return range(start - 1, end)
    elif pattern.isdigit():
        start = int(pattern) - 1
        return range(start, start + 1)
    else:
        print(f"Invalid pattern: {pattern}")
        return range(0)
