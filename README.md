# Readwise Account Sync

A Python script for exporting highlights from one Readwise account and uploading them to another.

## Features

- Use [Readwise API](https://readwise.io/api_deets) to retrieve and upload highlights.
- Readwise Reader info is also supported. However, highlights in Reader are **not** supported due to the limitation of [Readwise Reader API](https://readwise.io/reader_api). Tell me if you have any ideas to fix this.
- **Your metadata of highlights will be preserved**.

## Disclaimer

Please verify the data integrity after using this script. The author is not responsible for any data loss or damage that may occur during the sync process. Use this script at your own risk.

## Usage

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Configuration

Open the `config.cfg` file and fill in your source and target Readwise API Tokens, which can be obtained from [Readwise](https://readwise.io/access_token).

### Run the Script

```bash
python main.py
```

## License

This project is licensed under the [GNU General Public License v3.0](LICENSE).
