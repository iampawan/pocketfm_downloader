from subprocess import run, PIPE, CalledProcessError 
from os import path
from PIL import Image
from platform import system
from shutil import move

GREEN = '\033[32m'
RED = '\033[31m'
RESET = '\033[0m'

def convert_webp_to_jpeg(webp_image_path, jpeg_image_path):
    try:
        with Image.open(webp_image_path).convert("RGB") as image:
            image.save(jpeg_image_path, "jpeg")
        print(f"{GREEN}Converted album art to jpeg{RESET}")
    except Exception as e:
        print(f"{RED}Failed to convert album art to jpeg: {e}{RESET}")

def check_ffmpeg_installed(ffmpeg_path):
    ffmpeg_cmd = 'ffmpeg.exe' if system() == 'Windows' else 'ffmpeg'
    try:
        run([ffmpeg_cmd, '-version'], stdout=PIPE, stderr=PIPE, check=True)
        return True
    except FileNotFoundError:
        pass

    ffmpeg_executable = path.join(ffmpeg_path, 'ffmpeg')
    if system() == 'Windows':
        ffmpeg_executable += '.exe'
    if path.isfile(ffmpeg_executable):
        try:
            run([ffmpeg_executable, '-version'], stdout=PIPE, stderr=PIPE, check=True)
            return True
        except FileNotFoundError:
            return False
    return False

def add_metadata(filepath, story_title, author_name, album_name, image_name):
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
        '-metadata', 'album_artist=kAdLe eSports',
        '-metadata', 'encoded_by=https://github.com/advaithsshetty/pocketfm_downloader',
        '-metadata', 'publisher=kAdLe eSports',
        '-id3v2_version', '3',
        '-write_id3v1', '1',
        '-disposition:v', 'attached_pic',
        '-loglevel', 'quiet',
        output_filepath
    ]
    try:
        run(cmd, check=True)
        print(f"{GREEN}Metadata and album art added for '{story_title}'{RESET}")
        move(output_filepath, filepath)
    except CalledProcessError as e:
        print(f"{RED}Failed to add metadata for '{story_title}': {e}{RESET}")
    except Exception as e:
        print(f"{RED}Unexpected error occurred: {e}{RESET}")