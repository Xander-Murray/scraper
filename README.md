# Discord Channel CSV Export Bot

A Discord.py bot command that exports message history from a channel into a CSV file.

It is built for server moderation, archiving, and simple message analysis. The bot reads channel history safely, writes rows directly to a CSV file, and uploads the file back into Discord when finished.

## Features

- Export current channel message history to CSV
- Includes message metadata like:
  - channel name
  - message ID
  - author username
  - display name
  - timestamp (ISO format)
  - message content
  - bot flag
  - attachment URLs
- Optional filters using `FlagConverter`:
  - skip bot messages
  - remove attachment URLs from CSV
  - limit number of messages exported
- Progress updates while exporting
- Basic throttling to reduce rate-limit warnings
- Auto-renames CSV files to avoid overwriting previous exports

## Tech Stack

- Python 3
- [discord.py](https://discordpy.readthedocs.io/)
- `python-dotenv`
