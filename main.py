import requests
import json
import time
from datetime import datetime
from tqdm import tqdm
import configparser

READWISE_API_URL = 'https://readwise.io/api'
# You can check https://readwise.io/api_deets for Readwise API details
# check https://readwise.io/reader_api for Readwise Reader API details

config = configparser.ConfigParser()
config.read('config.cfg')

UPLOAD_FROM_FILE = config.getboolean('SYNC', 'UPLOAD_FROM_FILE')
SOURCE_TOKEN = config.get('SYNC', 'SOURCE_TOKEN')
TARGET_TOKEN = config.get('SYNC', 'TARGET_TOKEN')


def get_highlights(token):
    """
    Retrieve all highlights from a specified Readwise account using the export API.
    """
    full_data = []
    next_page_cursor = None
    headers = {'Authorization': f'Token {token}'}
    params = {}
    updated_after = None  # Set to retrieve highlights updated after a specific time if needed

    page_counter = 0
    print("Getting highlights...")
    while True:
        if next_page_cursor:
            params['pageCursor'] = next_page_cursor
        if updated_after:
            params['updatedAfter'] = updated_after.isoformat()
        # print("Making export API request with params " + str(params) + "...")
        response = requests.get(
            url=f"{READWISE_API_URL}/v2/export/",
            params=params,
            headers=headers,
        )

        if response.status_code == 200:
            data = response.json()
            full_data.extend(data.get('results', []))
            next_page_cursor = data.get('nextPageCursor')
            if not next_page_cursor:
                break
        elif response.status_code == 429:
            retry_after = int(response.headers.get('Retry-After', '60'))
            for _ in tqdm(range(retry_after), desc=f"Waiting for {retry_after} seconds:", unit="seconds"):
                time.sleep(1)
        else:
            print(f'Error retrieving highlights: {response.status_code}')
            print(response.text)
            break
        page_counter += 1
        print(f"Progress: {page_counter} page fetched")
    return full_data


def upload_highlights(token, full_data):
    """
    Upload highlights to a specified Readwise account using the import API.
    """
    print(f"Uploading {len(full_data)} highlights...")
    headers = {'Authorization': f'Token {token}', 'Content-Type': 'application/json'}
    url = f'{READWISE_API_URL}/v2/highlights/'

    # Convert highlight data to the required upload format
    highlights_data = []
    for item in full_data:
        for highlight in item.get('highlights', []):
            highlighted_at = highlight.get('highlighted_at', '')
            if highlighted_at == None:
                highlighted_at = datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            highlight_data = {
                'text': highlight.get('text', ''),
                'title': item.get('title', ''),
                'author': item.get('author', ''),
                'image_url': item.get('cover_image_url', ''),
                'source_url': item.get('source_url', ''),
                'category': item.get('category', ''),
                'note': highlight.get('note', ''),
                'location': highlight.get('location', ''),
                'location_type': highlight.get('location_type', ''),
                'highlighted_at': highlighted_at,
                'highlight_url': item.get('unique_url', '')
            }
            # Remove keys with empty values
            highlight_data = {k: v for k, v in highlight_data.items() if v != ''}
            highlights_data.append(highlight_data)

    try:
        response = requests.post(url, json={'highlights': highlights_data}, headers=headers)
        if response.status_code == 200:
            print(f'Successfully uploaded {len(highlights_data)} highlights.')
            return response.json()
        elif response.status_code == 429:
            retry_after = int(response.headers.get('Retry-After', '60'))
            # print(f'Upload rate limited, retrying after {retry_after} seconds...')
            for _ in tqdm(range(retry_after), desc=f"Waiting for {retry_after} seconds:", unit="seconds"):
                time.sleep(1)
            return upload_highlights(token, full_data)  # Recursive retry
        else:
            print(f'Upload failed with status code: {response.status_code}')
            print(response.text)
            return None
    except requests.exceptions.RequestException as e:
        print(f'Upload request exception: {e}')
        return None


