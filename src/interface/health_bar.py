import pygame as pg

class HealthBar:
    def __init__(self, font_path: str, font_size: int = 24):
        self.font = pg.font.Font(font_path, font_size)
        self.small_font = pg.font.Font(font_path, int(font_size * 0.7))
        
        self.COLOR_BG = (60, 60, 60)      
        self.COLOR_BORDER = (255, 255, 255) 
        self.COLOR_HP_HIGH = (0, 255, 0)  # 綠
        self.COLOR_HP_MID = (255, 255, 0) # 黃
        self.COLOR_HP_LOW = (255, 0, 0)   # 紅

        self.TYPE_COLORS = {
            "grass": (120, 200, 80),   # 綠
            "fire": (240, 128, 48),    # 紅
            "water": (104, 144, 240),  # 藍
        }
        self.DEFAULT_TYPE_COLOR = (160, 160, 160)

    def draw(self, screen: pg.Surface, x: int, y: int, hp: int, max_hp: int, name: str, m_type: str):

        bar_width = 210
        bar_height = 20

        # 底框
        container_width = bar_width + 100
        container_height = 70
        container_rect = pg.Rect(x - 10, y - 40, container_width, container_height)
        pg.draw.rect(screen, (250, 250, 250), container_rect, border_radius=8)
        pg.draw.rect(screen, (40, 40, 40), container_rect, 3, border_radius=8)

        type_color = self.TYPE_COLORS.get(m_type.lower(), self.DEFAULT_TYPE_COLOR)
        
        # 屬性
        type_text_surf = self.small_font.render(m_type.upper(), True, (255, 255, 255))
        type_w = type_text_surf.get_width() + 10
        type_h = type_text_surf.get_height() + 4
        
        type_rect = pg.Rect(x, y - 32, type_w, type_h)
        pg.draw.rect(screen, type_color, type_rect, border_radius=4)
        pg.draw.rect(screen, (0, 0, 0), type_rect, 1, border_radius=4)
        
        text_x = type_rect.centerx - type_text_surf.get_width() // 2
        text_y = type_rect.centery - type_text_surf.get_height() // 2
        screen.blit(type_text_surf, (text_x, text_y))

        # 名字 
        name_text = self.font.render(f"{name}", True, (40, 40, 40))
        screen.blit(name_text, (x + type_w + 5, y - 30))
        
        # 計算血量百分比，避免分母為 0
        if max_hp <= 0: max_hp = 1
        ratio = hp / max_hp
        ratio = max(0.0, min(1.0, ratio))
        
        fill_width = int(bar_width * ratio)
        
        # 顏色根據血量決定
        color = self.COLOR_HP_HIGH
        if ratio < 0.5: color = self.COLOR_HP_MID
        if ratio < 0.2: color = self.COLOR_HP_LOW
        
        pg.draw.rect(screen, self.COLOR_BG, (x, y, bar_width, bar_height), border_radius=4)
        pg.draw.rect(screen, color, (x, y, fill_width, bar_height), border_radius=4)
        pg.draw.rect(screen, self.COLOR_BORDER, (x, y, bar_width, bar_height), 2, border_radius=4)
        
        # 血量數值
        hp_text = self.font.render(f"{int(hp)}/{int(max_hp)}", True, (0, 0, 0))
        screen.blit(hp_text, (x + bar_width + 8, y - 2))