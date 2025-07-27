import asyncio
import json
import random
import time
from typing import Dict, List, Tuple, Optional

class GameBase:
    def __init__(self, game_id: str, player1_id: int, player2_id: int):
        self.game_id = game_id
        self.player1_id = player1_id
        self.player2_id = player2_id
        self.status = "waiting"
        self.winner_id = None
        self.created_at = time.time()
        
    def to_dict(self):
        return {
            "game_id": self.game_id,
            "player1_id": self.player1_id,
            "player2_id": self.player2_id,
            "status": self.status,
            "winner_id": self.winner_id,
            "created_at": self.created_at
        }

class SnakeGame(GameBase):
    def __init__(self, game_id: str, player1_id: int, player2_id: int):
        super().__init__(game_id, player1_id, player2_id)
        self.board_size = 20
        self.player1_snake = [(10, 5), (10, 4), (10, 3)]
        self.player2_snake = [(10, 15), (10, 16), (10, 17)]
        self.player1_direction = "UP"
        self.player2_direction = "DOWN"
        self.food = self.generate_food()
        self.player1_score = 0
        self.player2_score = 0
        
    def generate_food(self):
        while True:
            food = (random.randint(0, self.board_size-1), random.randint(0, self.board_size-1))
            if food not in self.player1_snake and food not in self.player2_snake:
                return food
    
    def move_snake(self, player_id: int, direction: str):
        if player_id == self.player1_id:
            snake = self.player1_snake
            self.player1_direction = direction
        else:
            snake = self.player2_snake
            self.player2_direction = direction
            
        head = snake[0]
        if direction == "UP":
            new_head = (head[0], head[1] - 1)
        elif direction == "DOWN":
            new_head = (head[0], head[1] + 1)
        elif direction == "LEFT":
            new_head = (head[0] - 1, head[1])
        elif direction == "RIGHT":
            new_head = (head[0] + 1, head[1])
        else:
            return False
            
        # Check boundaries
        if (new_head[0] < 0 or new_head[0] >= self.board_size or 
            new_head[1] < 0 or new_head[1] >= self.board_size):
            self.end_game(self.player2_id if player_id == self.player1_id else self.player1_id)
            return False
            
        # Check collision with self or other snake
        if (new_head in snake or new_head in 
            (self.player2_snake if player_id == self.player1_id else self.player1_snake)):
            self.end_game(self.player2_id if player_id == self.player1_id else self.player1_id)
            return False
            
        snake.insert(0, new_head)
        
        # Check if food eaten
        if new_head == self.food:
            if player_id == self.player1_id:
                self.player1_score += 1
            else:
                self.player2_score += 1
            self.food = self.generate_food()
        else:
            snake.pop()
            
        return True
    
    def end_game(self, winner_id: int):
        self.status = "finished"
        self.winner_id = winner_id
        
    def get_state(self):
        return {
            **self.to_dict(),
            "game_type": "snake",
            "player1_snake": self.player1_snake,
            "player2_snake": self.player2_snake,
            "food": self.food,
            "player1_score": self.player1_score,
            "player2_score": self.player2_score,
            "board_size": self.board_size
        }

