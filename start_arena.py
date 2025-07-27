#!/usr/bin/env python3
"""
Neon Betting Arena Launcher
Starts both the Telegram bot and WebSocket server
"""

import asyncio
import subprocess
import sys
import time
import signal
import os
from pathlib import Path

class ArenaLauncher:
    def __init__(self):
        self.bot_process = None
        self.ws_process = None
        self.running = True
        
    def print_banner(self):
        """Print startup banner"""
        banner = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║    🎮 NEON BETTING ARENA 🎮                                  ║
║                                                              ║
║    ✨ Telegram Gaming Bot with Crypto Betting ✨            ║
║                                                              ║
║    🐍 Snake  •  🏓 Ping Pong  •  🧩 Tetris                  ║
║    💰 0.10€ - 900€ Betting Range                            ║
║    🔗 Real-time WebSocket Gaming                            ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
        """
        print(banner)
        
    def check_dependencies(self):
        """Check if all required files exist"""
        required_files = [
            'bot.py',
            'ws_server.py',
            'db.py',
            'games.py',
            'payments.py',
            'config.py',
            'requirements.txt'
        ]
        
        missing_files = []
        for file in required_files:
            if not Path(file).exists():
                missing_files.append(file)
                
        if missing_files:
            print("❌ Missing required files:")
            for file in missing_files:
                print(f"   • {file}")
            return False
            
        print("✅ All required files found")
        return True
        
    def check_config(self):
        """Check if configuration is properly set"""
        try:
            from config import TELEGRAM_BOT_TOKEN, DB_HOST, DB_USER, DB_PASSWORD, DB_NAME
            
            if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "your_bot_token_here":
                print("❌ Telegram bot token not configured in config.py")
                return False
                
            if not all([DB_HOST, DB_USER, DB_PASSWORD, DB_NAME]):
                print("❌ Database configuration incomplete in config.py")
                return False
                
            print("✅ Configuration looks good")
            return True
            
        except ImportError as e:
            print(f"❌ Configuration error: {e}")
            return False
            
    def start_bot(self):
        """Start the Telegram bot"""
        print("🤖 Starting Telegram bot...")
        try:
            self.bot_process = subprocess.Popen(
                [sys.executable, 'bot.py'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            print("✅ Telegram bot started successfully")
            return True
        except Exception as e:
            print(f"❌ Failed to start Telegram bot: {e}")
            return False
            
    def start_websocket_server(self):
        """Start the WebSocket server"""
        print("🔌 Starting WebSocket server...")
        try:
            # Try simple server first, fallback to full server
            ws_file = 'ws_server_simple.py' if Path('ws_server_simple.py').exists() else 'ws_server.py'
            self.ws_process = subprocess.Popen(
                [sys.executable, ws_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            print(f"✅ WebSocket server started successfully ({ws_file})")
            return True
        except Exception as e:
            print(f"❌ Failed to start WebSocket server: {e}")
            return False
            
    def monitor_processes(self):
        """Monitor running processes"""
        print("\n📊 Monitoring services...")
        print("Press Ctrl+C to stop all services")
        print("-" * 50)
        
        try:
            while self.running:
                # Check bot process
                if self.bot_process:
                    bot_status = "🟢 Running" if self.bot_process.poll() is None else "🔴 Stopped"
                else:
                    bot_status = "🔴 Not Started"
                    
                # Check WebSocket process
                if self.ws_process:
                    ws_status = "🟢 Running" if self.ws_process.poll() is None else "🔴 Stopped"
                else:
                    ws_status = "🔴 Not Started"
                    
                # Print status
                print(f"\r🤖 Bot: {bot_status} | 🔌 WebSocket: {ws_status}", end="", flush=True)
                
                # Check if any process died
                if self.bot_process and self.bot_process.poll() is not None:
                    print(f"\n❌ Telegram bot process died with code {self.bot_process.poll()}")
                    break
                    
                if self.ws_process and self.ws_process.poll() is not None:
                    print(f"\n❌ WebSocket server process died with code {self.ws_process.poll()}")
                    break
                    
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n\n🛑 Shutdown requested by user")
            self.running = False
            
    def stop_services(self):
        """Stop all services"""
        print("\n🔄 Stopping services...")
        
        if self.bot_process:
            print("🤖 Stopping Telegram bot...")
            self.bot_process.terminate()
            try:
                self.bot_process.wait(timeout=5)
                print("✅ Telegram bot stopped")
            except subprocess.TimeoutExpired:
                print("⚠️ Force killing Telegram bot...")
                self.bot_process.kill()
                
        if self.ws_process:
            print("🔌 Stopping WebSocket server...")
            self.ws_process.terminate()
            try:
                self.ws_process.wait(timeout=5)
                print("✅ WebSocket server stopped")
            except subprocess.TimeoutExpired:
                print("⚠️ Force killing WebSocket server...")
                self.ws_process.kill()
                
    def show_logs(self):
        """Show recent logs from both services"""
        print("\n📋 Recent Logs:")
        print("=" * 50)
        
        if self.bot_process:
            print("\n🤖 Bot Logs:")
            try:
                stdout, stderr = self.bot_process.communicate(timeout=1)
                if stdout:
                    print(stdout[-500:])  # Last 500 chars
                if stderr:
                    print("Errors:", stderr[-500:])
            except subprocess.TimeoutExpired:
                pass
                
        if self.ws_process:
            print("\n🔌 WebSocket Logs:")
            try:
                stdout, stderr = self.ws_process.communicate(timeout=1)
                if stdout:
                    print(stdout[-500:])  # Last 500 chars
                if stderr:
                    print("Errors:", stderr[-500:])
            except subprocess.TimeoutExpired:
                pass
                
    def run(self):
        """Main run method"""
        self.print_banner()
        
        print("🔍 Checking system requirements...")
        
        # Check dependencies
        if not self.check_dependencies():
            print("\n❌ Please ensure all required files are present")
            return False
            
        # Check configuration
        if not self.check_config():
            print("\n❌ Please configure config.py properly")
            print("📖 See README.md for setup instructions")
            return False
            
        print("\n🚀 Starting Neon Betting Arena...")
        print("-" * 50)
        
        # Start services
        if not self.start_websocket_server():
            return False
            
        # Wait a moment for WebSocket server to start
        time.sleep(2)
        
        if not self.start_bot():
            self.stop_services()
            return False
            
        print("\n🎉 All services started successfully!")
        print("\n📱 Your bot is now ready to accept users!")
        print("💡 Users can find your bot on Telegram and start playing")
        
        # Monitor processes
        self.monitor_processes()
        
        # Cleanup
        self.stop_services()
        
        print("\n👋 Neon Betting Arena stopped. Thanks for playing!")
        return True

def main():
    """Main entry point"""
    launcher = ArenaLauncher()
    
    # Handle Ctrl+C gracefully
    def signal_handler(sig, frame):
        launcher.running = False
        
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        success = launcher.run()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n💥 Launcher failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
