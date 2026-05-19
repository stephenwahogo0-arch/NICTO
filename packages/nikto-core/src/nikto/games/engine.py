"""NIKTO Games — playable arcade games (Pong, Snake, Tetris, Platformer, RPG)."""
import random, time, uuid, os, json
from typing import Any


class GameBase:
    def __init__(self, name: str, genre: str):
        self.name = name
        self.genre = genre
        self.game_id = uuid.uuid4().hex[:8]
        self.score = 0
        self.level = 1
        self.state = "ready"
        self.start_time = 0.0
        self.duration = 0.0

    def start(self) -> dict:
        self.state = "playing"
        self.start_time = time.time()
        return {"success": True, "game_id": self.game_id, "name": self.name, "genre": self.genre, "state": self.state}

    def end(self) -> dict:
        self.state = "ended"
        self.duration = time.time() - self.start_time
        return {"success": True, "game_id": self.game_id, "final_score": self.score, "duration_sec": round(self.duration, 2), "state": self.state}

    def summary(self) -> dict:
        return {"name": self.name, "genre": self.genre, "game_id": self.game_id, "score": self.score, "level": self.level, "state": self.state}


class Pong(GameBase):
    def __init__(self):
        super().__init__("Pong", "arcade")
        self.player_y = 50
        self.ai_y = 50
        self.ball_x = 50
        self.ball_y = 50
        self.ball_dx = 1
        self.ball_dy = 1
        self.player_score = 0
        self.ai_score = 0
        self.max_score = 7

    def tick(self) -> dict:
        self.ball_x += self.ball_dx * 2
        self.ball_y += self.ball_dy * 2
        if self.ball_y <= 0 or self.ball_y >= 100:
            self.ball_dy *= -1
        ai_target = self.ball_y - self.ai_y
        self.ai_y += 1 if ai_target > 0 else -1 if ai_target < 0 else 0
        self.ai_y = max(0, min(100, self.ai_y))
        if self.ball_x <= 2 and self.player_y - 10 <= self.ball_y <= self.player_y + 10:
            self.ball_dx = 1
        elif self.ball_x <= 0:
            self.ai_score += 1
            self.ball_x = 50; self.ball_y = 50
        if self.ball_x >= 98 and self.ai_y - 10 <= self.ball_y <= self.ai_y + 10:
            self.ball_dx = -1
        elif self.ball_x >= 100:
            self.player_score += 1
            self.ball_x = 50; self.ball_y = 50
        self.score = self.player_score
        return {"success": True, "ball_x": round(self.ball_x, 1), "ball_y": round(self.ball_y, 1), "player_score": self.player_score, "ai_score": self.ai_score, "game_over": self.player_score >= self.max_score or self.ai_score >= self.max_score}

    def move_paddle(self, direction: str) -> dict:
        if direction == "up":
            self.player_y = max(0, self.player_y - 10)
        elif direction == "down":
            self.player_y = min(100, self.player_y + 10)
        return {"success": True, "player_y": self.player_y}


class Snake(GameBase):
    def __init__(self):
        super().__init__("Snake", "arcade")
        self.grid_size = 20
        self.snake = [(10, 10)]
        self.food = self._place_food()
        self.direction = (1, 0)
        self.growing = False

    def _place_food(self):
        while True:
            pos = (random.randint(0, self.grid_size - 1), random.randint(0, self.grid_size - 1))
            if pos not in self.snake:
                return pos

    def change_direction(self, dx: int, dy: int) -> dict:
        if (dx * -1, dy * -1) != self.direction:
            self.direction = (dx, dy)
        return {"success": True, "direction": self.direction}

    def tick(self) -> dict:
        head = self.snake[-1]
        new_head = (head[0] + self.direction[0], head[1] + self.direction[1])
        if new_head[0] < 0 or new_head[0] >= self.grid_size or new_head[1] < 0 or new_head[1] >= self.grid_size:
            return {"success": True, "game_over": True, "score": self.score, "reason": "wall_collision"}
        if new_head in self.snake:
            return {"success": True, "game_over": True, "score": self.score, "reason": "self_collision"}
        self.snake.append(new_head)
        if new_head == self.food:
            self.score += 10
            self.food = self._place_food()
            if self.score % 50 == 0:
                self.level += 1
        else:
            self.snake.pop(0)
        return {"success": True, "game_over": False, "score": self.score, "snake_length": len(self.snake), "food": self.food}


