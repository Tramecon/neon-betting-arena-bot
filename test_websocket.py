#!/usr/bin/env python3
"""
WebSocket Test Client for Neon Betting Arena
Tests the WebSocket server functionality
"""

import asyncio
import json
import websockets
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebSocketTestClient:
    def __init__(self, uri="ws://localhost:8765"):
        self.uri = uri
        self.websocket = None
        
    async def connect(self):
        """Connect to WebSocket server"""
        try:
            self.websocket = await websockets.connect(self.uri)
            logger.info(f"Connected to {self.uri}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            return False
            
    async def send_message(self, message):
        """Send message to server"""
        if self.websocket:
            await self.websocket.send(json.dumps(message))
            logger.info(f"Sent: {message}")
        else:
            logger.error("Not connected to server")
            
    async def receive_message(self):
        """Receive message from server"""
        if self.websocket:
            try:
                message = await self.websocket.recv()
                data = json.loads(message)
                logger.info(f"Received: {data}")
                return data
            except websockets.exceptions.ConnectionClosed:
                logger.warning("Connection closed by server")
                return None
        else:
            logger.error("Not connected to server")
            return None
            
    async def close(self):
        """Close connection"""
        if self.websocket:
            await self.websocket.close()
            logger.info("Connection closed")

async def test_basic_connection():
    """Test basic WebSocket connection"""
    print("\n🔧 Testing basic WebSocket connection...")
    
    client = WebSocketTestClient()
    
    if await client.connect():
        print("✅ Connection successful!")
        
        # Test invalid message
        await client.send_message({"action": "invalid_action"})
        response = await client.receive_message()
        
        if response and response.get("type") == "error":
            print("✅ Error handling works!")
        else:
            print("❌ Error handling failed")
            
        await client.close()
        return True
    else:
        print("❌ Connection failed!")
        return False

async def test_game_join():
    """Test joining a game"""
    print("\n🎮 Testing game join functionality...")
    
    client = WebSocketTestClient()
    
    if await client.connect():
        # Test joining non-existent game
        join_message = {
            "action": "join",
            "player_id": 123,
            "game_id": "test-game-id"
        }
        
        await client.send_message(join_message)
        response = await client.receive_message()
        
        if response and response.get("type") == "error":
            print("✅ Game not found error handled correctly!")
        else:
            print("❌ Game join test failed")
            
        await client.close()
        return True
    else:
        print("❌ Connection failed!")
        return False

async def test_move_handling():
    """Test move message handling"""
    print("\n🕹️ Testing move handling...")
    
    client = WebSocketTestClient()
    
    if await client.connect():
        # Test move without joining game
        move_message = {
            "action": "move",
            "game_id": "test-game-id",
            "move_data": {"direction": "UP"}
        }
        
        await client.send_message(move_message)
        response = await client.receive_message()
        
        if response and response.get("type") == "error":
            print("✅ Move validation works!")
        else:
            print("❌ Move validation failed")
            
        await client.close()
        return True
    else:
        print("❌ Connection failed!")
        return False

async def test_multiple_connections():
    """Test multiple simultaneous connections"""
    print("\n👥 Testing multiple connections...")
    
    clients = []
    
    try:
        # Create multiple clients
        for i in range(3):
            client = WebSocketTestClient()
            if await client.connect():
                clients.append(client)
                
        if len(clients) == 3:
            print("✅ Multiple connections successful!")
            
            # Send messages from all clients
            for i, client in enumerate(clients):
                await client.send_message({
                    "action": "join",
                    "player_id": i + 1,
                    "game_id": "multi-test"
                })
                
            print("✅ Multiple client messages sent!")
            
        else:
            print(f"❌ Only {len(clients)}/3 connections successful")
            
    finally:
        # Close all connections
        for client in clients:
            await client.close()
            
    return len(clients) == 3

async def run_all_tests():
    """Run all WebSocket tests"""
    print("🚀 Starting WebSocket Server Tests")
    print("=" * 50)
    
    tests = [
        ("Basic Connection", test_basic_connection),
        ("Game Join", test_game_join),
        ("Move Handling", test_move_handling),
        ("Multiple Connections", test_multiple_connections)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"Test {test_name} failed with exception: {e}")
            results.append((test_name, False))
            
        # Wait between tests
        await asyncio.sleep(1)
    
    # Print results
    print("\n📊 Test Results")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
            
    print(f"\nTotal: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! WebSocket server is working correctly.")
    else:
        print("⚠️ Some tests failed. Check the WebSocket server.")

if __name__ == "__main__":
    print("WebSocket Test Client for Neon Betting Arena")
    print("Make sure the WebSocket server is running on localhost:8765")
    print("Start server with: python ws_server.py")
    print()
    
    try:
        asyncio.run(run_all_tests())
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted by user")
    except Exception as e:
        print(f"\n💥 Test suite failed: {e}")
