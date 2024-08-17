import os
import argparse

from download import download_episodes
from pocketfm import fetch_pocketfm_data, save_data_to_json, get_show_name

def main():
    parser = argparse.ArgumentParser(description="SLD PocketFM Downloader")
    parser.add_argument('url', type=str, nargs='?', help="The URL of the PocketFM show")
    parser.add_argument('-p', '--pattern', type=str, help="The pattern to download episodes\n1. To download all episodes, enter '*'\n2. To download episodes before 'n', enter '*n'\n3. To download episodes after 'n', enter 'n*'\n4. To download episodes between 'n' and 'm', enter 'n*m'\n5. To download a specific episode, enter the episode number.")
    
    args = parser.parse_args()

    if args.url:
        show_url = args.url
    else:
        show_url = input("Enter the show URL: ")

    show_id = show_url.split("/")[-1]
    stories_data = fetch_pocketfm_data(show_id)

    if stories_data:
        json_filename = f"{show_id}.json"
        save_data_to_json(stories_data, json_filename)
    else:
        print("Failed to fetch data.")
        return

    download_pattern = args.pattern
    if not download_pattern:
        print('''
              Enter the pattern to download episodes: 
        1. To download all episodes, enter '*'
        2. To download episodes before 'n', enter '*n'
        3. To download episodes after 'n', enter 'n*'
        4. To download episodes between 'n' and 'm', enter 'n*m'
        5. To download a specific episode, enter the episode number.
              ''')
        download_pattern = input("Pattern: ")

    download_folder = show_id
    download_episodes(json_filename, download_pattern, download_folder, show_id)
    os.remove(json_filename)

if __name__ == "__main__":
    main()