class PingPongGame(GameBase):
    def __init__(self, game_id: str, player1_id: int, player2_id: int):
        super().__init__(game_id, player1_id, player2_id)
        self.board_width = 800
        self.board_height = 400
        self.paddle_height = 80
        self.paddle_width = 10
        self.ball_size = 10
        
        # Player positions (Y coordinate)
        self.player1_y = self.board_height // 2 - self.paddle_height // 2
        self.player2_y = self.board_height // 2 - self.paddle_height // 2
        
        # Ball position and velocity
        self.ball_x = self.board_width // 2
        self.ball_y = self.board_height // 2
        self.ball_vx = random.choice([-5, 5])
        self.ball_vy = random.randint(-3, 3)
        
        self.player1_score = 0
        self.player2_score = 0
        self.max_score = 5
        
    def move_paddle(self, player_id: int, direction: str):
        if player_id == self.player1_id:
            if direction == "UP" and self.player1_y > 0:
                self.player1_y -= 20
            elif direction == "DOWN" and self.player1_y < self.board_height - self.paddle_height:
                self.player1_y += 20
        else:
            if direction == "UP" and self.player2_y > 0:
                self.player2_y -= 20
            elif direction == "DOWN" and self.player2_y < self.board_height - self.paddle_height:
                self.player2_y += 20
                
    def update_ball(self):
        self.ball_x += self.ball_vx
        self.ball_y += self.ball_vy
        
        # Ball collision with top/bottom walls
        if self.ball_y <= 0 or self.ball_y >= self.board_height - self.ball_size:
            self.ball_vy = -self.ball_vy
            
        # Ball collision with paddles
        if (self.ball_x <= self.paddle_width and 
            self.player1_y <= self.ball_y <= self.player1_y + self.paddle_height):
            self.ball_vx = -self.ball_vx
            self.ball_vy += random.randint(-2, 2)
            
        if (self.ball_x >= self.board_width - self.paddle_width - self.ball_size and
            self.player2_y <= self.ball_y <= self.player2_y + self.paddle_height):
            self.ball_vx = -self.ball_vx
            self.ball_vy += random.randint(-2, 2)
            
        # Score points
        if self.ball_x < 0:
            self.player2_score += 1
            self.reset_ball()
        elif self.ball_x > self.board_width:
            self.player1_score += 1
            self.reset_ball()
            
        # Check win condition
        if self.player1_score >= self.max_score:
            self.end_game(self.player1_id)
        elif self.player2_score >= self.max_score:
            self.end_game(self.player2_id)
            
    def reset_ball(self):
        self.ball_x = self.board_width // 2
        self.ball_y = self.board_height // 2
        self.ball_vx = random.choice([-5, 5])
        self.ball_vy = random.randint(-3, 3)
        
    def end_game(self, winner_id: int):
        self.status = "finished"
        self.winner_id = winner_id
        
    def get_state(self):
        return {
            **self.to_dict(),
            "game_type": "pong",
            "player1_y": self.player1_y,
            "player2_y": self.player2_y,
            "ball_x": self.ball_x,
            "ball_y": self.ball_y,
            "player1_score": self.player1_score,
            "player2_score": self.player2_score,
            "board_width": self.board_width,
            "board_height": self.board_height
        }

