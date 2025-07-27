import logging
import asyncio
import uuid
from decimal import Decimal
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters
from db import db, create_user_table, create_friends_table, create_challenges_table, create_transactions_table, create_game_sessions_table
from payments import get_user_balance, process_deposit, process_withdrawal, get_deposit_address, process_bet, get_transaction_history
from ws_server import game_server
from config import TELEGRAM_BOT_TOKEN

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# User session storage
user_sessions = {}

def create_neon_message(title: str, content: str, footer: str = "") -> str:
    """Create neon-style message formatting"""
    neon_border = "═" * 30
    return f"""
╔{neon_border}╗
║  🎮 **{title}** 🎮  ║
╠{neon_border}╣
║ {content} ║
╚{neon_border}╝
{footer}
"""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Main start command with neon-style interface"""
    user = update.effective_user
    telegram_id = user.id
    
    # Check if user exists
    existing = await db.execute_one("SELECT id, username, balance FROM users WHERE telegram_id=%s", (telegram_id,))
    
    if existing:
        user_id, username, balance = existing
        keyboard = [
            [
                InlineKeyboardButton("🎯 Play Games", callback_data="play_games"),
                InlineKeyboardButton("⚔️ Challenge", callback_data="challenge_menu")
            ],
            [
                InlineKeyboardButton("👥 Friends", callback_data="friends_menu"),
                InlineKeyboardButton("💰 Wallet", callback_data="wallet_menu")
            ],
            [
                InlineKeyboardButton("📊 Stats", callback_data="stats"),
                InlineKeyboardButton("⚙️ Settings", callback_data="settings")
            ]
        ]
        
        welcome_content = f"""
**NEON BETTING ARENA**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👋 Welcome back, **{username}**!
💰 Balance: **{balance:.2f}€**
🎮 Ready to play and win?

Choose your next move:
        """
        
    else:
        keyboard = [
            [
                InlineKeyboardButton("🚀 Register", callback_data="register"),
                InlineKeyboardButton("🔑 Login", callback_data="login")
            ]
        ]
        
        welcome_content = f"""
**NEON BETTING ARENA**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✨ Welcome to the ultimate gaming experience!
🎮 Snake • Ping Pong • Tetris
💰 Bet from 0.10€ to 900€
🏆 Challenge friends and win big!

