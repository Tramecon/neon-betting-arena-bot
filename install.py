#!/usr/bin/env python3
"""
Neon Betting Arena Installation Script
Automated setup for the Telegram gaming bot
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

class ArenaInstaller:
    def __init__(self):
        self.python_cmd = sys.executable
        self.system = platform.system().lower()
        
    def print_banner(self):
        """Print installation banner"""
        banner = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║    🎮 NEON BETTING ARENA INSTALLER 🎮                       ║
║                                                              ║
║    Automated setup for Telegram Gaming Bot                  ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
        """
        print(banner)
        
    def check_python_version(self):
        """Check if Python version is compatible"""
        version = sys.version_info
        if version.major < 3 or (version.major == 3 and version.minor < 8):
            print("❌ Python 3.8+ is required")
            print(f"   Current version: {version.major}.{version.minor}.{version.micro}")
            return False
        
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} detected")
        return True
        
    def install_dependencies(self):
        """Install Python dependencies"""
        print("\n📦 Installing Python dependencies...")
        
        try:
            # Upgrade pip first
            subprocess.run([
                self.python_cmd, "-m", "pip", "install", "--upgrade", "pip"
            ], check=True, capture_output=True)
            
            # Install requirements
            subprocess.run([
                self.python_cmd, "-m", "pip", "install", "-r", "requirements.txt"
            ], check=True, capture_output=True)
            
            print("✅ Dependencies installed successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install dependencies: {e}")
            return False
            
    def check_mysql(self):
        """Check if MySQL is available"""
        print("\n🗄️ Checking MySQL availability...")
        
        try:
            # Try to import mysql connector
            import aiomysql
            print("✅ MySQL connector available")
            return True
        except ImportError:
            print("❌ MySQL connector not available")
            print("   Please install MySQL and ensure aiomysql is working")
            return False
            
    def setup_config(self):
        """Interactive configuration setup"""
        print("\n⚙️ Setting up configuration...")
        
        config_path = Path("config.py")
        if not config_path.exists():
            print("❌ config.py not found!")
            return False
            
        # Read current config
        with open(config_path, 'r') as f:
            config_content = f.read()
            
        print("\n📝 Please provide the following information:")
        
        # Get Telegram Bot Token
        bot_token = input("🤖 Telegram Bot Token (from @BotFather): ").strip()
        if not bot_token:
            print("❌ Bot token is required!")
            return False
            
        # Get database info
        print("\n🗄️ Database Configuration:")
        db_host = input("   Host (default: localhost): ").strip() or "localhost"
        db_port = input("   Port (default: 3306): ").strip() or "3306"
        db_user = input("   Username: ").strip()
        db_password = input("   Password: ").strip()
        db_name = input("   Database name: ").strip()
        
        if not all([db_user, db_password, db_name]):
            print("❌ All database fields are required!")
            return False
            
        # Optional: Binance API key
        binance_key = input("\n💰 Binance API Key (optional, press Enter to skip): ").strip()
        
        # Update config file
        try:
            # Replace tokens
            config_content = config_content.replace(
                'TELEGRAM_BOT_TOKEN = "8374121440:AAHri_UwBKSTpp_9qQrObT2peBE2xiQgfzs"',
                f'TELEGRAM_BOT_TOKEN = "{bot_token}"'
            )
            
            if binance_key:
                config_content = config_content.replace(
                    'BINANCE_API_KEY = "8t713BmtmUL8eFbwl7LHPftBtHo66Jv2nMS7uexrspkg4I3My5lXexSrhp1FUBsI"',
                    f'BINANCE_API_KEY = "{binance_key}"'
                )
                
            # Replace database config
            config_content = config_content.replace(
                'DB_HOST = "34.45.249.248"',
                f'DB_HOST = "{db_host}"'
            )
            config_content = config_content.replace(
                'DB_PORT = 3306',
                f'DB_PORT = {db_port}'
            )
            config_content = config_content.replace(
                'DB_USER = "mysql-test"',
                f'DB_USER = "{db_user}"'
            )
            config_content = config_content.replace(
                'DB_PASSWORD = "123456@"',
                f'DB_PASSWORD = "{db_password}"'
            )
            config_content = config_content.replace(
                'DB_NAME = "Basededatos1"',
                f'DB_NAME = "{db_name}"'
            )
            
            # Write updated config
            with open(config_path, 'w') as f:
                f.write(config_content)
                
            print("✅ Configuration updated successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to update configuration: {e}")
            return False
            
    def test_database_connection(self):
        """Test database connection"""
        print("\n🔍 Testing database connection...")
        
        try:
            # Import and test database
            from db import db
            import asyncio
            
            async def test_connection():
                try:
                    await db.connect()
                    print("✅ Database connection successful")
                    await db.close()
                    return True
                except Exception as e:
                    print(f"❌ Database connection failed: {e}")
                    return False
                    
            return asyncio.run(test_connection())
            
        except Exception as e:
            print(f"❌ Database test failed: {e}")
            return False
            
    def create_startup_scripts(self):
        """Create convenient startup scripts"""
        print("\n📝 Creating startup scripts...")
        
        try:
            # Create start script for Unix systems
            if self.system in ['linux', 'darwin']:
                start_script = """#!/bin/bash
echo "🎮 Starting Neon Betting Arena..."
python3 start_arena.py
"""
                with open("start.sh", "w") as f:
                    f.write(start_script)
                os.chmod("start.sh", 0o755)
                print("✅ Created start.sh")
                
            # Create start script for Windows
            if self.system == 'windows':
                start_script = """@echo off
echo 🎮 Starting Neon Betting Arena...
python start_arena.py
pause
"""
                with open("start.bat", "w") as f:
                    f.write(start_script)
                print("✅ Created start.bat")
                
            return True
            
        except Exception as e:
            print(f"❌ Failed to create startup scripts: {e}")
            return False
            
    def show_next_steps(self):
        """Show next steps after installation"""
        print("\n🎉 Installation completed successfully!")
        print("\n📋 Next Steps:")
        print("=" * 50)
        
        print("1. 🗄️ Set up your MySQL database:")
        print("   • Create the database you specified")
        print("   • Ensure MySQL server is running")
        print("   • Grant proper permissions to your user")
        
        print("\n2. 🤖 Set up your Telegram bot:")
        print("   • Message @BotFather on Telegram")
        print("   • Use /newbot to create your bot")
        print("   • Copy the token to config.py (already done)")
        
        print("\n3. 🚀 Start the application:")
        if self.system in ['linux', 'darwin']:
            print("   • Run: ./start.sh")
        elif self.system == 'windows':
            print("   • Run: start.bat")
        else:
            print("   • Run: python start_arena.py")
            
        print("\n4. 🧪 Test the installation:")
        print("   • Run: python test_websocket.py")
        print("   • Check that both services start correctly")
        
        print("\n📖 For detailed instructions, see README.md")
        print("\n🎮 Happy gaming!")
        
    def run_installation(self):
        """Run the complete installation process"""
        self.print_banner()
        
        print("🔍 Checking system requirements...")
        
        # Check Python version
        if not self.check_python_version():
            return False
            
        # Install dependencies
        if not self.install_dependencies():
            return False
            
        # Check MySQL
        if not self.check_mysql():
            print("⚠️ MySQL check failed, but continuing...")
            
        # Setup configuration
        if not self.setup_config():
            return False
            
        # Test database connection
        if not self.test_database_connection():
            print("⚠️ Database test failed, but installation continues...")
            print("   Please check your database configuration manually")
            
        # Create startup scripts
        if not self.create_startup_scripts():
            print("⚠️ Failed to create startup scripts, but installation continues...")
            
        # Show next steps
        self.show_next_steps()
        
        return True

def main():
    """Main installation function"""
    installer = ArenaInstaller()
    
    try:
        success = installer.run_installation()
        if success:
            print("\n✅ Installation completed successfully!")
            sys.exit(0)
        else:
            print("\n❌ Installation failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Installation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Installation failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
