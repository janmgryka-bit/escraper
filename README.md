# EScraper - OLX & Facebook iPhone Deal Hunter

Automated Discord bot that monitors OLX and Facebook for iPhone deals and sends real-time notifications.

## Features

- 🔍 **OLX Scraping**: Monitors OLX for new iPhone listings under specified budget
- 🔔 **Facebook Notifications**: Checks Facebook notifications for relevant posts
- 💬 **Discord Integration**: Sends formatted embeds to Discord channel
- 🗄️ **SQLite Database**: Tracks seen offers to avoid duplicates
- 🚀 **Headless Browser**: Uses Playwright for reliable scraping
- ⚡ **Fast Mode**: Blocks images for faster page loads

## Requirements

- Python 3.8+
- Discord Bot Token
- Facebook account (for notifications)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/janmgryka-bit/escraper.git
cd escraper
```

2. Install dependencies:
```bash
pip install -r requirements.txt
playwright install chromium
```

3. Create `.env` file with your credentials:
```env
DISCORD_TOKEN=your_discord_bot_token
```

4. Login to Facebook (one-time setup):
```bash
python fb_login.py
```

## Usage

Run the bot:
```bash
python main.py
```

The bot will:
- Check OLX every 2-4 minutes for new iPhone listings
- Monitor Facebook notifications
- Send Discord notifications for deals under 500 PLN

## Configuration

Edit `main.py` to adjust:
- `MAX_BUDGET`: Maximum price filter (default: 500 PLN)
- `CHANNEL_ID`: Discord channel ID for notifications
- Search parameters in OLX URL

## Project Structure

```
escraper_v1/
├── main.py           # Main bot logic
├── fb_login.py       # Facebook login helper
├── requirements.txt  # Python dependencies
├── .env             # Environment variables (not committed)
├── hunter_final.db  # SQLite database (auto-created)
└── fb_data/         # Facebook session data (not committed)
```

## License

MIT License