def get_reader_info(token):
    headers = {'Authorization': f'Token {token}', 'Content-Type': 'application/json'}
    url = f'{READWISE_API_URL}/v3/list/'
    params = {}
    params['withHtmlContent'] = True
    page_cursor = None
    full_data = []
    print("Getting reader info...")
    page_counter = 0
    while True:
        # 设置参数
        if page_cursor:
            params['pageCursor'] = page_cursor

        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            page_cursor = response.json().get('nextPageCursor')
            results = response.json().get('results', [])
            full_data.extend(results)
            if not page_cursor:
                break
        elif response.status_code == 429:
            retry_after = int(response.headers.get('Retry-After', '60'))
            print(f'Request rate limited, retrying after {retry_after} seconds...')
            for _ in tqdm(range(retry_after), desc="Waiting", unit="seconds"):
                time.sleep(1)
        else:
            print(f'Error retrieving reader info: {response.status_code}')
            print(response.text)
            break
        page_counter += 1
        print(f"Progress: {page_counter} page fetched")
    return full_data


def upload_reader_info(token, full_data):
    # skip highlights
    full_data = [item for item in full_data if item.get(
        'parent_id') is None]
    headers = {'Authorization': f'Token {token}', 'Content-Type': 'application/json'}
    upload_url = f'{READWISE_API_URL}/v3/save/'
    tqdm_desc = "Uploading reader info..."
    for item in tqdm(full_data, desc=tqdm_desc, unit="items"):
        try:
            if item.get('tags') and len(item.get('tags')) > 0:
                tags = [tag.get('name') for tag in item.get('tags').values()]
            else:
                tags = []

            if item.get('published_date'):
                published_date = datetime.fromtimestamp(
                    int(item.get('published_date', 0))/1000).strftime('%Y-%m-%dT%H:%M:%S+00:00')
            else:
                published_date = ''
            body = {
                'url': item.get('url', 'source_url'),
                'html': item.get('html', ''),
                'title': item.get('title', ''),
                'author': item.get('author', ''),
                'summary': item.get('summary', ''),
                'published_date': published_date,
                'image_url': item.get('image_url', ''),
                'location': item.get('location', ''),
                'category': item.get('category', ''),
                'tags': tags,
                'notes': item.get('notes', ''),
                'html': item.get('html_content', ''),
                'source': item.get('source', ''),
                'saved_using': item.get('saved_using', ''),
            }
            # clear empty values
            body = {k: v for k, v in body.items() if v != ''}
            response = requests.post(upload_url, json=body, headers=headers)
            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', '60'))
                # print(f'Request rate limited, retrying after {retry_after} seconds...')
                for _ in tqdm(range(retry_after), desc=f"Waiting for {retry_after} seconds:", unit="seconds"):
                    time.sleep(1)
                # Retry current item
                response = requests.post(upload_url, json=body, headers=headers)
            elif response.status_code == 502:
                retry_after = 5
                max_retry = 3
                for _ in range(max_retry):
                    time.sleep(retry_after)
                    response = requests.post(upload_url, json=body, headers=headers)
                    if response.status_code == 200:
                        break
                    else:
                        print(f'Upload failed, status code: {response.status_code}')
                        print(f'Error message: {response.text}')
            elif response.status_code not in [200, 201]:
                print(f'Upload failed, status code: {response.status_code}')
                print(f'Error message: {response.text}')
        except requests.exceptions.RequestException as e:
            print(f'Request exception: {e}')
        except Exception as e:
            print(f'Error occurred: {e}')
            break


def main():
    if UPLOAD_FROM_FILE:
        # Read highlights from a file, which is generated while retrieving highlights
        with open('highlights_info.json', 'r') as f:
            highlights = json.load(f)
        with open('reader_info.json', 'r') as f:
            reader_info = json.load(f)

    else:
        # Retrieve all highlights from the source account
        highlights = get_highlights(SOURCE_TOKEN)
        with open('highlights_info.json', 'w') as f:
            json.dump(highlights, f)
        reader_info = get_reader_info(SOURCE_TOKEN)
        with open('reader_info.json', 'w') as f:
            json.dump(reader_info, f)

    # Upload highlights to the target account
    upload_highlights(TARGET_TOKEN, highlights)
    upload_reader_info(TARGET_TOKEN, reader_info)


if __name__ == '__main__':
    main()
