'''check point 2 - 1: Overlay'''

import pygame as pg
from src.interface.windows.window import Window
from src.interface.components import Button
from src.core.services import scene_manager

class MenuWindow(Window):
    def __init__(self, game_manager, font_title):
        super().__init__(game_manager, 600, 500)
        self.font_title = font_title
        
        self.font_item = pg.font.Font("././assets/fonts/Minecraft.ttf", 20)

        # 回到主選單按鈕
        btn_w, btn_h = 60, 60
        self.home_button = Button(
            "UI/button_play.png",   
            "UI/button_play_hover.png", 
            self.rect.centerx - btn_w // 2, 
            self.rect.centery - 30, 
            btn_w, btn_h,
            on_click=lambda: scene_manager.change_scene("menu")
        )
        
        self.text_home = self.font_item.render("To Menu", True, (0, 0, 0))

    def update(self, dt: float):
        if not self.is_open: 
            return
        super().update(dt)
        self.home_button.update(dt)

    def draw(self, screen: pg.Surface):
        if not self.is_open: 
            return

        super().draw_background(screen)

        text_surface = self.font_title.render("Menu", True, (0, 0, 0))
        text_rect = text_surface.get_rect(center=(self.rect.centerx, self.rect.top + 60))
        screen.blit(text_surface, text_rect)

        self.home_button.draw(screen)

        label_rect = self.text_home.get_rect(center=(self.rect.centerx, self.home_button.hitbox.bottom + 15))
        screen.blit(self.text_home, label_rect)