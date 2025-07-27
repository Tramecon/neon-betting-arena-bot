#!/usr/bin/env python3
"""
Simplified WebSocket Server for Neon Betting Arena
Works without database connection for testing
"""

import asyncio
import json
import logging
import uuid
import websockets
from typing import Dict
from games import create_game, GameBase

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleGameServer:
    def __init__(self):
        self.active_games: Dict[str, GameBase] = {}
        self.player_connections: Dict[int, websockets.WebSocketServerProtocol] = {}
        self.connection_to_player: Dict[websockets.WebSocketServerProtocol, int] = {}
        
    async def register_player(self, websocket, player_id: int):
        """Register a player connection"""
        self.player_connections[player_id] = websocket
        self.connection_to_player[websocket] = player_id
        logger.info(f"Player {player_id} connected")
        
    async def unregister_player(self, websocket):
        """Unregister a player connection"""
        if websocket in self.connection_to_player:
            player_id = self.connection_to_player[websocket]
            if player_id in self.player_connections:
                del self.player_connections[player_id]
            del self.connection_to_player[websocket]
            logger.info(f"Player {player_id} disconnected")
            
    async def create_game_session(self, game_type: str, player1_id: int, player2_id: int):
        """Create a new game session"""
        game_id = str(uuid.uuid4())
        
        # Create game instance
        game = create_game(game_type, game_id, player1_id, player2_id)
        self.active_games[game_id] = game
        
        logger.info(f"Created game session {game_id} ({game_type})")
        return game_id
        
    async def handle_message(self, websocket, message_data):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(message_data)
            action = data.get("action")
            
            if action == "join":
                await self.handle_join(websocket, data)
            elif action == "create_game":
                await self.handle_create_game(websocket, data)
            elif action == "move":
                await self.handle_move(websocket, data)
            elif action == "ping":
                await self.handle_ping(websocket, data)
            else:
                await self.send_error(websocket, f"Unknown action: {action}")
                
        except json.JSONDecodeError:
            await self.send_error(websocket, "Invalid JSON message")
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            await self.send_error(websocket, "Internal server error")
            
    async def handle_ping(self, websocket, data):
        """Handle ping messages"""
        await self.send_message(websocket, {
            "type": "pong",
            "timestamp": data.get("timestamp", "")
        })
        
    async def handle_create_game(self, websocket, data):
        """Handle game creation"""
        game_type = data.get("game_type", "snake")
        player1_id = data.get("player1_id", 1)
        player2_id = data.get("player2_id", 2)
        
        try:
            game_id = await self.create_game_session(game_type, player1_id, player2_id)
            
            await self.send_message(websocket, {
                "type": "game_created",
                "data": {
                    "game_id": game_id,
                    "game_type": game_type,
                    "players": [player1_id, player2_id]
                }
            })
            
        except Exception as e:
            await self.send_error(websocket, f"Failed to create game: {e}")
            
    async def handle_join(self, websocket, data):
        """Handle player joining a game"""
        player_id = data.get("player_id")
        game_id = data.get("game_id")
        
        if not player_id or not game_id:
            await self.send_error(websocket, "Missing player_id or game_id")
            return
            
        if game_id not in self.active_games:
            await self.send_error(websocket, "Game not found")
            return
            
        game = self.active_games[game_id]
        
        if player_id not in [game.player1_id, game.player2_id]:
            await self.send_error(websocket, "Player not authorized for this game")
            return
            
        await self.register_player(websocket, player_id)
        
        # Send initial game state
        await self.send_message(websocket, {
            "type": "game_state",
            "data": game.get_state()
        })
        
        # Check if both players are connected
        if (game.player1_id in self.player_connections and 
            game.player2_id in self.player_connections):
            game.status = "active"
            await self.broadcast_to_game(game_id, {
                "type": "game_started",
                "data": game.get_state()
            })
            
    async def handle_move(self, websocket, data):
        """Handle player moves"""
        player_id = self.connection_to_player.get(websocket)
        game_id = data.get("game_id")
        move_data = data.get("move_data")
        
        if not player_id or not game_id or not move_data:
            await self.send_error(websocket, "Missing required data")
            return
            
        if game_id not in self.active_games:
            await self.send_error(websocket, "Game not found")
            return
            
        game = self.active_games[game_id]
        
        if game.status not in ["active", "waiting"]:
            await self.send_error(websocket, "Game is not active")
            return
            
        # Process move based on game type
        try:
            if hasattr(game, 'move_snake') and 'direction' in move_data:
                game.move_snake(player_id, move_data['direction'])
            elif hasattr(game, 'move_paddle') and 'direction' in move_data:
                game.move_paddle(player_id, move_data['direction'])
            elif hasattr(game, 'move_piece') and 'action' in move_data:
                game.move_piece(player_id, move_data['action'])
                
            # Broadcast updated game state
            await self.broadcast_to_game(game_id, {
                "type": "game_state",
                "data": game.get_state()
            })
            
            # Check if game ended
            if game.status == "finished":
                await self.handle_game_end(game_id)
                
        except Exception as e:
            logger.error(f"Error processing move: {e}")
            await self.send_error(websocket, f"Error processing move: {e}")
            
    async def handle_game_end(self, game_id: str):
        """Handle game ending"""
        if game_id not in self.active_games:
            return
            
        game = self.active_games[game_id]
        
        # Broadcast game end
        await self.broadcast_to_game(game_id, {
            "type": "game_ended",
            "data": {
                "winner_id": game.winner_id,
                "final_state": game.get_state()
            }
        })
        
        # Clean up
        del self.active_games[game_id]
        logger.info(f"Game {game_id} ended, winner: {game.winner_id}")
        
    async def broadcast_to_game(self, game_id: str, message):
        """Broadcast message to all players in a game"""
        if game_id not in self.active_games:
            return
            
        game = self.active_games[game_id]
        players = [game.player1_id, game.player2_id]
        
        for player_id in players:
            if player_id in self.player_connections:
                try:
                    await self.send_message(self.player_connections[player_id], message)
                except websockets.exceptions.ConnectionClosed:
                    # Remove disconnected player
                    await self.unregister_player(self.player_connections[player_id])
                except Exception as e:
                    logger.error(f"Error broadcasting to player {player_id}: {e}")
                    
    async def send_message(self, websocket, message):
        """Send message to a specific websocket"""
        try:
            await websocket.send(json.dumps(message))
        except websockets.exceptions.ConnectionClosed:
            logger.warning("Tried to send message to closed connection")
        except Exception as e:
            logger.error(f"Error sending message: {e}")
        
    async def send_error(self, websocket, error_message):
        """Send error message to websocket"""
        await self.send_message(websocket, {
            "type": "error",
            "message": error_message
        })

