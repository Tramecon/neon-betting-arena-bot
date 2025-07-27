import asyncio
import logging
import hashlib
import hmac
import time
import json
from decimal import Decimal
from typing import Optional, Dict, Any
from db import db
from config import BINANCE_API_KEY

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PaymentProcessor:
    def __init__(self):
        self.house_fee_percentage = Decimal('0.10')  # 10% house fee
        self.min_bet = Decimal('0.10')
        self.max_bet = Decimal('900.00')
        
    def calculate_house_fee(self, amount: Decimal) -> Decimal:
        """Calculate 10% house fee"""
        return amount * self.house_fee_percentage
        
    def validate_bet_amount(self, amount: Decimal) -> bool:
        """Validate bet amount is within allowed range"""
        return self.min_bet <= amount <= self.max_bet
        
    async def get_user_balance(self, user_id: int) -> Decimal:
        """Get user's current balance"""
        try:
            result = await db.execute_one(
                "SELECT balance FROM users WHERE id = %s",
                (user_id,)
            )
            return Decimal(str(result[0])) if result else Decimal('0')
        except Exception as e:
            logger.error(f"Error getting user balance: {e}")
            return Decimal('0')
            
    async def update_user_balance(self, user_id: int, new_balance: Decimal) -> bool:
        """Update user's balance"""
        try:
            await db.execute(
                "UPDATE users SET balance = %s WHERE id = %s",
                (float(new_balance), user_id)
            )
            return True
        except Exception as e:
            logger.error(f"Error updating user balance: {e}")
            return False
            
    async def record_transaction(self, user_id: int, transaction_type: str, 
                               amount: Decimal, fee: Decimal = Decimal('0'), 
                               reference_id: Optional[int] = None) -> bool:
        """Record transaction in database"""
        try:
            await db.execute(
                "INSERT INTO transactions (user_id, transaction_type, amount, fee, reference_id) VALUES (%s, %s, %s, %s, %s)",
                (user_id, transaction_type, float(amount), float(fee), reference_id)
            )
            return True
        except Exception as e:
            logger.error(f"Error recording transaction: {e}")
            return False
            
    async def process_deposit(self, user_id: int, amount: Decimal, 
                            crypto_address: str, tx_hash: str) -> Dict[str, Any]:
        """Process cryptocurrency deposit"""
        try:
            # In a real implementation, you would verify the transaction on the blockchain
            # For now, we'll simulate the deposit process
            
            if amount <= 0:
                return {"success": False, "error": "Invalid deposit amount"}
                
            # Get current balance
            current_balance = await self.get_user_balance(user_id)
            new_balance = current_balance + amount
            
            # Update balance
            if not await self.update_user_balance(user_id, new_balance):
                return {"success": False, "error": "Failed to update balance"}
                
            # Record transaction
            if not await self.record_transaction(user_id, "deposit", amount):
                return {"success": False, "error": "Failed to record transaction"}
                
            logger.info(f"Deposit processed: User {user_id}, Amount {amount}")
            
            return {
                "success": True,
                "amount": float(amount),
                "new_balance": float(new_balance),
                "tx_hash": tx_hash
            }
            
        except Exception as e:
            logger.error(f"Error processing deposit: {e}")
            return {"success": False, "error": "Internal server error"}
            
    async def process_withdrawal(self, user_id: int, amount: Decimal, 
                               crypto_address: str) -> Dict[str, Any]:
        """Process cryptocurrency withdrawal"""
        try:
            if amount <= 0:
                return {"success": False, "error": "Invalid withdrawal amount"}
                
            # Get current balance
            current_balance = await self.get_user_balance(user_id)
            
            if current_balance < amount:
                return {"success": False, "error": "Insufficient balance"}
                
            # Calculate withdrawal fee (small network fee)
            withdrawal_fee = Decimal('0.001')  # Small network fee
            total_deduction = amount + withdrawal_fee
            
            if current_balance < total_deduction:
                return {"success": False, "error": "Insufficient balance for withdrawal fee"}
                
            new_balance = current_balance - total_deduction
            
            # Update balance
            if not await self.update_user_balance(user_id, new_balance):
                return {"success": False, "error": "Failed to update balance"}
                
            # Record transaction
            if not await self.record_transaction(user_id, "withdrawal", amount, withdrawal_fee):
                return {"success": False, "error": "Failed to record transaction"}
                
            # In a real implementation, you would initiate the blockchain transaction here
            fake_tx_hash = hashlib.sha256(f"{user_id}{amount}{time.time()}".encode()).hexdigest()
            
            logger.info(f"Withdrawal processed: User {user_id}, Amount {amount}")
            
            return {
                "success": True,
                "amount": float(amount),
                "fee": float(withdrawal_fee),
                "new_balance": float(new_balance),
                "tx_hash": fake_tx_hash,
                "address": crypto_address
            }
            
        except Exception as e:
            logger.error(f"Error processing withdrawal: {e}")
            return {"success": False, "error": "Internal server error"}
            
    async def process_bet(self, user_id: int, amount: Decimal, 
                         challenge_id: int) -> Dict[str, Any]:
        """Process bet placement"""
        try:
            if not self.validate_bet_amount(amount):
                return {
                    "success": False, 
                    "error": f"Bet amount must be between {self.min_bet}€ and {self.max_bet}€"
                }
                
            # Get current balance
            current_balance = await self.get_user_balance(user_id)
            
            if current_balance < amount:
                return {"success": False, "error": "Insufficient balance"}
                
            new_balance = current_balance - amount
            
            # Update balance
            if not await self.update_user_balance(user_id, new_balance):
                return {"success": False, "error": "Failed to update balance"}
                
            # Record transaction
            if not await self.record_transaction(user_id, "bet", amount, reference_id=challenge_id):
                return {"success": False, "error": "Failed to record transaction"}
                
            logger.info(f"Bet placed: User {user_id}, Amount {amount}, Challenge {challenge_id}")
            
            return {
                "success": True,
                "amount": float(amount),
                "new_balance": float(new_balance),
                "challenge_id": challenge_id
            }
            
        except Exception as e:
            logger.error(f"Error processing bet: {e}")
            return {"success": False, "error": "Internal server error"}
            
    async def process_payout(self, winner_id: int, loser_id: int, 
                           bet_amount: Decimal, challenge_id: int) -> Dict[str, Any]:
        """Process game payout with house fee"""
        try:
            # Calculate house fee and winner payout
            house_fee = self.calculate_house_fee(bet_amount * 2)  # Fee on total pot
            winner_payout = (bet_amount * 2) - house_fee
            
            # Get winner's current balance
            winner_balance = await self.get_user_balance(winner_id)
            new_winner_balance = winner_balance + winner_payout
            
            # Update winner's balance
            if not await self.update_user_balance(winner_id, new_winner_balance):
                return {"success": False, "error": "Failed to update winner balance"}
                
            # Record winner payout transaction
            if not await self.record_transaction(winner_id, "payout", winner_payout, 
                                               reference_id=challenge_id):
                return {"success": False, "error": "Failed to record winner transaction"}
                
            # Record house fee transaction (system account)
            if not await self.record_transaction(1, "house_fee", house_fee, 
                                               reference_id=challenge_id):
                logger.warning(f"Failed to record house fee for challenge {challenge_id}")
                
            logger.info(f"Payout processed: Winner {winner_id}, Amount {winner_payout}, Fee {house_fee}")
            
            return {
                "success": True,
                "winner_id": winner_id,
                "winner_payout": float(winner_payout),
                "house_fee": float(house_fee),
                "new_winner_balance": float(new_winner_balance)
            }
            
        except Exception as e:
            logger.error(f"Error processing payout: {e}")
            return {"success": False, "error": "Internal server error"}
            
    async def get_deposit_address(self, user_id: int, currency: str = "BTC") -> Dict[str, Any]:
        """Generate deposit address for user"""
        try:
            # In a real implementation, you would generate a unique address for each user
            # For now, we'll create a fake address based on user ID
            
            if currency.upper() == "BTC":
                # Generate a fake Bitcoin address
                address_data = f"{user_id}{currency}{time.time()}"
                address_hash = hashlib.sha256(address_data.encode()).hexdigest()[:34]
                address = f"1{address_hash}"
            elif currency.upper() == "ETH":
                # Generate a fake Ethereum address
                address_data = f"{user_id}{currency}{time.time()}"
                address_hash = hashlib.sha256(address_data.encode()).hexdigest()[:40]
                address = f"0x{address_hash}"
            else:
                return {"success": False, "error": "Unsupported currency"}
                
            # Store address in user record
            await db.execute(
                "UPDATE users SET wallet_address = %s WHERE id = %s",
                (address, user_id)
            )
            
            return {
                "success": True,
                "address": address,
                "currency": currency.upper(),
                "qr_code": f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={address}"
            }
            
        except Exception as e:
            logger.error(f"Error generating deposit address: {e}")
            return {"success": False, "error": "Internal server error"}
            
    async def get_transaction_history(self, user_id: int, limit: int = 50) -> Dict[str, Any]:
        """Get user's transaction history"""
        try:
            transactions = await db.execute(
                "SELECT transaction_type, amount, fee, created_at FROM transactions WHERE user_id = %s ORDER BY created_at DESC LIMIT %s",
                (user_id, limit)
            )
            
            transaction_list = []
            for tx in transactions:
                transaction_list.append({
                    "type": tx[0],
                    "amount": float(tx[1]),
                    "fee": float(tx[2]),
                    "date": tx[3].isoformat() if tx[3] else None
                })
                
            return {
                "success": True,
                "transactions": transaction_list
            }
            
        except Exception as e:
            logger.error(f"Error getting transaction history: {e}")
            return {"success": False, "error": "Internal server error"}

# Global payment processor instance
payment_processor = PaymentProcessor()

# Convenience functions
async def process_deposit(user_id: int, amount: float, crypto_address: str, tx_hash: str):
    return await payment_processor.process_deposit(user_id, Decimal(str(amount)), crypto_address, tx_hash)

async def process_withdrawal(user_id: int, amount: float, crypto_address: str):
    return await payment_processor.process_withdrawal(user_id, Decimal(str(amount)), crypto_address)

async def process_bet(user_id: int, amount: float, challenge_id: int):
    return await payment_processor.process_bet(user_id, Decimal(str(amount)), challenge_id)

async def process_payout(winner_id: int, loser_id: int, bet_amount: float, challenge_id: int):
    return await payment_processor.process_payout(winner_id, loser_id, Decimal(str(bet_amount)), challenge_id)

async def get_user_balance(user_id: int):
    return float(await payment_processor.get_user_balance(user_id))

async def get_deposit_address(user_id: int, currency: str = "BTC"):
    return await payment_processor.get_deposit_address(user_id, currency)

async def get_transaction_history(user_id: int, limit: int = 50):
    return await payment_processor.get_transaction_history(user_id, limit)
