import pygame as pg
from src.utils import GameSettings
from src.interface.components import Button

class BattleDashboard:
    def __init__(self, font: pg.font.Font, on_fight, on_switch, on_run, on_catch):
        self.font = font
        
        # 儀表板
        self.height = 140
        self.rect = pg.Rect(
            0, 
            GameSettings.SCREEN_HEIGHT - self.height, 
            GameSettings.SCREEN_WIDTH, 
            self.height
        )

        # 按鈕共用參數
        btn_width, btn_height = 150, 50
        btn_y = self.rect.centery - (btn_height // 2)
        
        # 按鈕圖片路徑
        img_normal = "UI/raw/UI_Flat_Button02a_3.png"
        img_hover = "UI/raw/UI_Flat_Button02a_1.png"

        # Fight
        self.btn_fight = Button(
            img_normal, img_hover, 
            100, btn_y, btn_width, btn_height, 
            on_click=on_fight
        )
        
        # Switch
        self.btn_switch = Button(
            img_normal, img_hover, 
            300, btn_y, btn_width, btn_height, 
            on_click=on_switch
        )
        
        # Run
        self.btn_run = Button(
            img_normal, img_hover, 
            500, btn_y, btn_width, btn_height, 
            on_click=on_run
        )

        # Catch
        self.show_catch = False
        self.btn_catch = Button(
            img_normal, img_hover, 
            700, btn_y, btn_width, btn_height, 
            on_click=on_catch
        )

    def show_catch_button(self, show: bool):
        self.show_catch = show

    def update(self, dt: float):
        self.btn_fight.update(dt)
        self.btn_switch.update(dt)
        self.btn_run.update(dt)

        if self.show_catch:
            self.btn_catch.update(dt)

    def draw(self, screen: pg.Surface):
        # 背景框
        pg.draw.rect(screen, (40, 40, 40), self.rect)
        pg.draw.rect(screen, (255, 255, 255), self.rect, 3)

        # 按鈕
        self.btn_fight.draw(screen)
        self.btn_switch.draw(screen)
        self.btn_run.draw(screen)

        if self.show_catch:
            self.btn_catch.draw(screen)

        # 按鈕文字
        self._draw_text(screen, "Fight", self.btn_fight)
        self._draw_text(screen, "Switch", self.btn_switch)
        self._draw_text(screen, "Run", self.btn_run)

        if self.show_catch:
            self._draw_text(screen, "Catch", self.btn_catch)

    # 輔助函式：將文字置中畫在按鈕上
    def _draw_text(self, screen, text, button):
        txt_surf = self.font.render(text, True, (0, 0, 0))
        rect = getattr(button, 'hitbox', button.hitbox)
        txt_rect = txt_surf.get_rect(center=rect.center)
        screen.blit(txt_surf, txt_rect)