# Global game server instance
simple_game_server = SimpleGameServer()

async def handle_client(websocket, path):
    """Handle new WebSocket connections"""
    logger.info(f"New connection from {websocket.remote_address}")
    
    try:
        # Send welcome message
        await simple_game_server.send_message(websocket, {
            "type": "welcome",
            "message": "Connected to Neon Betting Arena WebSocket Server",
            "server_info": {
                "active_games": len(simple_game_server.active_games),
                "connected_players": len(simple_game_server.player_connections)
            }
        })
        
        async for message in websocket:
            await simple_game_server.handle_message(websocket, message)
            
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"Connection closed: {websocket.remote_address}")
    except Exception as e:
        logger.error(f"Error handling client: {e}")
    finally:
        await simple_game_server.unregister_player(websocket)

async def start_game_update_loop():
    """Start the game update loop for continuous games like Pong"""
    while True:
        try:
            for game_id, game in list(simple_game_server.active_games.items()):
                if game.status == "active" and hasattr(game, 'update_ball'):
                    game.update_ball()
                    
                    await simple_game_server.broadcast_to_game(game_id, {
                        "type": "game_state",
                        "data": game.get_state()
                    })
                    
                    if game.status == "finished":
                        await simple_game_server.handle_game_end(game_id)
                        
            await asyncio.sleep(1/30)  # 30 FPS for smooth gameplay
            
        except Exception as e:
            logger.error(f"Error in game update loop: {e}")
            await asyncio.sleep(1)

async def main():
    """Start the WebSocket server"""
    try:
        logger.info("Starting Simple WebSocket Server for Neon Betting Arena...")
        
        # Start the game update loop
        asyncio.create_task(start_game_update_loop())
        
        # Start WebSocket server
        server = await websockets.serve(handle_client, "localhost", 8765)
        logger.info("✅ WebSocket server started on ws://localhost:8765")
        logger.info("🎮 Ready to accept game connections!")
        
        # Keep the server running
        await server.wait_closed()
        
    except Exception as e:
        logger.error(f"Failed to start WebSocket server: {e}")
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 WebSocket server stopped by user")
    except Exception as e:
        logger.error(f"💥 WebSocket server crashed: {e}")
        exit(1)
