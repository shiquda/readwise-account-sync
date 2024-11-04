import requests
import json
import time
from tqdm import tqdm

READWISE_API_URL = 'https://readwise.io/api/v2'


def get_highlights(token):
    """
    Retrieve all highlights from a specified Readwise account using the export API.
    """
    import datetime
    full_data = []
    next_page_cursor = None
    headers = {'Authorization': f'Token {token}'}
    params = {}
    updated_after = None  # Set to retrieve highlights updated after a specific time if needed

    with tqdm(total=100, desc="Progress", unit="times") as pbar:
        while True:
            if next_page_cursor:
                params['pageCursor'] = next_page_cursor
            if updated_after:
                params['updatedAfter'] = updated_after.isoformat()
            print("Making export API request with params " + str(params) + "...")
            response = requests.get(
                url="https://readwise.io/api/v2/export/",
                params=params,
                headers=headers,
            )
            pbar.update(1)

            if response.status_code == 200:
                data = response.json()
                full_data.extend(data.get('results', []))
                next_page_cursor = data.get('nextPageCursor')
                if not next_page_cursor:
                    break
            elif response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', '60'))
                print(f'Request rate limited, retrying after {retry_after} seconds...')
                for _ in tqdm(range(retry_after), desc="Waiting", unit="seconds"):
                    time.sleep(1)
            else:
                print(f'Error retrieving highlights: {response.status_code}')
                print(response.text)
                break

    return full_data


def upload_highlights(token, full_data):
    """
    Upload highlights to a specified Readwise account using the import API.
    """
    headers = {'Authorization': f'Token {token}', 'Content-Type': 'application/json'}
    url = f'{READWISE_API_URL}/highlights/'

    # Convert highlight data to the required upload format
    highlights_data = []
    for item in full_data:
        for highlight in item.get('highlights', []):
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
                'highlighted_at': highlight.get('highlighted_at', ''),
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
            print(f'Upload rate limited, retrying after {retry_after} seconds...')
            for _ in tqdm(range(retry_after), desc="Waiting", unit="seconds"):
                time.sleep(1)
            return upload_highlights(token, full_data)  # Recursive retry
        else:
            print(f'Upload failed with status code: {response.status_code}')
            print(response.text)
            return None
    except requests.exceptions.RequestException as e:
        print(f'Upload request exception: {e}')
        return None


def main():
    UPLOAD_FROM_FILE = False
    # You can get your token from https://readwise.io/access_token
    source_token = '<YOUR_SOURCE_TOKEN>'
    target_token = '<YOUR_TARGET_TOKEN>'

    if UPLOAD_FROM_FILE:
        # Read highlights from a file, which is generated while retrieving highlights
        with open('highlights.json', 'r') as f:
            highlights = json.load(f)
    else:
        # Retrieve all highlights from the source account
        highlights = get_highlights(source_token)
        with open('highlights.json', 'w') as f:
            json.dump(highlights, f)

    print(f'Total items retrieved: {len(highlights)}.')

    # Upload highlights to the target account
    upload_highlights(target_token, highlights)


if __name__ == '__main__':
    main()
