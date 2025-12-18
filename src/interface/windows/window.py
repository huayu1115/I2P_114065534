import pygame as pg
from src.utils import GameSettings
from src.interface.components import Button

'''
check point 2: Overlay
建立父類別 window 處理共通的外觀、功能
'''

class Window:
    def __init__(self, game_manager, width: int, height: int):
        self.game_manager = game_manager
        self.is_open = False
        
        # 計算置中位置
        screen_w = GameSettings.SCREEN_WIDTH
        screen_h = GameSettings.SCREEN_HEIGHT
        self.rect = pg.Rect(
            (screen_w - width) // 2,
            (screen_h - height) // 2,
            width, height
        )

        # 關閉按鈕
        self.btn_close = Button(
            "UI/button_x.png", 
            "UI/button_x_hover.png",
            self.rect.right - 45,
            self.rect.top + 10,
            35, 35,
            on_click=self.close
        )

    # 共通方法
    def toggle(self):
        self.is_open = not self.is_open

    def close(self):
        self.is_open = False
        
    def open(self):
        self.is_open = True

    def update(self, dt: float):
        if self.is_open:
            self.btn_close.update(dt)

    def draw_background(self, screen: pg.Surface):
        if not self.is_open: 
            return

        # 半透明遮罩
        overlay = pg.Surface(screen.get_size(), pg.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))

        # 視窗底圖
        pg.draw.rect(screen, (255, 153, 51), self.rect)
        pg.draw.rect(screen, (255, 178, 102), self.rect, 10) # 邊框

        # 關閉按鈕
        self.btn_close.draw(screen)