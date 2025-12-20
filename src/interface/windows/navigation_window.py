import pygame as pg
from src.interface.windows.window import Window
from src.interface.components import Button
from src.utils import Logger, Position

class NavigationWindow(Window):
    def __init__(self, game_manager, font_title: pg.font.Font, font_item: pg.font.Font):
        super().__init__(game_manager, 600, 500)
        self.font_title = font_title
        self.font_item = font_item
        
        # 標題
        self.title_text = self.font_title.render("Navigation", True, (0, 0, 0))
        
        # 導航的地點清單
        self.locations = [
            {"name": "Home", "map": "map.tmx", "pos": (16, 30)},
            {"name": "Gym", "map": "map.tmx", "pos": (24, 25)},
            {"name": "Pokemon Center", "map": "map.tmx", "pos": (46, 27)},
            {"name": "Shop", "map": "map.tmx", "pos": (38, 27)}
        ]
        
        self.ui_items = []
        self._init_ui()

    def _init_ui(self):
        """生成按鈕與計算排版位置"""
        columns = 2 
        gap_x = 20 
        gap_y = 20 
        
        # 計算每個底框的大小
        item_width = (self.rect.width - 80 - gap_x) // columns 
        item_height = 70 
        
        start_x = self.rect.x + 40 
        start_y = self.rect.y + 80

        # 按鈕圖片與大小
        btn_width, btn_height = 40, 40
        img_normal = "UI/button_play.png"
        img_hover = "UI/button_play_hover.png"

        for i, loc in enumerate(self.locations):
            # 計算格狀位置
            col = i % columns 
            row = i // columns 
            
            # 底框的左上角座標
            item_x = start_x + col * (item_width + gap_x)
            item_y = start_y + row * (item_height + gap_y)
            container_rect = pg.Rect(item_x, item_y, item_width, item_height)

            # 計算按鈕位置
            btn_x = item_x + item_width - btn_width - 15 
            btn_y = item_y + (item_height - btn_height) // 2

            # 建立按鈕
            btn = Button(
                img_normal, img_hover,
                btn_x, btn_y, btn_width, btn_height,
                on_click=lambda l=loc: self.on_location_selected(l)
            )
            
            # 將所有繪圖需要的資訊存起來
            self.ui_items.append({
                "button": btn,
                "name": loc["name"],
                "rect": container_rect
            })

    def on_location_selected(self, location_data):
        target_name = location_data["name"]
        target_map = location_data["map"]
        target_pos = location_data["pos"]
        Logger.info(f"Navigation target selected: {target_name} at {target_pos}")
        
        current_map = self.game_manager.current_map_key
        if current_map != target_map:
            Logger.info("Target is in another map, cannot auto-navigate yet.")
            return

        # 呼叫 Player 的導航功能
        if self.game_manager.player:
            self.game_manager.player.start_auto_move(target_pos)
        
        # 關閉視窗，讓玩家看路徑
        self.toggle()

    def update(self, dt: float):
        super().update(dt)
        if not self.is_open: return
        
        # 更新所有按鈕
        for item in self.ui_items:
            item["button"].update(dt)

    def draw(self, screen: pg.Surface):
        self.draw_background(screen)
        if not self.is_open: return

        title_rect = self.title_text.get_rect(center=(self.rect.centerx, self.rect.y + 40))
        screen.blit(self.title_text, title_rect)

        for item in self.ui_items:
            rect = item["rect"]
            name = item["name"]
            btn = item["button"]

            # 繪製底框
            pg.draw.rect(screen, (240, 240, 240), rect, border_radius=10)
            pg.draw.rect(screen, (150, 150, 150), rect, 2, border_radius=10)

            # 繪製文字
            text_surf = self.font_item.render(name, True, (50, 50, 50))
            text_rect = text_surf.get_rect(
                left=rect.x + 20,
                centery=rect.centery
            )
            screen.blit(text_surf, text_rect)

            # 繪製按鈕
            btn.draw(screen)