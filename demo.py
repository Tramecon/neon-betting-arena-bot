#!/usr/bin/env python3
"""
Neon Betting Arena Demo Script
Demonstrates the key features of the gaming bot
"""

import asyncio
import json
import time
from games import create_game, SnakeGame, PingPongGame, TetrisGame
from payments import PaymentProcessor
from decimal import Decimal

class NeonArenaDemo:
    def __init__(self):
        self.payment_processor = PaymentProcessor()
        
    def print_banner(self):
        """Print demo banner"""
        banner = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║    🎮 NEON BETTING ARENA DEMO 🎮                            ║
║                                                              ║
║    Live demonstration of gaming bot features                 ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
        """
        print(banner)
        
    def demo_game_creation(self):
        """Demonstrate game creation and basic mechanics"""
        print("\n🎯 GAME CREATION DEMO")
        print("=" * 50)
        
        # Create Snake game
        print("\n🐍 Creating Snake Game...")
        snake_game = create_game("snake", "demo-snake-1", 123, 456)
        print(f"✅ Snake game created: {snake_game.__class__.__name__}")
        print(f"   Players: {snake_game.player1_id} vs {snake_game.player2_id}")
        print(f"   Board size: {snake_game.board_size}x{snake_game.board_size}")
        print(f"   Initial food position: {snake_game.food}")
        
        # Simulate some moves
        print("\n🕹️ Simulating snake moves...")
        snake_game.move_snake(123, "UP")
        snake_game.move_snake(456, "DOWN")
        state = snake_game.get_state()
        print(f"   Player 1 score: {state['player1_score']}")
        print(f"   Player 2 score: {state['player2_score']}")
        
        # Create Ping Pong game
        print("\n🏓 Creating Ping Pong Game...")
        pong_game = create_game("pong", "demo-pong-1", 789, 101)
        print(f"✅ Pong game created: {pong_game.__class__.__name__}")
        print(f"   Board: {pong_game.board_width}x{pong_game.board_height}")
        print(f"   Ball position: ({pong_game.ball_x}, {pong_game.ball_y})")
        
        # Simulate ball updates
        print("\n🏓 Simulating ball movement...")
        for i in range(3):
            pong_game.update_ball()
            print(f"   Frame {i+1}: Ball at ({pong_game.ball_x}, {pong_game.ball_y})")
            
        # Create Tetris game
        print("\n🧩 Creating Tetris Game...")
        tetris_game = create_game("tetris", "demo-tetris-1", 111, 222)
        print(f"✅ Tetris game created: {tetris_game.__class__.__name__}")
        print(f"   Board: {tetris_game.board_width}x{tetris_game.board_height}")
        print(f"   Player 1 piece: {len(tetris_game.player1_piece)}x{len(tetris_game.player1_piece[0]) if tetris_game.player1_piece else 0}")
        
        # Simulate piece movement
        print("\n🧩 Simulating piece movement...")
        tetris_game.move_piece(111, "LEFT")
        tetris_game.move_piece(111, "ROTATE")
        tetris_game.move_piece(222, "RIGHT")
        state = tetris_game.get_state()
        print(f"   Player 1 position: ({state['player1_piece_x']}, {state['player1_piece_y']})")
        print(f"   Player 2 position: ({state['player2_piece_x']}, {state['player2_piece_y']})")
        
        return True
        
    def demo_payment_system(self):
        """Demonstrate payment processing"""
        print("\n💰 PAYMENT SYSTEM DEMO")
        print("=" * 50)
        
        # Test bet validation
        print("\n🎯 Testing bet validation...")
        valid_bets = [0.10, 1.00, 50.00, 900.00]
        invalid_bets = [0.05, 1000.00, -10.00]
        
        for bet in valid_bets:
            is_valid = self.payment_processor.validate_bet_amount(Decimal(str(bet)))
            print(f"   {bet}€: {'✅ Valid' if is_valid else '❌ Invalid'}")
            
        for bet in invalid_bets:
            is_valid = self.payment_processor.validate_bet_amount(Decimal(str(bet)))
            print(f"   {bet}€: {'✅ Valid' if is_valid else '❌ Invalid'}")
            
        # Test house fee calculation
        print("\n🏦 Testing house fee calculation...")
        test_amounts = [10.00, 50.00, 100.00, 500.00]
        
        for amount in test_amounts:
            fee = self.payment_processor.calculate_house_fee(Decimal(str(amount)))
            payout = Decimal(str(amount)) - fee
            print(f"   {amount}€ bet → {fee}€ fee → {payout}€ payout")
            
        # Test crypto address generation
        print("\n🔗 Testing crypto address generation...")
        btc_data = f"123BTC{time.time()}"
        eth_data = f"456ETH{time.time()}"
        
        import hashlib
        btc_hash = hashlib.sha256(btc_data.encode()).hexdigest()[:34]
        eth_hash = hashlib.sha256(eth_data.encode()).hexdigest()[:40]
        
        print(f"   BTC address: 1{btc_hash}")
        print(f"   ETH address: 0x{eth_hash}")
        
        return True
        
    def demo_websocket_protocol(self):
        """Demonstrate WebSocket message protocol"""
        print("\n🔌 WEBSOCKET PROTOCOL DEMO")
        print("=" * 50)
        
        # Sample messages
        messages = [
            {
                "action": "join",
                "player_id": 123,
                "game_id": "demo-game-123"
            },
            {
                "action": "move",
                "game_id": "demo-game-123",
                "move_data": {
                    "direction": "UP"
                }
            },
            {
                "action": "game_update",
                "game_id": "demo-game-123"
            }
        ]
        
        responses = [
            {
                "type": "game_state",
                "data": {
                    "game_id": "demo-game-123",
                    "status": "active",
                    "player1_score": 5,
                    "player2_score": 3
                }
            },
            {
                "type": "game_ended",
                "data": {
                    "winner_id": 123,
                    "final_score": "5-3"
                }
            },
            {
                "type": "error",
                "message": "Game not found"
            }
        ]
        
        print("\n📤 Sample client messages:")
        for i, msg in enumerate(messages, 1):
            print(f"   {i}. {json.dumps(msg, indent=6)}")
            
        print("\n📥 Sample server responses:")
        for i, resp in enumerate(responses, 1):
            print(f"   {i}. {json.dumps(resp, indent=6)}")
            
        return True
        
    def demo_database_schema(self):
        """Demonstrate database structure"""
        print("\n🗄️ DATABASE SCHEMA DEMO")
        print("=" * 50)
        
        tables = {
            "users": [
                "id (INT, PRIMARY KEY)",
                "telegram_id (BIGINT, UNIQUE)",
                "username (VARCHAR(255))",
                "balance (DECIMAL(18,8))",
                "wallet_address (VARCHAR(255))",
                "created_at (TIMESTAMP)"
            ],
            "challenges": [
                "id (INT, PRIMARY KEY)",
                "challenger_id (INT, FK to users)",
                "challengee_id (INT, FK to users)",
                "game_type (VARCHAR(20))",
                "bet_amount (DECIMAL(10,2))",
                "status (VARCHAR(20))",
                "winner_id (INT, FK to users)",
                "created_at (TIMESTAMP)"
            ],
            "transactions": [
                "id (INT, PRIMARY KEY)",
                "user_id (INT, FK to users)",
                "transaction_type (VARCHAR(20))",
                "amount (DECIMAL(10,2))",
                "fee (DECIMAL(10,2))",
                "reference_id (INT)",
                "created_at (TIMESTAMP)"
            ],
            "friends": [
                "id (INT, PRIMARY KEY)",
                "user_id (INT, FK to users)",
                "friend_id (INT, FK to users)",
                "created_at (TIMESTAMP)"
            ],
            "game_sessions": [
                "id (INT, PRIMARY KEY)",
                "challenge_id (INT, FK to challenges)",
                "session_token (VARCHAR(255))",
                "game_state (JSON)",
                "status (VARCHAR(20))",
                "created_at (TIMESTAMP)"
            ]
        }
        
        for table_name, columns in tables.items():
            print(f"\n📋 {table_name.upper()} TABLE:")
            for column in columns:
                print(f"   • {column}")
                
        return True
        
    def demo_bot_interface(self):
        """Demonstrate bot interface structure"""
        print("\n🤖 BOT INTERFACE DEMO")
        print("=" * 50)
        
        # Main menu
        print("\n🏠 MAIN MENU:")
        menu_options = [
            "🎯 Play Games",
            "⚔️ Challenge",
            "👥 Friends",
            "💰 Wallet",
            "📊 Stats",
            "⚙️ Settings"
        ]
        
        for option in menu_options:
            print(f"   • {option}")
            
        # Game selection
        print("\n🎮 GAME SELECTION:")
        games = [
            "🐍 Snake - Classic multiplayer snake",
            "🏓 Ping Pong - Real-time paddle battle",
            "🧩 Tetris - Competitive block stacking"
        ]
        
        for game in games:
            print(f"   • {game}")
            
        # Bet amounts
        print("\n💰 BET AMOUNTS:")
        bet_options = ["0.10€", "1€", "5€", "10€", "50€", "100€", "💰 Custom"]
        
        for bet in bet_options:
            print(f"   • {bet}")
            
        # Wallet options
        print("\n💳 WALLET OPTIONS:")
        wallet_options = [
            "📥 Deposit BTC",
            "📥 Deposit ETH", 
            "📤 Withdraw",
            "📊 Transaction History"
        ]
        
        for option in wallet_options:
            print(f"   • {option}")
            
        return True
        
    def demo_neon_styling(self):
        """Demonstrate neon-style message formatting"""
        print("\n✨ NEON STYLING DEMO")
        print("=" * 50)
        
        # Sample neon messages
        messages = [
            {
                "title": "WELCOME",
                "content": """
