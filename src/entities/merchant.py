from __future__ import annotations
import pygame
from typing import override

from .entity import Entity
from src.sprites import Sprite
from src.core import GameManager
from src.core.services import input_manager
from src.utils import GameSettings, Direction, Position, PositionCamera, Logger

class Merchant(Entity):
    goods: list[dict]
    max_tiles: int | None
    warning_sign: Sprite
    detected: bool
    los_direction: Direction

    def __init__(
        self, 
        x: float, 
        y: float, 
        game_manager: GameManager, 
        max_tiles: int | None = 2,
        facing: Direction | None = None,
        goods: list[dict] | None = None
        ):
        super().__init__(x, y, game_manager)
        self.goods = goods if goods is not None else []
        self.max_tiles = max_tiles
        
        if facing is None:
            facing = Direction.DOWN
        self._set_direction(facing)

        # 驚嘆號
        self.warning_sign = Sprite("exclamation.png", (GameSettings.TILE_SIZE // 2, GameSettings.TILE_SIZE // 2))
        self.warning_sign.update_pos(Position(x + GameSettings.TILE_SIZE // 4, y - GameSettings.TILE_SIZE // 2))
        self.detected = False

    @override
    def update(self, dt: float) -> None:
        self._has_los_to_player()
        self.animation.update_pos(self.position)
    
    @override
    def draw(self, screen: pygame.Surface, camera: PositionCamera) -> None:
        super().draw(screen, camera)
        
        # 當玩家在視線範圍內時，顯示驚嘆號
        if self.detected:
            self.warning_sign.draw(screen, camera)
            
        if GameSettings.DRAW_HITBOXES:
            los_rect = self._get_los_rect()
            if los_rect is not None:
                pygame.draw.rect(screen, (0, 255, 255), camera.transform_rect(los_rect), 1)

    def _set_direction(self, direction: Direction) -> None:
        self.direction = direction
        if direction == Direction.RIGHT:
            self.animation.switch("right")
        elif direction == Direction.LEFT:
            self.animation.switch("left")
        elif direction == Direction.DOWN:
            self.animation.switch("down")
        else:
            self.animation.switch("up")
        self.los_direction = self.direction        

    def _get_los_rect(self) -> pygame.Rect | None:
        '''
        Create hitbox to detect line of sight towards the player
        '''
        if self.max_tiles is None or self.max_tiles <= 0:
            return None
        
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
        player = self.game_manager.player
        if player is None:
            self.detected = False
            return
        los_rect = self._get_los_rect()
        if los_rect is None:
            self.detected = False
            return

        if los_rect.colliderect(player.animation.rect):
            self.detected = True
        else:
            self.detected = False

    @classmethod
    @override
    def from_dict(cls, data: dict, game_manager: GameManager) -> "Merchant":
        max_tiles = data.get("max_tiles", 2)
        facing_val = data.get("facing")
        facing: Direction | None = None
        
        if facing_val is not None:
            if isinstance(facing_val, str):
                facing = Direction[facing_val]
            elif isinstance(facing_val, Direction):
                facing = facing_val


        # 看商人有賣甚麼，並從資料庫查找商品資訊
        raw_goods_ids = data.get("goods", [])
        resolved_goods = []

        for item_id in raw_goods_ids:
            item_info = game_manager.item_database.get(item_id)
            if item_info:
                item_copy = item_info.copy()
                item_copy["id"] = item_id 
                resolved_goods.append(item_copy)
            else:
                Logger.warning(f"Merchant has unknown item ID: {item_id}")
                
        return cls(
            data["x"] * GameSettings.TILE_SIZE,
            data["y"] * GameSettings.TILE_SIZE,
            game_manager,
            max_tiles,
            facing,
            resolved_goods
        )

    @override
    def to_dict(self) -> dict[str, object]:
        base: dict[str, object] = super().to_dict()
        base["facing"] = self.direction.name
        base["max_tiles"] = self.max_tiles
        base["goods"] = [item.get("id") for item in self.goods if "id" in item]
        return base