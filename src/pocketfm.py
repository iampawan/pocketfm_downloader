from os import _exit as exit
from json import dump
from requests import Session, get, RequestException
from configparser import ConfigParser, NoSectionError, NoOptionError

RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"

def load_access_token():
    config = ConfigParser()
    # Default access token for a throwaway account to bypass 401 error and fetch the first few episodes
    default_token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1aWQiOiI5NDE5ODU2ZDU0NDA1YjBhOTBlNjU0NjBmMTM4NmZiNTdhNjM1MjcxIiwiYWNjZXNzX3Rva2VuIjoiYjQ0ODMxZWNjNzY4Njc4YmEwNzQxYTVkMzZmY2VlMGMwNzYxOGQ0NyIsImRldmljZS1pZCI6Ijc4OTUwM2FmYTRkYTRjNjgiLCJhdXRoX3Rva2VuIjoid2ViLWF1dGgiLCJsYXN0X2FjdGl2ZV9wbGF0Zm9ybSI6ImFuZHJvaWQiLCJsYXN0X2FjdGl2ZV9kZXZpY2VfYXBwX3ZlcnNpb25fY29kZSI6Ijg4MSIsImV4cCI6MTcyNjMwMDcxM30.tBuyKjsZG3IwWbJYAS2NEV-cLFCCVmGTcp5gU3cBl-4'
    try:
        if not config.read('config.ini'):
            raise FileNotFoundError
        config.read('config.ini')
        token = config.get('pocketfm', 'access_token')
        if token == default_token:
            raise LookupError
        else:
            return token
    except LookupError:
        print(f"{YELLOW}This token is of a throwaway account to bypass 401 error and contains only the first few episodes. Use your access token to access all your shows.{RESET}")
        return token
    except FileNotFoundError:
        print(f"{YELLOW}Configuration file 'config.ini' not found. Using throwaway account.{RESET}")
        print(f"{YELLOW}Please login to PocketFM and provide your access token in the 'config.ini' file.{RESET}")
        return default_token

access_token = load_access_token() #Using a global variable to store the access token so that  the function is not called again and again.

def base_url():
    return "https://web.pocketfm.com/v2/content_api/show.get_details"

def headers():
    return {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Accept-Language': 'en-US,en;q=0.5',
        'app-client': 'consumer-web',
        'app-version': '180',
        'Connection': 'keep-alive',
        'device-id': 'web-auth',
        'access-token': access_token,
        'Host': 'web.pocketfm.com',
        'Origin': 'https://pocketfm.com',
        'Referer': 'https://pocketfm.com/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-site'
    }

def fetch_pocketfm_data(show_id, headers=headers(), base_url=base_url()):
    episode_count = get_show_episodecount(show_id)
    session = Session()
    curr_ptr = ''
    curr_ptr_prev = ''
    all_stories = []
    while True:
        params = {
            'show_id': show_id,
            'curr_ptr': curr_ptr,
            'info_level': 'max'
        }
        print(f"{BLUE}Fetching data for show: {get_show_name(show_id)}, Pointing: {curr_ptr}...{RESET}")
        try:
            response = session.get(base_url, headers=headers, params=params)
            if response.status_code == 200:
                data = response.json()
                result = data.get('result')
                if result:
                    first_result = result[0][0] if isinstance(result[0], list) else result[0]
                    stories = first_result.get('stories', [])
                    for story in stories:
                        if story.get("media_url"):
                            filtered_stories = [
                                {
                                    "story_title": story.get("story_title"),
                                    "story_id": story.get("story_id"),
                                    "media_url": story.get("media_url"),
                                }
                            ]
                            all_stories.extend(filtered_stories)
                        else:
                            print(f"{RED}Media URL not found for story: {story.get('story_title')}{RESET}")
                            session.close()
                            return all_stories
                    curr_ptr_prev = curr_ptr
                    curr_ptr = first_result.get('next_ptr')
                    if str(curr_ptr_prev) < str(episode_count) and curr_ptr == -1:
                        print(f"{YELLOW}Server returned -1 for 'next_ptr' even though there is still more data. Retrying...{RESET}")
                        curr_ptr = str(int(curr_ptr_prev) + 10) # Manually incrementing the pointer by 10 to fetch the next set of episodes
                        continue
                    if not curr_ptr or curr_ptr == -1:
                        break # Break the loop if there are no more episodes to fetch
                elif str(curr_ptr) >= str(episode_count):
                    break # Break the loop if the current pointer is greater than or equal to the total episode count
                else:
                    print(f"{RED}The 'result' field is not present in the response. Retrying...{RESET}") # Retry fetching data if the 'result' field is not present. PocketFM API is known to return empty responses sometimes.
                    continue
            else:
                print(f"{RED}Failed to fetch data. Status code: {response.status_code}{RESET}") 
                break
        except Exception as e:
            print(f"{RED}An error occurred: {e}{RESET}")
            break
    session.close()
    return all_stories

def response_json(show_id):
    params = {'show_id': show_id}
    try:
        response = get(base_url(), headers=headers(), params=params)
        response.raise_for_status()
        return response.json()
    except RequestException as e:
        print(f"{RED}Error fetching data for show_id {show_id}: {e}{RESET}")
        return {}

def save_data_to_json(data, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        dump(data, f, ensure_ascii=False, indent=4)
    print(f"{GREEN}Data successfully saved{RESET}")

def get_show_image_url(show_id):
    try:
        data = response_json(show_id)
        result = data.get('result', [])
        if result:
            first_result = result[0] if isinstance(result[0], dict) else {}
            img_url = first_result.get('image_url')
            if img_url:
                return img_url
        return None
    except Exception as e:
        print(f"{RED}Error fetching image URL for show_id {show_id}: {e}{RESET}")
        return None

def get_show_name(show_id):
    try:    
        data = response_json(show_id)
        result = data.get('result', [])
        if result:
            return result[0].get('show_title', 'Unknown Show Title')
    except Exception as e:
        print(f"{RED}Error fetching show name for show_id {show_id}: {e}{RESET}")
        return 'Unknown Show Title'

def get_author_name(show_id):
    try:
        data = response_json(show_id)
        result = data.get('result', [])
        if result:
            if result:
                first_result = result[0][0] if isinstance(result[0], list) else result[0]   
                user_info = first_result.get('user_info', [])
                if user_info:
                    author = user_info.get('fullname', 'Unknown Author Name')
                    return author
    except Exception as e:
        print(f"{RED}Error fetching author name for show_id {show_id}: {e}{RESET}")
        return 'Unknown Author Name'

def get_show_episodecount(show_id):
    count = 0
    try:
        for _ in range(3):
            data = response_json(show_id)
            result = data.get('result', [])
            if result and count < int(result[0].get('episodes_count')):
                count = result[0].get('episodes_count')
            else:
                continue
    except Exception as e:
        print(f"{RED}Error fetching episode count for show_id {show_id}: {e}{RESET}")
    return count
