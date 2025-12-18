from __future__ import annotations
import pygame as pg
from .entity import Entity
from src.core.services import input_manager
from src.utils import Position, PositionCamera, GameSettings, Logger
from src.core import GameManager
import math
from typing import override

class Player(Entity):
    speed: float = 5 * GameSettings.TILE_SIZE
    game_manager: GameManager

    def __init__(self, x: float, y: float, game_manager: GameManager) -> None:
        sprite_path = "character/ow3.png"
        super().__init__(x, y, game_manager, sprite_path)
        

    @override
    def update(self, dt: float) -> None:
        ## 暫存每幀位移向量，從 (0, 0) 開始
        dis = Position(0, 0) 

        ## 控制玩家移動
        if input_manager.key_down(pg.K_LEFT) or input_manager.key_down(pg.K_a):
            dis.x -= 1
        if input_manager.key_down(pg.K_RIGHT) or input_manager.key_down(pg.K_d):
            dis.x += 1
        if input_manager.key_down(pg.K_UP) or input_manager.key_down(pg.K_w):
            dis.y -= 1
        if input_manager.key_down(pg.K_DOWN) or input_manager.key_down(pg.K_s):
            dis.y += 1

        ## normalize
        length = (dis.x**2 + dis.y**2) ** 0.5
        if length != 0:
            dis.x = dis.x / length * self.speed * dt
            dis.y = dis.y / length * self.speed * dt

        # 預計新位置
        new_x = self.position.x + dis.x
        new_y = self.position.y + dis.y    
      
        # 嘗試 X 軸移動
        self.animation.rect.x = new_x
        self.animation.rect.y = self.position.y
        if not self.game_manager.check_collision(self.animation.rect):
            self.position.x = new_x
        else:
            self.position.x = self._snap_to_grid(self.position.x)  

        # 嘗試 Y 軸移動
        self.animation.rect.x = self.position.x 
        self.animation.rect.y = new_y
        if not self.game_manager.check_collision(self.animation.rect):
            self.position.y = new_y
        else:
            self.position.y = self._snap_to_grid(self.position.y)
      
        ## 給 Entity 判斷方向
        self.dis = dis
        
        '''
        [TODO HACKATHON 2]
        Calculate the distance change, and then normalize the distance
        
        [TODO HACKATHON 4]
        Check if there is collision, if so try to make the movement smooth
        Hint #1 : use entity.py _snap_to_grid function or create a similar function
        Hint #2 : Beware of glitchy teleportation, you must do
                    1. Update X
                    2. If collide, snap to grid
                    3. Update Y
                    4. If collide, snap to grid
                  instead of update both x, y, then snap to grid
        '''
        
        # Check teleportation
        tp = self.game_manager.current_map.check_teleport(self.position)
        if tp:

            dest_map = tp.destination
            self.game_manager.switch_map(dest_map)
         
        super().update(dt)

    @override
    def draw(self, screen: pg.Surface, camera: PositionCamera) -> None:
        super().draw(screen, camera)
        
    @override
    def to_dict(self) -> dict[str, object]:
        return super().to_dict()
    
    @classmethod
    @override
    def from_dict(cls, data: dict[str, object], game_manager: GameManager) -> Player:
        return cls(data["x"] * GameSettings.TILE_SIZE, data["y"] * GameSettings.TILE_SIZE, game_manager)