Join the arena now:
        """
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text(welcome_content, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.callback_query.edit_message_text(welcome_content, reply_markup=reply_markup, parse_mode='Markdown')

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all button callbacks"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user = update.effective_user
    telegram_id = user.id
    
    # Get user from database
    user_data = await db.execute_one("SELECT id, username, balance FROM users WHERE telegram_id=%s", (telegram_id,))
    
    if data == "register":
        await handle_register(update, context)
    elif data == "login":
        await handle_login(update, context)
    elif data == "play_games":
        await handle_play_games(update, context)
    elif data == "challenge_menu":
        await handle_challenge_menu(update, context)
    elif data == "friends_menu":
        await handle_friends_menu(update, context)
    elif data == "wallet_menu":
        await handle_wallet_menu(update, context)
    elif data == "stats":
        await handle_stats(update, context)
    elif data == "settings":
        await handle_settings(update, context)
    elif data.startswith("game_"):
        await handle_game_selection(update, context, data)
    elif data.startswith("bet_"):
        await handle_bet_selection(update, context, data)
    elif data == "back_main":
        await start(update, context)
    elif data.startswith("deposit_"):
        await handle_deposit(update, context, data)
    elif data.startswith("withdraw"):
        await handle_withdrawal(update, context)
    elif data == "transaction_history":
        await handle_transaction_history(update, context)

async def handle_register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user registration"""
    user = update.effective_user
    telegram_id = user.id
    username = user.username or user.first_name

    # Check if user already registered
    existing = await db.execute_one("SELECT id FROM users WHERE telegram_id=%s", (telegram_id,))
    if existing:
        await update.callback_query.edit_message_text("⚠️ You are already registered!")
        return

    # Insert new user
    await db.execute(
        "INSERT INTO users (telegram_id, username, balance) VALUES (%s, %s, %s)",
        (telegram_id, username, 0.0)
    )
    
    # Generate deposit address
    user_id = await db.execute_one("SELECT id FROM users WHERE telegram_id=%s", (telegram_id,))
    deposit_result = await get_deposit_address(user_id[0])
    
    success_message = f"""
**🎉 REGISTRATION SUCCESSFUL! 🎉**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Welcome to the arena, **{username}**!

🎮 You can now play all games
💰 Your starting balance: **0.00€**
🔗 Your deposit address: `{deposit_result.get('address', 'N/A')}`

Ready to start your gaming journey?
    """
    
    keyboard = [
        [InlineKeyboardButton("🚀 Start Playing", callback_data="play_games")],
        [InlineKeyboardButton("💰 Add Funds", callback_data="wallet_menu")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="back_main")]
    ]
    
    await update.callback_query.edit_message_text(
        success_message, 
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def handle_login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user login (simplified - just check if registered)"""
    user = update.effective_user
    telegram_id = user.id
    
    existing = await db.execute_one("SELECT id, username, balance FROM users WHERE telegram_id=%s", (telegram_id,))
    
    if not existing:
        await update.callback_query.edit_message_text("❌ Please register first!")
        return
        
    await start(update, context)

async def handle_play_games(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show available games"""
    games_message = f"""
**🎮 GAME SELECTION 🎮**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Choose your game:

🐍 **SNAKE**
Classic snake game with multiplayer action!

🏓 **PING PONG**
Fast-paced paddle battle!

🧩 **TETRIS**
Block-stacking competition!

💰 Bet Range: **0.10€ - 900€**
🏆 Winner takes all (minus 10% house fee)
    """
    
    keyboard = [
        [
            InlineKeyboardButton("🐍 Snake", callback_data="game_snake"),
            InlineKeyboardButton("🏓 Ping Pong", callback_data="game_pong")
        ],
        [
            InlineKeyboardButton("🧩 Tetris", callback_data="game_tetris")
        ],
        [
            InlineKeyboardButton("🏠 Main Menu", callback_data="back_main")
        ]
    ]
    
    await update.callback_query.edit_message_text(
        games_message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def handle_game_selection(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    """Handle game selection and bet amount"""
    game_type = data.split("_")[1]
    
    user_sessions[update.effective_user.id] = {"selected_game": game_type}
    
    bet_message = f"""
**💰 BET SELECTION 💰**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Selected Game: **{game_type.upper()}**

Choose your bet amount:
    """
    
    keyboard = [
        [
            InlineKeyboardButton("0.10€", callback_data="bet_0.10"),
            InlineKeyboardButton("1€", callback_data="bet_1.00"),
            InlineKeyboardButton("5€", callback_data="bet_5.00")
        ],
        [
            InlineKeyboardButton("10€", callback_data="bet_10.00"),
            InlineKeyboardButton("50€", callback_data="bet_50.00"),
            InlineKeyboardButton("100€", callback_data="bet_100.00")
        ],
        [
            InlineKeyboardButton("💰 Custom Amount", callback_data="bet_custom")
        ],
        [
            InlineKeyboardButton("🔙 Back", callback_data="play_games")
        ]
    ]
    
    await update.callback_query.edit_message_text(
        bet_message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def handle_bet_selection(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    """Handle bet amount selection"""
    user_id = update.effective_user.id
    
    if data == "bet_custom":
        await update.callback_query.edit_message_text(
            "💰 Please enter your custom bet amount (0.10€ - 900€):",
            parse_mode='Markdown'
        )
        user_sessions[user_id]["waiting_for_bet"] = True
        return
    
    bet_amount = float(data.split("_")[1])
    game_type = user_sessions.get(user_id, {}).get("selected_game", "snake")
    
    # Get user data
    user_data = await db.execute_one("SELECT id, balance FROM users WHERE telegram_id=%s", (user_id,))
    if not user_data:
        await update.callback_query.edit_message_text("❌ User not found!")
        return
        
    db_user_id, balance = user_data
    
    if balance < bet_amount:
        await update.callback_query.edit_message_text(
            f"❌ Insufficient balance! You have {balance:.2f}€, need {bet_amount:.2f}€"
        )
        return
    
    # Create challenge
    challenge_id = await create_open_challenge(db_user_id, game_type, bet_amount)
    
    challenge_message = f"""
**⚔️ CHALLENGE CREATED ⚔️**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎮 Game: **{game_type.upper()}**
💰 Bet: **{bet_amount:.2f}€**
🆔 Challenge ID: **{challenge_id}**

Waiting for opponent...

Share this challenge ID with friends or wait for a random opponent!
    """
    
    keyboard = [
        [InlineKeyboardButton("❌ Cancel Challenge", callback_data=f"cancel_challenge_{challenge_id}")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="back_main")]
    ]
    
    await update.callback_query.edit_message_text(
        challenge_message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def handle_wallet_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle wallet operations"""
    user = update.effective_user
    user_data = await db.execute_one("SELECT id, balance FROM users WHERE telegram_id=%s", (user.id,))
    
    if not user_data:
        await update.callback_query.edit_message_text("❌ User not found!")
        return
        
    user_id, balance = user_data
    
    wallet_message = f"""
**💰 CRYPTO WALLET 💰**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💳 Current Balance: **{balance:.2f}€**

🔗 Supported Cryptocurrencies:
• Bitcoin (BTC)
• Ethereum (ETH)

Choose an action:
    """
    
    keyboard = [
        [
            InlineKeyboardButton("📥 Deposit BTC", callback_data="deposit_BTC"),
            InlineKeyboardButton("📥 Deposit ETH", callback_data="deposit_ETH")
        ],
        [
            InlineKeyboardButton("📤 Withdraw", callback_data="withdraw")
        ],
        [
            InlineKeyboardButton("📊 Transaction History", callback_data="transaction_history")
        ],
        [
            InlineKeyboardButton("🏠 Main Menu", callback_data="back_main")
        ]
    ]
    
    await update.callback_query.edit_message_text(
        wallet_message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def handle_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    """Handle deposit address generation"""
    currency = data.split("_")[1]
    user = update.effective_user
    user_data = await db.execute_one("SELECT id FROM users WHERE telegram_id=%s", (user.id,))
    
    if not user_data:
        await update.callback_query.edit_message_text("❌ User not found!")
        return
        
    user_id = user_data[0]
    deposit_result = await get_deposit_address(user_id, currency)
    
    if deposit_result["success"]:
        deposit_message = f"""
**📥 DEPOSIT {currency} 📥**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Your {currency} deposit address:

`{deposit_result['address']}`

⚠️ **IMPORTANT:**
• Only send {currency} to this address
• Minimum deposit: 0.01 {currency}
• Funds will be credited automatically
• Keep this address safe!

QR Code: {deposit_result.get('qr_code', 'N/A')}
        """
        
        keyboard = [
            [InlineKeyboardButton("🔄 Generate New Address", callback_data=f"deposit_{currency}")],
            [InlineKeyboardButton("🔙 Back to Wallet", callback_data="wallet_menu")]
        ]
        
        await update.callback_query.edit_message_text(
            deposit_message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    else:
        await update.callback_query.edit_message_text(f"❌ Error: {deposit_result['error']}")

async def handle_friends_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle friends list and management"""
    user = update.effective_user
    user_data = await db.execute_one("SELECT id FROM users WHERE telegram_id=%s", (user.id,))
    
    if not user_data:
        await update.callback_query.edit_message_text("❌ User not found!")
        return
        
    user_id = user_data[0]
    
    # Get friends list
    friends = await db.execute(
        """SELECT u.username, u.id FROM users u 
           JOIN friends f ON u.id = f.friend_id 
           WHERE f.user_id = %s""",
        (user_id,)
    )
    
    friends_list = "\n".join([f"👤 {friend[0]}" for friend in friends]) if friends else "No friends yet"
    
    friends_message = f"""
**👥 FRIENDS LIST 👥**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{friends_list}

Manage your gaming network:
    """
    
    keyboard = [
        [InlineKeyboardButton("➕ Add Friend", callback_data="add_friend")],
        [InlineKeyboardButton("⚔️ Challenge Friend", callback_data="challenge_friend")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="back_main")]
    ]
    
    await update.callback_query.edit_message_text(
        friends_message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def handle_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user statistics"""
    user = update.effective_user
    user_data = await db.execute_one("SELECT id, balance FROM users WHERE telegram_id=%s", (user.id,))
    
    if not user_data:
        await update.callback_query.edit_message_text("❌ User not found!")
        return
        
    user_id, balance = user_data
    
    # Get game statistics
    total_games = await db.execute_one(
        "SELECT COUNT(*) FROM challenges WHERE (challenger_id = %s OR challengee_id = %s) AND status = 'finished'",
        (user_id, user_id)
    )
    
    wins = await db.execute_one(
        "SELECT COUNT(*) FROM challenges WHERE winner_id = %s",
        (user_id,)
    )
    
    total_bet = await db.execute_one(
        "SELECT SUM(amount) FROM transactions WHERE user_id = %s AND transaction_type = 'bet'",
        (user_id,)
    )
    
    total_winnings = await db.execute_one(
        "SELECT SUM(amount) FROM transactions WHERE user_id = %s AND transaction_type = 'payout'",
        (user_id,)
    )
    
    stats_message = f"""
**📊 YOUR STATS 📊**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💰 Current Balance: **{balance:.2f}€**
🎮 Total Games: **{total_games[0] if total_games else 0}**
🏆 Wins: **{wins[0] if wins else 0}**
💸 Total Bet: **{total_bet[0] if total_bet and total_bet[0] else 0:.2f}€**
💰 Total Winnings: **{total_winnings[0] if total_winnings and total_winnings[0] else 0:.2f}€**

Win Rate: **{(wins[0] / total_games[0] * 100) if total_games and total_games[0] > 0 else 0:.1f}%**
    """
    
    keyboard = [
        [InlineKeyboardButton("🏠 Main Menu", callback_data="back_main")]
    ]
    
    await update.callback_query.edit_message_text(
        stats_message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def handle_transaction_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show transaction history"""
    user = update.effective_user
    user_data = await db.execute_one("SELECT id FROM users WHERE telegram_id=%s", (user.id,))
    
    if not user_data:
        await update.callback_query.edit_message_text("❌ User not found!")
        return
        
    user_id = user_data[0]
    history_result = await get_transaction_history(user_id, 10)
    
    if history_result["success"]:
        transactions = history_result["transactions"]
        
        if transactions:
            tx_list = []
            for tx in transactions:
                emoji = {"deposit": "📥", "withdrawal": "📤", "bet": "🎯", "payout": "💰"}.get(tx["type"], "💳")
                tx_list.append(f"{emoji} {tx['type'].title()}: {tx['amount']:.2f}€")
            
            history_text = "\n".join(tx_list)
        else:
            history_text = "No transactions yet"
            
        history_message = f"""
**📊 TRANSACTION HISTORY 📊**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{history_text}

Last 10 transactions shown.
        """
    else:
        history_message = f"❌ Error loading history: {history_result['error']}"
    
    keyboard = [
        [InlineKeyboardButton("🔙 Back to Wallet", callback_data="wallet_menu")]
    ]
    
    await update.callback_query.edit_message_text(
        history_message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def handle_challenge_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle challenge menu"""
    user = update.effective_user
    user_data = await db.execute_one("SELECT id FROM users WHERE telegram_id=%s", (user.id,))
    
    if not user_data:
        await update.callback_query.edit_message_text("❌ User not found!")
        return
        
    user_id = user_data[0]
    
    # Get pending challenges
    pending_challenges = await db.execute(
        "SELECT id, game_type, bet_amount FROM challenges WHERE challengee_id = %s AND status = 'pending' LIMIT 5",
        (user_id,)
    )
    
    # Get open challenges
    open_challenges = await db.execute(
        "SELECT id, challenger_id, game_type, bet_amount FROM challenges WHERE status = 'open' AND challenger_id != %s LIMIT 5",
        (user_id,)
    )
    
    challenge_text = "**⚔️ CHALLENGE CENTER ⚔️**\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    if pending_challenges:
        challenge_text += "📥 **Pending Challenges:**\n"
        for challenge in pending_challenges:
            challenge_text += f"• {challenge[1].upper()} - {challenge[2]:.2f}€\n"
    
    if open_challenges:
        challenge_text += "\n🎯 **Open Challenges:**\n"
        for challenge in open_challenges:
            challenge_text += f"• {challenge[2].upper()} - {challenge[3]:.2f}€\n"
    
    if not pending_challenges and not open_challenges:
        challenge_text += "No active challenges available.\nCreate your own or wait for others!"
    
    keyboard = [
        [InlineKeyboardButton("🎯 Create Challenge", callback_data="play_games")],
        [InlineKeyboardButton("🔍 Join Open Challenge", callback_data="join_open_challenge")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="back_main")]
    ]
    
    await update.callback_query.edit_message_text(
        challenge_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def handle_withdrawal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle withdrawal request"""
    user = update.effective_user
    user_data = await db.execute_one("SELECT id, balance FROM users WHERE telegram_id=%s", (user.id,))
    
    if not user_data:
        await update.callback_query.edit_message_text("❌ User not found!")
        return
        
    user_id, balance = user_data
    
    if balance < 0.01:
        await update.callback_query.edit_message_text(
            "❌ Insufficient balance for withdrawal. Minimum: 0.01€"
        )
        return
    
    withdrawal_message = f"""
**📤 WITHDRAWAL REQUEST 📤**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💰 Available Balance: **{balance:.2f}€**
💸 Network Fee: **0.001 BTC/ETH**

⚠️ **Instructions:**
1. Enter withdrawal amount
2. Provide your crypto address
3. Confirm transaction

Please enter withdrawal amount (minimum 0.01€):
    """
    
    await update.callback_query.edit_message_text(
        withdrawal_message,
        parse_mode='Markdown'
    )
    
    # Set user session for withdrawal
    user_sessions[user.id] = {"waiting_for_withdrawal": True}

async def handle_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user settings"""
    user = update.effective_user
    user_data = await db.execute_one("SELECT username, created_at FROM users WHERE telegram_id=%s", (user.id,))
    
    if not user_data:
        await update.callback_query.edit_message_text("❌ User not found!")
        return
        
    username, created_at = user_data
    
    settings_message = f"""
**⚙️ ACCOUNT SETTINGS ⚙️**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👤 **Profile Information:**
• Username: **{username}**
• Member since: **{created_at.strftime('%Y-%m-%d') if created_at else 'Unknown'}**
• Telegram ID: **{user.id}**

🔧 **Available Options:**
• Change notification settings
• Update security preferences
• View account activity
• Export game data

🚧 More settings coming soon...
    """
    
    keyboard = [
        [InlineKeyboardButton("🔔 Notifications", callback_data="settings_notifications")],
        [InlineKeyboardButton("🔒 Security", callback_data="settings_security")],
        [InlineKeyboardButton("📊 Export Data", callback_data="export_data")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="back_main")]
    ]
    
    await update.callback_query.edit_message_text(
        settings_message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def create_open_challenge(user_id: int, game_type: str, bet_amount: float) -> int:
    """Create an open challenge"""
    result = await db.execute(
        "INSERT INTO challenges (challenger_id, challengee_id, game_type, bet_amount, status) VALUES (%s, %s, %s, %s, %s)",
        (user_id, 0, game_type, bet_amount, "open")  # challengee_id = 0 means open challenge
    )
    
    # Get the challenge ID
    challenge = await db.execute_one("SELECT LAST_INSERT_ID()")
    return challenge[0]

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages"""
    user_id = update.effective_user.id
    text = update.message.text
    
    if user_id in user_sessions and user_sessions[user_id].get("waiting_for_bet"):
        try:
            bet_amount = float(text)
            if 0.10 <= bet_amount <= 900.00:
                # Process custom bet
                game_type = user_sessions[user_id].get("selected_game", "snake")
                
                # Get user data
                user_data = await db.execute_one("SELECT id, balance FROM users WHERE telegram_id=%s", (user_id,))
                if user_data:
                    db_user_id, balance = user_data
                    
                    if balance >= bet_amount:
                        challenge_id = await create_open_challenge(db_user_id, game_type, bet_amount)
                        
                        await update.message.reply_text(
                            f"✅ Challenge created!\n🎮 Game: {game_type.upper()}\n💰 Bet: {bet_amount:.2f}€\n🆔 ID: {challenge_id}",
                            parse_mode='Markdown'
                        )
                    else:
                        await update.message.reply_text(f"❌ Insufficient balance! You have {balance:.2f}€")
                else:
                    await update.message.reply_text("❌ User not found!")
            else:
                await update.message.reply_text("❌ Bet amount must be between 0.10€ and 900€")
        except ValueError:
            await update.message.reply_text("❌ Please enter a valid number")
        
        # Clear session
        user_sessions[user_id]["waiting_for_bet"] = False

async def main():
    """Main function to start the bot"""
    await db.connect()
    
    # Create all tables
    await create_user_table()
    await create_friends_table()
    await create_challenges_table()
    await create_transactions_table()
    await create_game_sessions_table()

    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    logger.info("🚀 Neon Betting Arena Bot started!")
    await application.run_polling()

if __name__ == '__main__':
    asyncio.run(main())
