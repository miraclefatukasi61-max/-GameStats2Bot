# GameStats2Bot 🎮

A Telegram bot for tracking gaming statistics with multiple games.

## Features

- 🎮 Multiple games: Tic-Tac-Toe, Rock Paper Scissors, Number Guessing, Dice Roll
- 📊 Track wins, losses, draws, and points
- 🏆 Leaderboard system
- 📜 Game history
- 💾 Persistent SQLite database

## Deployment on Railway

1. **Fork this repository** to your GitHub account
2. **Create a bot** on Telegram via @BotFather
3. **Deploy on Railway:**
   - Connect your GitHub account
   - Select this repository
   - Add environment variable: `TELEGRAM_BOT_TOKEN`
   - Deploy!

## Local Development

```bash
pip install -r requirements.txt
python bot.py
