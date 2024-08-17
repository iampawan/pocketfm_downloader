import json
import requests
import configparser
import logging

def load_access_token():
    config = configparser.ConfigParser()
    try:
        config.read('config.ini')
        return config.get('pocketfm', 'access_token')
    except (configparser.NoSectionError, configparser.NoOptionError) as e:
        logging.error(f"Configuration error: {e}:: Defaulting to guest access.")
        return None
    except FileNotFoundError:
        logging.error("Configuration file 'config.ini' not found. Defaulting to guest access.")
        return None

def base_url():
    return "https://web.pocketfm.com/v2/content_api/show.get_details"

def headers(extra_args=None):
    header = {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Accept-Language': 'en-US,en;q=0.5',
        'app-client': 'consumer-web',
        'app-version': '180',
        'Connection': 'keep-alive',
        'device-id': 'web-auth',
        'Host': 'web.pocketfm.com',
        'locale': 'IN',
        'Origin': 'https://pocketfm.com',
        'Referer': 'https://pocketfm.com/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-site'
    }
    if extra_args:
        header['access-token'] = extra_args
    return header

def fetch_pocketfm_data(show_id, headers=headers(load_access_token()), base_url=base_url()):
    session = requests.Session()
    curr_ptr = ''
    all_stories = []
    while True:
        params = {
            'show_id': show_id,
            'curr_ptr': curr_ptr,
            'info_level': 'max'
        }
        print(f"Fetching data for show: {get_show_name(show_id)}, curr_ptr: {curr_ptr}...")
        try:
            response = session.get(base_url, headers=headers, params=params)
            if response.status_code == 200:
                data = response.json()
                result = data.get('result')
                if result:
                    first_result = result[0][0] if isinstance(result[0], list) else result[0]
                    stories = first_result.get('stories', [])
                    filtered_stories = [
                        {
                            "story_title": story.get("story_title"),
                            "story_id": story.get("story_id"),
                            "media_url": story.get("media_url")
                        }
                        for story in stories
                    ]
                    all_stories.extend(filtered_stories)
                    curr_ptr = first_result.get('next_ptr')
                    if not curr_ptr or curr_ptr == -1:
                        break
                else:
                    print("The 'result' field is not present in the response.")
                    break
            else:
                print(f"Failed to fetch data. Status code: {response.status_code}")
                break
        except Exception as e:
            print(f"An error occurred: {e}")
            break
    session.close()
    return all_stories

def response_json(show_id, headers=headers(), base_url=base_url()):
    params = {'show_id': show_id}
    try:
        response = requests.get(base_url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching data for show_id {show_id}: {e}")
        return {}

def save_data_to_json(data, filename):
    print(f"Saving data to {filename}...")
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"Data successfully saved to {filename}")

def get_show_image_url(show_id):
    data = response_json(show_id)
    result = data.get('result', [])
    if result:
        first_result = result[0] if isinstance(result[0], dict) else {}
        img_url = first_result.get('image_url')
        if img_url:
            return img_url
    return None

def get_show_name(show_id):
    data = response_json(show_id)
    result = data.get('result', [])
    if result:
        return result[0].get('show_title', 'Unknown Show Title')
    return 'Unknown Show Title'

def get_author_name(show_id):
    data = response_json(show_id)
    result = data.get('result', [])
    if result:
        if result:
            first_result = result[0][0] if isinstance(result[0], list) else result[0]   
            user_info = first_result.get('user_info', [])
            if user_info:
                author= user_info.get('fullname', 'Unknown Author Name')
                return author
    return 'Unknown Author Name'
