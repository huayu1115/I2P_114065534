'''check point 2 - 1: Overlay'''

import pygame as pg
from src.interface.windows.window import Window

class MenuWindow(Window):
    def __init__(self, game_manager, font_title):
        super().__init__(game_manager, 600, 500)
        self.font_title = font_title

    def update(self, dt: float):
        if not self.is_open: 
            return

        super().update(dt)

    def draw(self, screen: pg.Surface):
        if not self.is_open: 
            return

        super().draw_background(screen)

        text_surface = self.font_title.render("Menu", True, (0, 0, 0))
        text_rect = text_surface.get_rect(center=(self.rect.centerx, self.rect.top + 60))
        screen.blit(text_surface, text_rect)