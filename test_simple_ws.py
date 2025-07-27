#!/usr/bin/env python3
"""
Quick test for the simple WebSocket server
"""

import asyncio
import json
import websockets
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_websocket_connection():
    """Test basic WebSocket connection and game creation"""
    uri = "ws://localhost:8765"
    
    try:
        async with websockets.connect(uri) as websocket:
            logger.info("✅ Connected to WebSocket server")
            
            # Wait for welcome message
            welcome = await websocket.recv()
            welcome_data = json.loads(welcome)
            logger.info(f"📨 Received: {welcome_data['type']}")
            
            # Test ping
            ping_msg = {
                "action": "ping",
                "timestamp": "test-123"
            }
            await websocket.send(json.dumps(ping_msg))
            logger.info("📤 Sent ping")
            
            pong = await websocket.recv()
            pong_data = json.loads(pong)
            logger.info(f"📨 Received pong: {pong_data['type']}")
            
            # Test game creation
            create_game_msg = {
                "action": "create_game",
                "game_type": "snake",
                "player1_id": 123,
                "player2_id": 456
            }
            await websocket.send(json.dumps(create_game_msg))
            logger.info("📤 Sent create_game")
            
            game_created = await websocket.recv()
            game_data = json.loads(game_created)
            logger.info(f"📨 Game created: {game_data}")
            
            if game_data['type'] == 'game_created':
                game_id = game_data['data']['game_id']
                logger.info(f"🎮 Game ID: {game_id}")
                
                # Test joining the game
                join_msg = {
                    "action": "join",
                    "player_id": 123,
                    "game_id": game_id
                }
                await websocket.send(json.dumps(join_msg))
                logger.info("📤 Sent join game")
                
                join_response = await websocket.recv()
                join_data = json.loads(join_response)
                logger.info(f"📨 Join response: {join_data['type']}")
                
                # Test a move
                move_msg = {
                    "action": "move",
                    "game_id": game_id,
                    "move_data": {
                        "direction": "UP"
                    }
                }
                await websocket.send(json.dumps(move_msg))
                logger.info("📤 Sent move")
                
                move_response = await websocket.recv()
                move_data = json.loads(move_response)
                logger.info(f"📨 Move response: {move_data['type']}")
                
            logger.info("✅ All tests completed successfully!")
            
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False
        
    return True

async def main():
    """Main test function"""
    print("🧪 Testing Simple WebSocket Server")
    print("=" * 50)
    print("Make sure to start the server first:")
    print("python ws_server_simple.py")
    print()
    
    # Wait a moment for server to be ready
    await asyncio.sleep(1)
    
    success = await test_websocket_connection()
    
    if success:
        print("\n🎉 WebSocket server test passed!")
    else:
        print("\n❌ WebSocket server test failed!")
        
    return success

if __name__ == "__main__":
    asyncio.run(main())
