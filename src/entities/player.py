from __future__ import annotations
import pygame as pg
from .entity import Entity
from src.core.services import input_manager
from src.utils import Position, PositionCamera, GameSettings, Logger, Direction
from src.core import GameManager
import math
from typing import override
import collections

class Player(Entity):
    speed: float = 5 * GameSettings.TILE_SIZE
    game_manager: GameManager

    def __init__(self, x: float, y: float, game_manager: GameManager) -> None:
        sprite_path = "character/ow3.png"
        super().__init__(x, y, game_manager, sprite_path)

        # checkpoint 3-6: 導航路徑佇列
        self.navigation_path: list[tuple[int, int]] = []
        self.is_auto_moving = False
        
    def start_auto_move(self, target_grid_pos: tuple[int, int]):
        """開始自動導航到目標網格座標"""
        # 取得當前玩家的網格座標
        start_grid_x = int(self.position.x // GameSettings.TILE_SIZE)
        start_grid_y = int(self.position.y // GameSettings.TILE_SIZE)
        start_pos = (start_grid_x, start_grid_y)

        Logger.info(f"Start Navigation: {start_pos} -> {target_grid_pos}")

        # BFS 找路徑
        path = self._bfs_find_path(start_pos, target_grid_pos)
        
        if path:
            self.navigation_path = path
            self.is_auto_moving = True
            Logger.info(f"Path found! Length: {len(path)}")
        else:
            Logger.warning("No path found to destination!")
            self.is_auto_moving = False

    def _bfs_find_path(self, start: tuple[int, int], end: tuple[int, int]) -> list[tuple[int, int]]:
        """廣度優先搜尋演算法 (BFS)"""
        if start == end:
            return []

        # 先檢查終點本身是否就是障礙物
        end_rect = pg.Rect(
            end[0] * GameSettings.TILE_SIZE, 
            end[1] * GameSettings.TILE_SIZE, 
            GameSettings.TILE_SIZE, 
            GameSettings.TILE_SIZE
        )
        if self.game_manager.check_collision(end_rect):
            Logger.warning(f"BFS Failed: The destination {end} is a WALL/OBSTACLE!")
            return []

        # Queue 存放: 當前座標, 路徑列表
        queue = collections.deque([(start, [])])
        visited = set()
        visited.add(start)

        # 上下左右四個方向
        directions = [(0, -1), (0, 1), (-1, 0), (1, 0)] 
        
        steps_check = 0
        
        while queue:
            current, path = queue.popleft()
            steps_check += 1
            if steps_check > 3000: # 稍微加大一點安全閥
                Logger.warning("BFS Timeout: Search steps exceeded limit.")
                break

            if current == end:
                return path 

            cx, cy = current
            
            for dx, dy in directions:
                neighbor = (cx + dx, cy + dy)
                if neighbor[0] < 0 or neighbor[1] < 0 or neighbor[0] > 100 or neighbor[1] > 100:
                    continue
                if neighbor in visited:
                    continue
                check_rect = pg.Rect(
                    neighbor[0] * GameSettings.TILE_SIZE, 
                    neighbor[1] * GameSettings.TILE_SIZE, 
                    GameSettings.TILE_SIZE, 
                    GameSettings.TILE_SIZE
                )
                if not self.game_manager.check_collision(check_rect):
                    visited.add(neighbor)
                    new_path = path + [neighbor]
                    if neighbor == end:
                        return new_path   
                    queue.append((neighbor, new_path))              
        return []

    @override
    def update(self, dt: float) -> None:
        # 自動導航邏輯
        if self.is_auto_moving and self.navigation_path:
            # 取得路徑中的下一個點
            next_grid_x, next_grid_y = self.navigation_path[0]
            
            # 轉換成像素座標
            target_pixel_x = next_grid_x * GameSettings.TILE_SIZE
            target_pixel_y = next_grid_y * GameSettings.TILE_SIZE
            
            # 計算差值向量
            diff_x = target_pixel_x - self.position.x
            diff_y = target_pixel_y - self.position.y
            
            # 設定移動速度
            move_step = self.speed * dt
            
            # 設定動畫所需的 dis
            self.dis = Position(0, 0)

            # 到達判定
            if abs(diff_x) <= move_step and abs(diff_y) <= move_step:
                # 對齊格子
                self.position.x = target_pixel_x
                self.position.y = target_pixel_y
                # 移除已經走到的點
                self.navigation_path.pop(0)
                
                if not self.navigation_path:
                    self.is_auto_moving = False
                    Logger.info("Navigation Arrived!")
            else: # 還沒到繼續移動
                # Normalize 
                if abs(diff_x) > abs(diff_y):
                    dir_x = 1 if diff_x > 0 else -1
                    dir_y = 0
                    self.direction = Direction.RIGHT if dir_x > 0 else Direction.LEFT
                else:
                    dir_x = 0
                    dir_y = 1 if diff_y > 0 else -1
                    self.direction = Direction.DOWN if dir_y > 0 else Direction.UP

                # 實際移動
                move_x = dir_x * move_step
                move_y = dir_y * move_step
                
                self.position.x += move_x
                self.position.y += move_y
                
                self.dis.x = move_x
                self.dis.y = move_y

            # 檢查是否有玩家介入: 按鍵盤則取消導航
            if input_manager.key_down(pg.K_LEFT) or input_manager.key_down(pg.K_RIGHT) or \
               input_manager.key_down(pg.K_UP) or input_manager.key_down(pg.K_DOWN):
                self.is_auto_moving = False
                self.navigation_path = []
                Logger.info("Navigation Cancelled by user.")
            
            # 自動移動時呼叫父類別更新動畫
            super().update(dt)
            return

      
        # 手動移動邏輯
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

        # 預計新位置 X
        new_x = self.position.x + dis.x
        
        # 碰撞偵測 X
        # 建立一個測試用的 Rect
        test_rect = self.animation.rect.copy()
        test_rect.x = new_x
        test_rect.y = self.position.y
        
        if not self.game_manager.check_collision(test_rect):
            self.position.x = new_x
        else:
            self.position.x = self._snap_to_grid(self.position.x)  

        # 預計新位置 Y
        new_y = self.position.y + dis.y    
        
        # 碰撞偵測 Y
        test_rect.x = self.position.x
        test_rect.y = new_y
        
        if not self.game_manager.check_collision(test_rect):
            self.position.y = new_y
        else:
            self.position.y = self._snap_to_grid(self.position.y)
    
        ## 給 Entity 判斷動畫方向
        self.dis = dis
        
        # 檢查傳送點
        tp = self.game_manager.current_map.check_teleport(self.position)
        if tp:
            dest_map = tp.destination
            self.game_manager.switch_map(dest_map)
         
        super().update(dt)
        
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
        if self.is_auto_moving and len(self.navigation_path) > 0:
            start_pos = (self.position.x + GameSettings.TILE_SIZE//2, self.position.y + GameSettings.TILE_SIZE//2)
            
            # 轉換路徑點為螢幕座標
            points = []
            # 加上當前位置
            rect_start = camera.transform_rect(pg.Rect(start_pos[0], start_pos[1], 0, 0))
            points.append((rect_start.x, rect_start.y))

            for px, py in self.navigation_path:
                # 轉回世界座標 (Center)
                world_x = px * GameSettings.TILE_SIZE + GameSettings.TILE_SIZE // 2
                world_y = py * GameSettings.TILE_SIZE + GameSettings.TILE_SIZE // 2
                
                # 轉為螢幕座標
                rect = camera.transform_rect(pg.Rect(world_x, world_y, 0, 0))
                points.append((rect.x, rect.y))
            
            if len(points) > 1:
                # 畫路徑線
                pg.draw.lines(screen, (0, 255, 0), False, points, 3)
                
                # 終點小紅點
                end_point = points[-1]
                pg.draw.circle(screen, (255, 0, 0), end_point, 5)
        
    @override
    def to_dict(self) -> dict[str, object]:
        return super().to_dict()
    
    @classmethod
    @override
    def from_dict(cls, data: dict[str, object], game_manager: GameManager) -> Player:
        return cls(data["x"] * GameSettings.TILE_SIZE, data["y"] * GameSettings.TILE_SIZE, game_manager)

