# Telegram Username Finder

A GUI application for generating Telegram usernames and checking their availability.

## Features
- Generate random usernames of a specified length (5–32 characters).
- Check availability via the Telegram API using Telethon.
- Categorize found usernames into available ones and those taken by deleted accounts.
- Stop the search at any time.
- Save usernames to a text file.
- Save settings (API ID, Hash, parameters) to `config.json`.

## Requirements
- Python 3.7 or higher.
- Installed `telethon` package (see `requirements.txt`).
- API ID and API Hash obtained from [my.telegram.org](https://my.telegram.org).

## Installation
1. Clone or download the project files.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
