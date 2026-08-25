import logging
import random
import os
import sys
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, 
    CommandHandler, 
    CallbackQueryHandler, 
    ContextTypes, 
    MessageHandler, 
    filters
)

from config import BOT_TOKEN, logger
from database import db

# ============================================================
# GAME CONFIGURATION
# ============================================================

GAMES = {
    'tictactoe': {'name': 'Tic-Tac-Toe', 'emoji': '❌', 'desc': 'Classic 3x3 strategy'},
    'rps': {'name': 'Rock Paper Scissors', 'emoji': '✊', 'desc': 'Quick decision game'},
    'guess': {'name': 'Number Guessing', 'emoji': '🔢', 'desc': 'Guess 1-100'},
    'dice': {'name': 'Dice Roll', 'emoji': '🎲', 'desc': 'Roll and test your luck'},
}

# ============================================================
# COMMAND HANDLERS
# ============================================================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    
    # Register user
    db.register_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )
    
    welcome_text = f"""
🎮 **Welcome to GameStats2Bot!** 🎮

Hello {user.first_name}! 👋 Track your gaming stats.

📊 **Features:**
• Track wins, losses, draws
• Leaderboards
• Game history
• Multiple games

🕹️ **Games:**
"""
    for key, game in GAMES.items():
        welcome_text += f"• {game['emoji']} {game['name']}: {game['desc']}\n"
    
    welcome_text += """
📋 **Commands:**
/start - Welcome
/stats - Your stats
/leaderboard - Top players
/history - Your history
/play - Start a game
/games - All games
/help - Help

Start playing! 🚀
    """
    
    keyboard = [
        [InlineKeyboardButton("🎯 Play", callback_data="play")],
        [InlineKeyboardButton("📊 Stats", callback_data="stats")],
        [InlineKeyboardButton("🏆 Leaderboard", callback_data="leaderboard")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        welcome_text, 
        reply_markup=reply_markup, 
        parse_mode='Markdown'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    text = """
📚 **GameStats2Bot Help**

**Commands:**
/start - Start the bot
/help - This help
/stats - Your statistics
/leaderboard - Top players
/history - Your game history
/games - All games
/play - Start a game

**How to Play:**
1. Click a game button or use /play
2. Follow the instructions
3. Stats tracked automatically!

💡 **Tip:** Use the inline buttons!
    """
    await update.message.reply_text(text, parse_mode='Markdown')

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stats command"""
    user = update.effective_user
    stats = db.get_user_stats(user.id)
    
    if not stats or stats['total_games'] == 0:
        await update.message.reply_text(
            "📊 No stats yet!\n\nPlay some games to start tracking! 🎮"
        )
        return
    
    win_rate = (stats['total_wins'] / stats['total_games'] * 100) if stats['total_games'] > 0 else 0
    
    text = f"""
📊 **Your Statistics**

👤 **Player:** {stats['first_name']}
🏆 **Wins:** {stats['total_wins']}
❌ **Losses:** {stats['total_losses']}
⚖️ **Draws:** {stats['total_draws']}
🎮 **Games:** {stats['total_games']}
💎 **Points:** {stats['total_points']}
📈 **Win Rate:** {win_rate:.1f}%

Keep playing! 💪
    """
    await update.message.reply_text(text, parse_mode='Markdown')

async def leaderboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /leaderboard command"""
    leaderboard = db.get_leaderboard(10)
    
    if not leaderboard:
        await update.message.reply_text(
            "🏆 No players yet!\n\nBe the first! 🎮"
        )
        return
    
    text = "🏆 **Leaderboard** 🏆\n\n"
    medals = ['🥇', '🥈', '🥉']
    
    for idx, player in enumerate(leaderboard):
        medal = medals[idx] if idx < 3 else f"{idx+1}."
        name = player.get('username') or player.get('first_name', 'Anonymous')
        
        text += f"{medal} **{name}**\n"
        text += f"   • Wins: {player.get('total_wins', 0)}\n"
        text += f"   • Points: {player.get('total_points', 0)}\n"
        text += f"   • Games: {player.get('total_games', 0)}\n"
        text += f"   • Win Rate: {player.get('win_rate', 0)}%\n\n"
    
    await update.message.reply_text(text, parse_mode='Markdown')

async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /history command"""
    user = update.effective_user
    history = db.get_game_history(user.id, 10)
    
    if not history:
        await update.message.reply_text(
            "📜 No history yet!\n\nPlay some games! 🎮"
        )
        return
    
    text = "📜 **Recent History** 📜\n\n"
    for idx, game in enumerate(history, 1):
        emoji = '✅' if game['result'] == 'win' else '❌' if game['result'] == 'loss' else '⚖️'
        text += f"{idx}. {game['game_type']} vs {game['opponent']}\n"
        text += f"   {emoji} {game['result']} | +{game['points']} points\n"
        text += f"   🕐 {game['played_at'][:16]}\n\n"
    
    await update.message.reply_text(text, parse_mode='Markdown')

async def games_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /games command"""
    text = "🎮 **Available Games** 🎮\n\n"
    
    for game_id, game in GAMES.items():
        text += f"{game['emoji']} **{game['name']}**\n"
        text += f"   • {game['desc']}\n"
        text += f"   • /play_{game_id}\n\n"
    
    text += "💡 Click a game below to start!"
    
    keyboard = []
    for game_id, game in GAMES.items():
        keyboard.append([InlineKeyboardButton(
            f"{game['emoji']} {game['name']}", 
            callback_data=f"play_{game_id}"
        )])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def play_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /play command"""
    text = "🎯 **Choose a game:** 🎯"
    
    keyboard = []
    for game_id, game in GAMES.items():
        keyboard.append([InlineKeyboardButton(
            f"{game['emoji']} {game['name']}", 
            callback_data=f"play_{game_id}"
        )])
    keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

# ============================================================
# GAME HANDLERS
# ============================================================

async def game_tictactoe(update: Update, context: ContextTypes.DEFAULT_TYPE, is_callback=False):
    """Tic-Tac-Toe game"""
    if 'board' not in context.user_data:
        context.user_data['board'] = [' '] * 9
        context.user_data['turn'] = 'X'
    
    board = context.user_data['board']
    turn = context.user_data['turn']
    
    # Show board
    display = ""
    for i in range(3):
        row = []
        for j in range(3):
            idx = i * 3 + j
            row.append(str(idx + 1) if board[idx] == ' ' else board[idx])
        display += " | ".join(row) + "\n"
        if i < 2:
            display += "─────────\n"
    
    text = f"❌ **Tic-Tac-Toe** ⭕\n\n{display}\n\nTurn: {turn}"
    
    keyboard = []
    for i in range(0, 9, 3):
        row = []
        for j in range(3):
            idx = i + j
            if board[idx] == ' ':
                row.append(InlineKeyboardButton(str(idx + 1), callback_data=f"ttt_{idx}"))
            else:
                row.append(InlineKeyboardButton(board[idx], callback_data="ttt_none"))
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("🔄 New", callback_data="ttt_new")])
    keyboard.append([InlineKeyboardButton("❌ Exit", callback_data="cancel")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if is_callback:
        await update.callback_query.message.edit_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def game_rps(update: Update, context: ContextTypes.DEFAULT_TYPE, is_callback=False):
    """Rock Paper Scissors"""
    text = "✊ **Rock Paper Scissors** ✋\n\nChoose:"
    
    keyboard = [
        [
            InlineKeyboardButton("🪨 Rock", callback_data="rps_rock"),
            InlineKeyboardButton("📄 Paper", callback_data="rps_paper"),
            InlineKeyboardButton("✂️ Scissors", callback_data="rps_scissors")
        ],
        [InlineKeyboardButton("❌ Exit", callback_data="cancel")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if is_callback:
        await update.callback_query.message.edit_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def game_guess(update: Update, context: ContextTypes.DEFAULT_TYPE, is_callback=False):
    """Number Guessing"""
    if 'target' not in context.user_data:
        context.user_data['target'] = random.randint(1, 100)
        context.user_data['attempts'] = 0
    
    text = f"🔢 **Number Guessing** 🔢\n\n"
    text += "I'm thinking of 1-100.\n"
    text += f"Attempts: {context.user_data['attempts'] + 1}\n\n"
    text += "Send a number to guess!"
    
    keyboard = [[InlineKeyboardButton("❌ Exit", callback_data="cancel")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if is_callback:
        await update.callback_query.message.edit_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def game_dice(update: Update, context: ContextTypes.DEFAULT_TYPE, is_callback=False):
    """Dice Roll"""
    value = random.randint(1, 6)
    emojis = ['⚀', '⚁', '⚂', '⚃', '⚄', '⚅']
    
    text = f"🎲 **Dice Roll** 🎲\n\n"
    text += f"You rolled: {emojis[value-1]} **{value}**\n\n"
    
    if value % 2 == 0:
        points = value * 2
        text += f"🎉 **Win!** +{points} points"
        result = 'win'
    else:
        points = 0
        text += f"😅 **Lose!** Try again"
        result = 'loss'
    
    db.update_game_result(update.effective_user.id, result, "dice", "AI", points)
    
    keyboard = [
        [InlineKeyboardButton("🔄 Roll Again", callback_data="play_dice")],
        [InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if is_callback:
        await update.callback_query.message.edit_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

# ============================================================
# CALLBACK HANDLER
# ============================================================

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all callbacks"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user = update.effective_user
    
    # Navigation
    if data == "main_menu":
        await start_command(update, context)
        return
    if data == "play":
        await play_command(update, context)
        return
    if data == "stats":
        await stats_command(update, context)
        return
    if data == "leaderboard":
        await leaderboard_command(update, context)
        return
    
    if data == "cancel":
        for key in ['board', 'turn', 'target', 'attempts']:
            if key in context.user_data:
                del context.user_data[key]
        await query.message.edit_text("❌ Cancelled. Type /play to start again!")
        return
    
    # Game selection
    if data.startswith("play_"):
        game = data.replace("play_", "")
        if game == "tictactoe":
            await game_tictactoe(update, context, is_callback=True)
        elif game == "rps":
            await game_rps(update, context, is_callback=True)
        elif game == "guess":
            await game_guess(update, context, is_callback=True)
        elif game == "dice":
            await game_dice(update, context, is_callback=True)
        return
    
    # Tic-Tac-Toe
    if data.startswith("ttt_"):
        pos = data.replace("ttt_", "")
        
        if pos == "new":
            context.user_data['board'] = [' '] * 9
            context.user_data['turn'] = 'X'
            await game_tictactoe(update, context, is_callback=True)
            return
        
        if pos == "none":
            return
        
        pos = int(pos)
        board = context.user_data['board']
        
        if board[pos] != ' ':
            await query.answer("Taken!")
            return
        
        # User move
        board[pos] = 'X'
        
        # Check win
        win_patterns = [
            [0,1,2], [3,4,5], [6,7,8],
            [0,3,6], [1,4,7], [2,5,8],
            [0,4,8], [2,4,6]
        ]
        
        winner = None
        for pattern in win_patterns:
            if board[pattern[0]] == board[pattern[1]] == board[pattern[2]] != ' ':
                winner = board[pattern[0]]
                break
        
        if winner == 'X':
            db.update_game_result(user.id, 'win', "tictactoe", "AI", 10)
            context.user_data['board'] = [' '] * 9
            await query.message.edit_text("🎉 **You win!** +10 points", parse_mode='Markdown')
            return
        
        if ' ' not in board:
            db.update_game_result(user.id, 'draw', "tictactoe", "AI", 5)
            context.user_data['board'] = [' '] * 9
            await query.message.edit_text("⚖️ **Draw!** +5 points", parse_mode='Markdown')
            return
        
        # AI move (O)
        available = [i for i in range(9) if board[i] == ' ']
        if available:
            ai_move = random.choice(available)
            board[ai_move] = 'O'
            
            for pattern in win_patterns:
                if board[pattern[0]] == board[pattern[1]] == board[pattern[2]] != ' ':
                    winner = board[pattern[0]]
                    break
            
            if winner == 'O':
                db.update_game_result(user.id, 'loss', "tictactoe", "AI", 0)
                context.user_data['board'] = [' '] * 9
                await query.message.edit_text("😅 **AI wins!** Better luck next time!", parse_mode='Markdown')
                return
            
            if ' ' not in board:
                db.update_game_result(user.id, 'draw', "tictactoe", "AI", 5)
                context.user_data['board'] = [' '] * 9
                await query.message.edit_text("⚖️ **Draw!** +5 points", parse_mode='Markdown')
                return
        
        await game_tictactoe(update, context, is_callback=True)
        return
    
    # RPS
    if data.startswith("rps_"):
        user_move = data.replace("rps_", "")
        moves = ['rock', 'paper', 'scissors']
        bot_move = random.choice(moves)
        
        emojis = {'rock': '🪨', 'paper': '📄', 'scissors': '✂️'}
        
        result_map = {
            ('rock', 'scissors'): 'win',
            ('scissors', 'paper'): 'win',
            ('paper', 'rock'): 'win',
        }
        
        if user_move == bot_move:
            result = 'draw'
            points = 3
            msg = "⚖️ Draw! +3 points"
        elif (user_move, bot_move) in result_map:
            result = 'win'
            points = 5
            msg = "🎉 You win! +5 points"
        else:
            result = 'loss'
            points = 0
            msg = "😅 You lose!"
        
        db.update_game_result(user.id, result, "rps", "AI", points)
        
        text = f"✊ **Rock Paper Scissors** ✋\n\n"
        text += f"You: {emojis[user_move]} {user_move}\n"
        text += f"Bot: {emojis[bot_move]} {bot_move}\n\n"
        text += f"**{msg}**"
        
        keyboard = [
            [InlineKeyboardButton("🔄 Play Again", callback_data="play_rps")],
            [InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.edit_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        return

# ============================================================
# MESSAGE HANDLER
# ============================================================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages"""
    user = update.effective_user
    text = update.message.text
    
    # Guess game
    if 'target' in context.user_data and text.isdigit():
        guess = int(text)
        target = context.user_data['target']
        attempts = context.user_data['attempts'] + 1
        context.user_data['attempts'] = attempts
        
        if guess < 1 or guess > 100:
            await update.message.reply_text("⚠️ Enter 1-100!")
            return
        
        if guess == target:
            points = max(10 - attempts + 1, 1)
            db.update_game_result(user.id, 'win', "guess", "AI", points)
            await update.message.reply_text(
                f"🎉 **You got it!**\n\nNumber: {target}\nAttempts: {attempts}\n+{points} points! 🏆",
                parse_mode='Markdown'
            )
            del context.user_data['target']
            del context.user_data['attempts']
        elif guess < target:
            await update.message.reply_text(f"📈 **Higher!** (Attempt {attempts})")
        else:
            await update.message.reply_text(f"📉 **Lower!** (Attempt {attempts})")
        return
    
    if text.lower() in ['hi', 'hello', 'hey', 'start']:
        await start_command(update, context)
    else:
        await update.message.reply_text(
            f"🤔 I don't understand.\n\nType /help for commands!"
        )

# ============================================================
# MAIN
# ============================================================

def main():
    """Start the bot"""
    try:
        logger.info("🚀 Starting GameStats2Bot...")
        
        # Create application
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("stats", stats_command))
        application.add_handler(CommandHandler("leaderboard", leaderboard_command))
        application.add_handler(CommandHandler("history", history_command))
        application.add_handler(CommandHandler("games", games_command))
        application.add_handler(CommandHandler("play", play_command))
        
        # Game commands
        application.add_handler(CommandHandler("play_tictactoe", game_tictactoe))
        application.add_handler(CommandHandler("play_rps", game_rps))
        application.add_handler(CommandHandler("play_guess", game_guess))
        application.add_handler(CommandHandler("play_dice", game_dice))
        
        # Callback and message handlers
        application.add_handler(CallbackQueryHandler(handle_callback))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        # Start polling
        logger.info("✅ Bot is running! Polling for updates...")
        application.run_polling()
        
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