class TetrisGame(GameBase):
    def __init__(self, game_id: str, player1_id: int, player2_id: int):
        super().__init__(game_id, player1_id, player2_id)
        self.board_width = 10
        self.board_height = 20
        
        # Initialize empty boards for both players
        self.player1_board = [[0 for _ in range(self.board_width)] for _ in range(self.board_height)]
        self.player2_board = [[0 for _ in range(self.board_width)] for _ in range(self.board_height)]
        
        self.player1_score = 0
        self.player2_score = 0
        self.player1_lines = 0
        self.player2_lines = 0
        
        # Current pieces
        self.player1_piece = self.generate_piece()
        self.player2_piece = self.generate_piece()
        self.player1_piece_x = 4
        self.player1_piece_y = 0
        self.player2_piece_x = 4
        self.player2_piece_y = 0
        
    def generate_piece(self):
        pieces = [
            [[1, 1, 1, 1]],  # I piece
            [[1, 1], [1, 1]],  # O piece
            [[0, 1, 0], [1, 1, 1]],  # T piece
            [[0, 1, 1], [1, 1, 0]],  # S piece
            [[1, 1, 0], [0, 1, 1]],  # Z piece
            [[1, 0, 0], [1, 1, 1]],  # J piece
            [[0, 0, 1], [1, 1, 1]]   # L piece
        ]
        return random.choice(pieces)
        
    def rotate_piece(self, piece):
        return [list(row) for row in zip(*piece[::-1])]
        
    def can_place_piece(self, board, piece, x, y):
        for py, row in enumerate(piece):
            for px, cell in enumerate(row):
                if cell:
                    nx, ny = x + px, y + py
                    if (nx < 0 or nx >= self.board_width or 
                        ny >= self.board_height or 
                        (ny >= 0 and board[ny][nx])):
                        return False
        return True
        
    def place_piece(self, board, piece, x, y):
        for py, row in enumerate(piece):
            for px, cell in enumerate(row):
                if cell:
                    nx, ny = x + px, y + py
                    if ny >= 0:
                        board[ny][nx] = 1
                        
    def clear_lines(self, board):
        lines_cleared = 0
        y = self.board_height - 1
        while y >= 0:
            if all(board[y]):
                del board[y]
                board.insert(0, [0 for _ in range(self.board_width)])
                lines_cleared += 1
            else:
                y -= 1
        return lines_cleared
        
    def move_piece(self, player_id: int, action: str):
        if player_id == self.player1_id:
            board = self.player1_board
            piece = self.player1_piece
            x, y = self.player1_piece_x, self.player1_piece_y
        else:
            board = self.player2_board
            piece = self.player2_piece
            x, y = self.player2_piece_x, self.player2_piece_y
            
        if action == "LEFT":
            new_x = x - 1
            if self.can_place_piece(board, piece, new_x, y):
                if player_id == self.player1_id:
                    self.player1_piece_x = new_x
                else:
                    self.player2_piece_x = new_x
                    
        elif action == "RIGHT":
            new_x = x + 1
            if self.can_place_piece(board, piece, new_x, y):
                if player_id == self.player1_id:
                    self.player1_piece_x = new_x
                else:
                    self.player2_piece_x = new_x
                    
        elif action == "DOWN":
            new_y = y + 1
            if self.can_place_piece(board, piece, x, new_y):
                if player_id == self.player1_id:
                    self.player1_piece_y = new_y
                else:
                    self.player2_piece_y = new_y
            else:
                # Piece landed, place it and generate new piece
                self.place_piece(board, piece, x, y)
                lines_cleared = self.clear_lines(board)
                
                if player_id == self.player1_id:
                    self.player1_lines += lines_cleared
                    self.player1_score += lines_cleared * 100
                    self.player1_piece = self.generate_piece()
                    self.player1_piece_x = 4
                    self.player1_piece_y = 0
                    
                    # Check game over
                    if not self.can_place_piece(board, self.player1_piece, 4, 0):
                        self.end_game(self.player2_id)
                else:
                    self.player2_lines += lines_cleared
                    self.player2_score += lines_cleared * 100
                    self.player2_piece = self.generate_piece()
                    self.player2_piece_x = 4
                    self.player2_piece_y = 0
                    
                    # Check game over
                    if not self.can_place_piece(board, self.player2_piece, 4, 0):
                        self.end_game(self.player1_id)
                        
        elif action == "ROTATE":
            rotated_piece = self.rotate_piece(piece)
            if self.can_place_piece(board, rotated_piece, x, y):
                if player_id == self.player1_id:
                    self.player1_piece = rotated_piece
                else:
                    self.player2_piece = rotated_piece
                    
    def end_game(self, winner_id: int):
        self.status = "finished"
        self.winner_id = winner_id
        
    def get_state(self):
        return {
            **self.to_dict(),
            "game_type": "tetris",
            "player1_board": self.player1_board,
            "player2_board": self.player2_board,
            "player1_piece": self.player1_piece,
            "player2_piece": self.player2_piece,
            "player1_piece_x": self.player1_piece_x,
            "player1_piece_y": self.player1_piece_y,
            "player2_piece_x": self.player2_piece_x,
            "player2_piece_y": self.player2_piece_y,
            "player1_score": self.player1_score,
            "player2_score": self.player2_score,
            "player1_lines": self.player1_lines,
            "player2_lines": self.player2_lines
        }

# Game factory
def create_game(game_type: str, game_id: str, player1_id: int, player2_id: int):
    if game_type == "snake":
        return SnakeGame(game_id, player1_id, player2_id)
    elif game_type == "pong":
        return PingPongGame(game_id, player1_id, player2_id)
    elif game_type == "tetris":
        return TetrisGame(game_id, player1_id, player2_id)
    else:
        raise ValueError(f"Unknown game type: {game_type}")
