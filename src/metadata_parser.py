import subprocess
import os
from PIL import Image
import platform
import shutil

def convert_webp_to_jpeg(webp_image_path, jpeg_image_path):
    try:
        with Image.open(webp_image_path).convert("RGB") as image:
            image.save(jpeg_image_path, "jpeg")
        print(f"Converted '{webp_image_path}' to '{jpeg_image_path}'")
    except Exception as e:
        print(f"Failed to convert image '{webp_image_path}': {e}")

def check_ffmpeg_installed(ffmpeg_path):
    if platform.system() == 'Windows':
        ffmpeg_cmd = 'ffmpeg.exe'
    else:
        ffmpeg_cmd = 'ffmpeg'
    
    try:
        subprocess.run([ffmpeg_cmd, '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return True
    except FileNotFoundError:
        pass

    ffmpeg_executable = os.path.join(ffmpeg_path, 'ffmpeg')
    if platform.system() == 'Windows':
        ffmpeg_executable += '.exe'
    if os.path.isfile(ffmpeg_executable):
        try:
            subprocess.run([ffmpeg_executable, '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            return True
        except FileNotFoundError:
            return False
    return False

def add_metadata(filepath, story_title, author_name, album_name, image_name):
    try:
        output_filepath = f"{filepath}_with_art.mp3"
        cmd = [
            'ffmpeg',
            '-y',
            '-i', filepath,
            '-i', image_name,
            '-map', '0:a',
            '-map', '1:v',
            '-c', 'copy',
            '-metadata', f'title={story_title}',
            '-metadata', f'artist={author_name}',
            '-metadata', f'album={album_name}',
            '-metadata', 'album_artist=SLD!',
            '-metadata', 'encoded_by=https://github.com/advaithsshetty/pocketfm_downloader',
            '-metadata', 'publisher=Lotan',
            '-id3v2_version', '3',
            '-write_id3v1', '1',
            '-disposition:v', 'attached_pic',
            '-loglevel', 'quiet',
            output_filepath
        ]
        
        subprocess.run(cmd, check=True)
        print(f"Metadata and album art added for '{story_title}'")
        shutil.move(output_filepath, filepath)

    except subprocess.CalledProcessError as e:
        print(f"Failed to add metadata for '{story_title}': {e}")
    except Exception as e:
        print(f"Unexpected error occurred: {e}")