class Tetris(GameBase):
    def __init__(self):
        super().__init__("Tetris", "puzzle")
        self.width = 10
        self.height = 20
        self.board = [[0] * self.width for _ in range(self.height)]
        self.pieces = [[(0,0),(1,0),(2,0),(3,0)], [(0,0),(1,0),(0,1),(1,1)], [(0,0),(1,0),(2,0),(2,1)], [(0,0),(1,0),(2,0),(0,1)], [(0,0),(1,0),(1,1),(2,1)], [(1,0),(0,1),(1,1),(2,1)], [(0,0),(0,1),(1,1),(1,2)]]
        self.current = self._new_piece()
        self.lines_cleared = 0

    def _new_piece(self):
        return {"shape": random.choice(self.pieces), "x": self.width // 2 - 2, "y": 0}

    def _collides(self, shape, x, y):
        for dx, dy in shape:
            nx, ny = x + dx, y + dy
            if nx < 0 or nx >= self.width or ny >= self.height:
                return True
            if ny >= 0 and self.board[ny][nx]:
                return True
        return False

    def tick(self) -> dict:
        if not self._collides(self.current["shape"], self.current["x"], self.current["y"] + 1):
            self.current["y"] += 1
            return {"success": True, "landed": False, "lines": self.lines_cleared}
        for dx, dy in self.current["shape"]:
            nx, ny = self.current["x"] + dx, self.current["y"] + dy
            if 0 <= nx < self.width and 0 <= ny < self.height:
                self.board[ny][nx] = 1
        new_board = [row for row in self.board if any(c == 0 for c in row)]
        cleared = self.height - len(new_board)
        self.lines_cleared += cleared
        self.board = [[0] * self.width for _ in range(cleared)] + new_board
        self.score += cleared * 100 * self.level
        if cleared > 0:
            self.level = self.lines_cleared // 10 + 1
        self.current = self._new_piece()
        if self._collides(self.current["shape"], self.current["x"], self.current["y"]):
            return {"success": True, "game_over": True, "score": self.score, "lines": self.lines_cleared}
        return {"success": True, "landed": True, "lines": self.lines_cleared}

    def move_piece(self, dx: int) -> dict:
        if not self._collides(self.current["shape"], self.current["x"] + dx, self.current["y"]):
            self.current["x"] += dx
        return {"success": True}

    def rotate_piece(self) -> dict:
        rotated = [(-dy, dx) for dx, dy in self.current["shape"]]
        if not self._collides(rotated, self.current["x"], self.current["y"]):
            self.current["shape"] = rotated
        return {"success": True}


class Platformer(GameBase):
    def __init__(self):
        super().__init__("Jump Runner", "platformer")
        self.player_x = 5
        self.player_y = 10
        self.vx = 0
        self.vy = 0
        self.gravity = 0.5
        self.jump_power = -8
        self.level_width = 100
        self.level_height = 20
        self.platforms = [(0, 15, 20), (15, 12, 8), (25, 14, 6), (35, 10, 10), (48, 13, 5), (55, 8, 12), (70, 11, 8), (80, 6, 15)]
        self.collected = []
        self.coins = [(random.randint(1, self.level_width - 1), random.randint(1, self.level_height - 2)) for _ in range(10)]
        self.goal_x = self.level_width - 5
        self.goal_y = 2

    def tick(self) -> dict:
        self.vy += self.gravity
        self.player_x += self.vx
        self.player_y += self.vy
        if self.player_y > self.level_height:
            return {"success": True, "game_over": True, "score": self.score, "reason": "fell"}
        on_ground = False
        for px, py, pw in self.platforms:
            if px <= self.player_x <= px + pw and abs(self.player_y - py) < 1 and self.vy >= 0:
                self.player_y = py
                self.vy = 0
                on_ground = True
        for coin in self.coins[:]:
            if abs(self.player_x - coin[0]) < 2 and abs(self.player_y - coin[1]) < 2:
                self.coins.remove(coin)
                self.collected.append(coin)
                self.score += 10
        if abs(self.player_x - self.goal_x) < 2 and abs(self.player_y - self.goal_y) < 2:
            return {"success": True, "game_over": True, "won": True, "score": self.score}
        return {"success": True, "player_x": round(self.player_x, 1), "player_y": round(self.player_y, 1), "on_ground": on_ground, "coins_left": len(self.coins)}

    def jump(self) -> dict:
        self.vy = self.jump_power
        return {"success": True}

    def move(self, direction: str) -> dict:
        self.vx = 3 if direction == "right" else -3 if direction == "left" else 0
        return {"success": True}


class RPGCharacter:
    def __init__(self, name: str, char_class: str):
        self.name = name
        self.char_class = char_class
        self.level = 1
        self.hp = 100
        self.max_hp = 100
        self.mp = 50
        self.max_mp = 50
        self.attack = 10
        self.defense = 5
        self.xp = 0
        self.xp_to_next = 100
        self.inventory = []

    def take_damage(self, dmg: int) -> dict:
        actual = max(1, dmg - self.defense)
        self.hp = max(0, self.hp - actual)
        return {"damage_taken": actual, "hp": self.hp, "alive": self.hp > 0}

    def heal(self, amount: int) -> dict:
        self.hp = min(self.max_hp, self.hp + amount)
        return {"healed": amount, "hp": self.hp}

    def gain_xp(self, amount: int) -> dict:
        self.xp += amount
        leveled_up = False
        while self.xp >= self.xp_to_next:
            self.xp -= self.xp_to_next
            self.level += 1
            self.max_hp += 20
            self.hp = self.max_hp
            self.max_mp += 10
            self.mp = self.max_mp
            self.attack += 5
            self.defense += 3
            self.xp_to_next = int(self.xp_to_next * 1.5)
            leveled_up = True
        return {"xp": self.xp, "level": self.level, "leveled_up": leveled_up}


class RogueLike(GameBase):
    def __init__(self):
        super().__init__("Dungeon Crawler", "rpg")
        self.hero = RPGCharacter("NIKTO", "sage")
        self.floor = 1
        self.map_size = 10
        self.enemies_killed = 0
        self.treasure_found = 0

    def explore_room(self) -> dict:
        encounters = ["enemy", "treasure", "trap", "empty", "shop", "boss"]
        encounter = random.choice(encounters)
        result = {"encounter": encounter, "floor": self.floor}
        if encounter == "enemy":
            enemy_hp = random.randint(10, 30) + self.floor * 5
            dmg_to_enemy = self.hero.attack + random.randint(0, 5)
            dmg_to_hero = max(1, enemy_hp // 3 - self.hero.defense)
            self.hero.take_damage(dmg_to_hero)
            self.hero.gain_xp(dmg_to_enemy)
            self.enemies_killed += 1
            self.score += 20
            result.update({"enemy_hp": enemy_hp, "damage_dealt": dmg_to_enemy, "damage_taken": dmg_to_hero, "hero_hp": self.hero.hp, "hero_alive": self.hero.hp > 0})
        elif encounter == "treasure":
            gold = random.randint(10, 50) + self.floor * 5
            self.score += gold
            self.treasure_found += 1
            result["gold_found"] = gold
        elif encounter == "trap":
            trap_dmg = random.randint(5, 15) + self.floor * 2
            self.hero.take_damage(trap_dmg)
            result["trap_damage"] = trap_dmg
        elif encounter == "shop":
            heal_amt = random.randint(10, 30)
            self.hero.heal(heal_amt)
            result["healed"] = heal_amt
        elif encounter == "boss":
            boss_hp = 50 + self.floor * 20
            rewards = self.floor * 50
            self.hero.gain_xp(rewards)
            self.score += rewards
            self.enemies_killed += 1
            result.update({"boss_hp": boss_hp, "rewards": rewards})
        if not self.hero.hp > 0:
            result["game_over"] = True
            self.state = "ended"
        return {"success": True, **result}

    def descend(self) -> dict:
        if self.hero.hp > 0:
            self.floor += 1
            self.hero.heal(random.randint(10, 30))
            return {"success": True, "floor": self.floor, "hero_hp": self.hero.hp}
        return {"success": False, "error": "Hero is defeated"}


class GameEngine:
    def __init__(self):
        self.active_games: dict[str, GameBase] = {}

    def create_game(self, game_type: str) -> dict:
        game_map = {"pong": Pong, "snake": Snake, "tetris": Tetris, "platformer": Platformer, "rpg": RogueLike}
        cls = game_map.get(game_type.lower())
        if not cls:
            return {"success": False, "error": f"Unknown game type: {game_type}. Available: {list(game_map.keys())}"}
        game = cls()
        result = game.start()
        self.active_games[game.game_id] = game
        return {"success": True, "game": result, "game_type": game_type}

    def get_game(self, game_id: str):
        return self.active_games.get(game_id)

    def list_games(self) -> list:
        return [g.summary() for g in self.active_games.values()]

    def remove_game(self, game_id: str) -> bool:
        if game_id in self.active_games:
            del self.active_games[game_id]
            return True
        return False
