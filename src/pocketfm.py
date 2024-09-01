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
    try:
        config.read('config.ini')
        return config.get('pocketfm', 'access_token')
    except (NoSectionError, NoOptionError) as e:
        print(f"{YELLOW}Configuration error: {e}:: Defaulting to guest access.{RESET}")
        return None
    except FileNotFoundError:
        print(f"{YELLOW}Configuration file 'config.ini' not found. Defaulting to guest access.{RESET}")
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
        print(f"{BLUE}Fetching data for show: {get_show_name(show_id)}, curr_ptr: {curr_ptr}...{RESET}")
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
                        curr_ptr = str(int(curr_ptr_prev) + 10)
                        continue
                    if not curr_ptr or curr_ptr == -1:
                        break
                elif str(curr_ptr) >= str(episode_count):
                    break
                else:
                    print(f"{RED}The 'result' field is not present in the response. Retrying...{RESET}")
                    continue
            else:
                print(f"{RED}Failed to fetch data. Status code: {response.status_code}{RESET}")
                break
        except Exception as e:
            print(f"{RED}An error occurred: {e}{RESET}")
            break
    session.close()
    return all_stories

def response_json(show_id, headers=headers(), base_url=base_url()):
    params = {'show_id': show_id}
    try:
        response = get(base_url, headers=headers, params=params)
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
                author = user_info.get('fullname', 'Unknown Author Name')
                return author
    return 'Unknown Author Name'

def get_show_episodecount(show_id):
    count = 0
    for _ in range(5):
        data = response_json(show_id)
        result = data.get('result', [])
        if result and count < int(result[0].get('episodes_count')):
            count = result[0].get('episodes_count')
        else:
            continue
    return count
