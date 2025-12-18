import pygame as pg

class HealthBar:
    def __init__(self, font_path: str, font_size: int = 24):
        self.font = pg.font.Font(font_path, font_size)
        
        self.COLOR_BG = (60, 60, 60)      
        self.COLOR_BORDER = (255, 255, 255) 
        self.COLOR_HP_HIGH = (0, 255, 0)  # 綠
        self.COLOR_HP_MID = (255, 255, 0) # 黃
        self.COLOR_HP_LOW = (255, 0, 0)   # 紅

    def draw(self, screen: pg.Surface, x: int, y: int, hp: int, max_hp: int, name: str):

        bar_width = 200
        bar_height = 20
        
        # 計算血量百分比，避免分母為 0
        if max_hp <= 0: max_hp = 1
        ratio = hp / max_hp
        ratio = max(0.0, min(1.0, ratio))
        
        fill_width = int(bar_width * ratio)
        
        # 顏色根據血量決定
        color = self.COLOR_HP_HIGH
        if ratio < 0.5: color = self.COLOR_HP_MID
        if ratio < 0.2: color = self.COLOR_HP_LOW
        
        pg.draw.rect(screen, self.COLOR_BG, (x, y, bar_width, bar_height))
        pg.draw.rect(screen, color, (x, y, fill_width, bar_height))
        pg.draw.rect(screen, self.COLOR_BORDER, (x, y, bar_width, bar_height), 2)

        # 名字
        name_text = self.font.render(f"{name}", True, (0, 0, 0))
        screen.blit(name_text, (x, y - 30))
        
        # 血量數值
        hp_text = self.font.render(f"{int(hp)}/{int(max_hp)}", True, (0, 0, 0))
        screen.blit(hp_text, (x + bar_width + 10, y))