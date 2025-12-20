from __future__ import annotations
import pygame
from typing import override

from .entity import Entity
from src.sprites import Sprite
from src.core import GameManager
from src.utils import GameSettings, Direction, Position, PositionCamera, Logger
from src.entities.monster import Monster

class Nurse(Entity):
    warning_sign: Sprite
    detected: bool
    max_tiles: int = 2 

    def __init__(
        self, 
        x: float, 
        y: float, 
        game_manager: GameManager, 
        facing: Direction | None = None
    ):
        super().__init__(x, y, game_manager, sprite_path="character/ow2.png") 
        
        if facing is None:
            facing = Direction.DOWN
        self._set_direction(facing)

        self.warning_sign = Sprite("exclamation.png", (GameSettings.TILE_SIZE // 2, GameSettings.TILE_SIZE // 2))
        self.warning_sign.update_pos(Position(x + GameSettings.TILE_SIZE // 4, y - GameSettings.TILE_SIZE // 2))
        self.detected = False

    def heal_team(self) -> str:
        """治療背包內所有怪獸，並回傳訊息字串"""
        bag_monsters = self.game_manager.bag._monsters_data
        
        count = 0
        for m_data in bag_monsters:
            # 取得怪獸基本資料
            name = m_data.get("name")
            level = m_data.get("level", 1)
            
            db_data = self.game_manager.monster_database.get(name, {})
            base_hp = db_data.get("base_hp", 40)
            
            # 使用 Monster 類別的公式計算 Max HP
            max_hp = Monster.calculate_max_hp(base_hp, level)
            
            # 恢復血量
            m_data["hp"] = max_hp
            count += 1
            
        Logger.info("Nurse healed the team.")
        return "Your pokemon are fully healed!"

    @override
    def update(self, dt: float) -> None:
        self._has_los_to_player()
        self.animation.update_pos(self.position)

    @override
    def draw(self, screen: pygame.Surface, camera: PositionCamera) -> None:
        super().draw(screen, camera)
        
        if self.detected:
            self.warning_sign.draw(screen, camera)

    def _set_direction(self, direction: Direction) -> None:
        self.direction = direction
        if direction == Direction.RIGHT: self.animation.switch("right")
        elif direction == Direction.LEFT: self.animation.switch("left")
        elif direction == Direction.DOWN: self.animation.switch("down")
        else: self.animation.switch("up")

    def _get_los_rect(self) -> pygame.Rect | None:
        """取得視線範圍 (Hitbox)"""
        distance = self.max_tiles * GameSettings.TILE_SIZE
        x, y = self.position.x, self.position.y
        size = GameSettings.TILE_SIZE
        
        if self.direction == Direction.RIGHT:
            return pygame.Rect(x + size, y, distance, size)
        elif self.direction == Direction.LEFT:
            return pygame.Rect(x - distance, y, distance, size)
        elif self.direction == Direction.DOWN:
            return pygame.Rect(x, y + size, size, distance)
        elif self.direction == Direction.UP:
            return pygame.Rect(x, y - distance, size, distance)
        return None

    def _has_los_to_player(self) -> None:
        """偵測玩家是否在前方"""
        player = self.game_manager.player
        if player is None:
            self.detected = False
            return
        los_rect = self._get_los_rect()
        if los_rect and los_rect.colliderect(player.animation.rect):
            self.detected = True
        else:
            self.detected = False

    @classmethod
    @override
    def from_dict(cls, data: dict, game_manager: GameManager) -> "Nurse":
        facing_val = data.get("facing", "DOWN")
        facing = Direction[facing_val] if isinstance(facing_val, str) else Direction.DOWN
        
        return cls(
            data["x"] * GameSettings.TILE_SIZE,
            data["y"] * GameSettings.TILE_SIZE,
            game_manager,
            facing
        )

    @override
    def to_dict(self) -> dict[str, object]:
        base = super().to_dict()
        base["facing"] = self.direction.name
        return base