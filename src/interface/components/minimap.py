import pygame as pg
from src.utils import GameSettings, PositionCamera

class Minimap:
    def __init__(self, game_manager, width=200, height=150):
        self.game_manager = game_manager
        
        # 小地圖的尺寸
        self.w = width
        self.h = height
        
        # 小地圖顯示位置
        self.x = 20
        self.y = 20
        
        # 背景
        self.cached_image: pg.Surface | None = None
        self.last_map_key: str | None = None
        self.border_color = (200, 200, 200)
        
        # 鏡頭框顏色 (黃色)
        self.camera_rect_color = (255, 255, 0)
        # 玩家點顏色 (紅色)
        self.player_dot_color = (255, 50, 50)

    def _update_map_snapshot(self):
        """生成當前地圖的縮圖快照"""
        current_map = self.game_manager.current_map
        if not current_map: return

        # 取得地圖真實尺寸
        map_w_tiles = getattr(current_map, 'width', 50)
        map_h_tiles = getattr(current_map, 'height', 50)
        real_w = map_w_tiles * GameSettings.TILE_SIZE
        real_h = map_h_tiles * GameSettings.TILE_SIZE
        
        # 建立一個跟真實地圖一樣大的暫存畫布
        temp_surface = pg.Surface((real_w, real_h))
        
        # 使用一個位於 (0,0) 的假相機來繪製整張地圖
        dummy_camera = PositionCamera(0, 0)
        
        # 呼叫地圖原本的 draw 方法，畫在這個暫存畫布上
        current_map.draw(temp_surface, dummy_camera)
        
        # 將畫好的大地圖縮小成小地圖的尺寸
        self.cached_image = pg.transform.scale(temp_surface, (self.w, self.h))
        
        # 加上半透明效果
        self.cached_image.set_alpha(200)
        
        # 更新紀錄
        self.last_map_key = self.game_manager.current_map_key

    def draw(self, screen: pg.Surface):
        current_map_key = self.game_manager.current_map_key
        
        # 檢查是否需要更新快照
        if self.cached_image is None or current_map_key != self.last_map_key:
            self._update_map_snapshot()
            
        if self.cached_image is None: return

        # 繪製地圖縮圖
        screen.blit(self.cached_image, (self.x, self.y))
        
        # 繪製邊框
        pg.draw.rect(screen, self.border_color, (self.x, self.y, self.w, self.h), 2)
        
        # 準備計算座標
        player = self.game_manager.player
        current_map = self.game_manager.current_map
        if not player or not current_map: return

        real_map_w = getattr(current_map, 'width', 50) * GameSettings.TILE_SIZE
        real_map_h = getattr(current_map, 'height', 50) * GameSettings.TILE_SIZE
        
        # 計算比例
        scale_x = self.w / real_map_w
        scale_y = self.h / real_map_h

        # 計算並繪製玩家點: 玩家在小地圖的 x = 真實 x * 比例 + 小地圖偏移 x
        p_mini_x = self.x + (player.position.x * scale_x)
        p_mini_y = self.y + (player.position.y * scale_y)
        pg.draw.circle(screen, self.player_dot_color, (int(p_mini_x), int(p_mini_y)), 3)
        
        # 計算並繪製鏡頭框 
        view_w_real = GameSettings.SCREEN_WIDTH
        view_h_real = GameSettings.SCREEN_HEIGHT
        
        # 視野的左上角座標
        view_x_real = player.position.x - (view_w_real / 2)
        view_y_real = player.position.y - (view_h_real / 2)
        
        # 邊界限制: 不讓框框跑出地圖外
        view_x_real = max(0, min(view_x_real, real_map_w - view_w_real))
        view_y_real = max(0, min(view_y_real, real_map_h - view_h_real))

        # 轉換成小地圖座標
        rect_x = self.x + (view_x_real * scale_x)
        rect_y = self.y + (view_y_real * scale_y)
        rect_w = view_w_real * scale_x
        rect_h = view_h_real * scale_y
        
        # 畫出框框
        pg.draw.rect(screen, self.camera_rect_color, (rect_x, rect_y, rect_w, rect_h), 1)