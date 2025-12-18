from __future__ import annotations
import pygame as pg
from typing import override
from src.sprites import Animation
from src.utils import Position, PositionCamera, Direction, GameSettings
from src.core import GameManager


class Entity:
    animation: Animation
    direction: Direction
    position: Position
    game_manager: GameManager
    
    def __init__(self, x: float, y: float, game_manager: GameManager, sprite_path: str = "character/ow1.png") -> None:
        # Sprite is only for debug, need to change into animations
        self.animation = Animation(
            sprite_path, ["down", "left", "right", "up"], 4,
            (GameSettings.TILE_SIZE, GameSettings.TILE_SIZE)
        )
        
        self.position = Position(x, y)
        self.direction = Direction.DOWN
        self.animation.update_pos(self.position)
        self.game_manager = game_manager

    def update(self, dt: float) -> None:

        ## 根據玩家方向設定 direction
        if hasattr(self, 'dis') and self.dis is not None:
            dis = self.dis
            if abs(dis.x) > abs(dis.y):
                self.direction = Direction.RIGHT if dis.x > 0 else Direction.LEFT
            elif abs(dis.y) > 0:
                self.direction = Direction.DOWN if dis.y > 0 else Direction.UP    

        ## 根據 direction 切換動畫
        if self.direction == Direction.UP:
            self.animation.switch("up")
        elif self.direction == Direction.DOWN:
            self.animation.switch("down")
        elif self.direction == Direction.LEFT:
            self.animation.switch("left")
        elif self.direction == Direction.RIGHT:
            self.animation.switch("right")

        self.animation.update_pos(self.position)
        self.animation.update(dt)
        
    def draw(self, screen: pg.Surface, camera: PositionCamera) -> None:
        self.animation.draw(screen, camera)
        if GameSettings.DRAW_HITBOXES:
            self.animation.draw_hitbox(screen, camera)
        
    @staticmethod
    def _snap_to_grid(value: float) -> int:
        return round(value / GameSettings.TILE_SIZE) * GameSettings.TILE_SIZE
    
    @property
    def camera(self) -> PositionCamera:
        '''
        [TODO HACKATHON 3]
        Implement the correct algorithm of player camera
        '''
        ## PositionCamera 相機的左上角位置，決定顯示哪塊地圖
        ## 將相機放在玩家中心: 減掉畫面寬和高的一半，讓玩家保持在畫面中央
        cam_x = int(self.position.x - GameSettings.SCREEN_WIDTH // 2)
        cam_y = int(self.position.y - GameSettings.SCREEN_HEIGHT // 2)
        
        return PositionCamera(cam_x, cam_y)
            
    def to_dict(self) -> dict[str, object]:
        return {
            "x": self.position.x / GameSettings.TILE_SIZE,
            "y": self.position.y / GameSettings.TILE_SIZE,
        }
        
    @classmethod
    def from_dict(cls, data: dict[str, float | int], game_manager: GameManager) -> Entity:
        x = float(data["x"])
        y = float(data["y"])
        return cls(x * GameSettings.TILE_SIZE, y * GameSettings.TILE_SIZE, game_manager)
        