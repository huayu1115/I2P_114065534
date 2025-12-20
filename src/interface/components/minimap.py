import pygame as pg
from src.utils import GameSettings, PositionCamera

class Minimap:
    def __init__(self, game_manager, font: pg.font.Font, width=200, height=150):
        self.game_manager = game_manager
        self.font = font
        
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
        if hasattr(current_map, "tmxdata"):
            map_w_tiles = current_map.tmxdata.width
            map_h_tiles = current_map.tmxdata.height
        else:
            map_w_tiles = 50
            map_h_tiles = 50

        real_w = map_w_tiles * GameSettings.TILE_SIZE
        real_h = map_h_tiles * GameSettings.TILE_SIZE

        if real_w > 0:
            self.h = int(self.w * (real_h / real_w))
        
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

        # 繪製地圖縮圖背景
        screen.blit(self.cached_image, (self.x, self.y))
        pg.draw.rect(screen, self.border_color, (self.x, self.y, self.w, self.h), 2)
        
        # 取得必要的參照
        player = self.game_manager.player
        current_map = self.game_manager.current_map
        if not player or not current_map: return

        # 正確取得地圖真實像素寬高
        map_tiles_w = getattr(current_map.tmxdata, 'width', 1)
        map_tiles_h = getattr(current_map.tmxdata, 'height', 1)
        
        real_map_w = map_tiles_w * GameSettings.TILE_SIZE
        real_map_h = map_tiles_h * GameSettings.TILE_SIZE
        
        # 計算比例尺: 小地圖寬度 / 真實地圖寬度
        scale_x = self.w / real_map_w
        scale_y = self.h / real_map_h

        # 繪製玩家紅點：(pos.x + 半個格子) * 比例
        player_center_x = player.position.x + (GameSettings.TILE_SIZE / 2)
        player_center_y = player.position.y + (GameSettings.TILE_SIZE / 2)

        p_mini_x = self.x + (player_center_x * scale_x)
        p_mini_y = self.y + (player_center_y * scale_y)
        
        # 限制紅點不要畫出框框外
        p_mini_x = max(self.x, min(self.x + self.w, p_mini_x))
        p_mini_y = max(self.y, min(self.y + self.h, p_mini_y))
        
        pg.draw.circle(screen, self.player_dot_color, (int(p_mini_x), int(p_mini_y)), 3)
        
        # 繪製黃色鏡頭框
        view_w_real = min(GameSettings.SCREEN_WIDTH, real_map_w)
        view_h_real = min(GameSettings.SCREEN_HEIGHT, real_map_h)
        
        # 鏡頭中心對準玩家: 左上角 = 玩家中心 - (畫面寬高 / 2)
        cam_x = player_center_x - (view_w_real / 2)
        cam_y = player_center_y - (view_h_real / 2)
        
        # 限制鏡頭框不要超出真實地圖邊界
        cam_x = max(0, min(cam_x, real_map_w - view_w_real))
        cam_y = max(0, min(cam_y, real_map_h - view_h_real))

        # 轉換為小地圖座標
        rect_x = self.x + (cam_x * scale_x)
        rect_y = self.y + (cam_y * scale_y)
        rect_w = view_w_real * scale_x
        rect_h = view_h_real * scale_y
        
        pg.draw.rect(screen, self.camera_rect_color, (rect_x, rect_y, rect_w, rect_h), 1)

        # 繪製座標文字
        grid_x = int(player.position.x // GameSettings.TILE_SIZE)
        grid_y = int(player.position.y // GameSettings.TILE_SIZE)
        
        coord_text = f"Pos: ({grid_x}, {grid_y})"
        text_surf = self.font.render(coord_text, True, (255, 255, 255))
        shadow_surf = self.font.render(coord_text, True, (0, 0, 0))
        
        screen.blit(shadow_surf, (self.x + 1, self.y + self.h + 6))
        screen.blit(text_surf, (self.x, self.y + self.h + 5))