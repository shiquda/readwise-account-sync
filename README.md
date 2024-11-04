# Readwise Account Sync

A Python script for exporting highlights from one Readwise account and uploading them to another.

## Features

- Use Readwise Export API to retrieve highlights.
- Use Readwise Import API to upload highlights.
- **Your metadata of highlights will be preserved**.

## Usage

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Configuration

1. Open the `main.py` file and locate the following section:

    ```python:main.py
    source_token = '<YOUR_SOURCE_TOKEN>'
    target_token = '<YOUR_TARGET_TOKEN>'
    ```

2. Replace `<YOUR_SOURCE_TOKEN>` and `<YOUR_TARGET_TOKEN>` with your source and target Readwise API Tokens, which can be obtained from [Readwise](https://readwise.io/access_token)

### Run the Script

```bash
python main.py
```

## License

This project is licensed under the [GNU General Public License v3.0](LICENSE).