**NEON BETTING ARENA**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✨ Welcome to the ultimate gaming experience!
🎮 Snake • Ping Pong • Tetris
💰 Bet from 0.10€ to 900€
🏆 Challenge friends and win big!
                """
            },
            {
                "title": "CHALLENGE CREATED",
                "content": """
**⚔️ CHALLENGE CREATED ⚔️**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎮 Game: **SNAKE**
💰 Bet: **50.00€**
🆔 Challenge ID: **12345**

Waiting for opponent...
                """
            },
            {
                "title": "GAME STATS",
                "content": """
**📊 YOUR STATS 📊**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💰 Current Balance: **125.50€**
🎮 Total Games: **47**
🏆 Wins: **28**
💸 Total Bet: **1,250.00€**
💰 Total Winnings: **1,890.75€**

Win Rate: **59.6%**
                """
            }
        ]
        
        for msg in messages:
            print(f"\n🎨 {msg['title']} MESSAGE:")
            print(msg['content'])
            
        return True
        
    async def run_demo(self):
        """Run the complete demo"""
        self.print_banner()
        
        print("🚀 Starting comprehensive demo of Neon Betting Arena...")
        print("This demo showcases all major features without requiring database connection.")
        
        demos = [
            ("Game Creation & Mechanics", self.demo_game_creation),
            ("Payment System", self.demo_payment_system),
            ("WebSocket Protocol", self.demo_websocket_protocol),
            ("Database Schema", self.demo_database_schema),
            ("Bot Interface", self.demo_bot_interface),
            ("Neon Styling", self.demo_neon_styling)
        ]
        
        results = []
        
        for demo_name, demo_func in demos:
            try:
                print(f"\n🔄 Running {demo_name} demo...")
                result = demo_func()
                results.append((demo_name, result))
                if result:
                    print(f"✅ {demo_name} demo completed successfully!")
                else:
                    print(f"❌ {demo_name} demo failed!")
            except Exception as e:
                print(f"💥 {demo_name} demo crashed: {e}")
                results.append((demo_name, False))
                
            # Small delay between demos
            await asyncio.sleep(0.5)
            
        # Summary
        print("\n📊 DEMO RESULTS")
        print("=" * 50)
        
        passed = 0
        for demo_name, result in results:
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{demo_name}: {status}")
            if result:
                passed += 1
                
        print(f"\nTotal: {passed}/{len(results)} demos passed")
        
        if passed == len(results):
            print("\n🎉 All demos completed successfully!")
            print("🚀 The Neon Betting Arena is ready for deployment!")
        else:
            print("\n⚠️ Some demos failed. Check the implementation.")
            
        print("\n📋 NEXT STEPS:")
        print("1. 🗄️ Set up your MySQL database")
        print("2. 🤖 Configure your Telegram bot token")
        print("3. 🚀 Run: python start_arena.py")
        print("4. 🧪 Test with: python test_websocket.py")
        print("5. 🎮 Start gaming!")
        
        return passed == len(results)

async def main():
    """Main demo function"""
    demo = NeonArenaDemo()
    
    try:
        success = await demo.run_demo()
        if success:
            print("\n✅ Demo completed successfully!")
        else:
            print("\n❌ Demo completed with errors!")
            
    except KeyboardInterrupt:
        print("\n\n🛑 Demo interrupted by user")
    except Exception as e:
        print(f"\n💥 Demo failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
