'''check point 2 - 3: Backpack Overlay'''
import pygame as pg
from src.interface.windows.window import Window 
from src.interface.components import Button
from src.core import GameManager
from src.utils import load_img, Logger
from src.entities.monster import Monster

class BagWindow(Window):
    def __init__(self, game_manager: GameManager, font_title: pg.font.Font, font_item: pg.font.Font):

        super().__init__(game_manager, 600, 500)
        
        self.font_title = font_title
        self.font_item = font_item

        # 圖片快取字典
        self.sprite_cache = {}

        # 頁面相關
        self.items_per_page = 4
        self.item_height = 80
        self.current_item_page = 0
        self.current_monster_page = 0

        btn_y = self.rect.bottom - 45
        
        self.btn_item_prev = Button(
            "UI/button_back.png", "UI/button_back_hover.png",
            self.rect.centerx - 195, btn_y-10, 35, 35, on_click=self.prev_item_page
        )
        self.btn_item_next = Button(
            "UI/button_play.png", "UI/button_play_hover.png",
            self.rect.centerx - 150, btn_y-10, 35, 35, on_click=self.next_item_page
        )
        self.btn_monster_prev = Button(
            "UI/button_back.png", "UI/button_back_hover.png",
            self.rect.centerx + 100, btn_y-10, 35, 35, on_click=self.prev_monster_page
        )
        self.btn_monster_next = Button(
            "UI/button_play.png", "UI/button_play_hover.png",
            self.rect.centerx + 145, btn_y-10, 35, 35, on_click=self.next_monster_page
        )

        self.TYPE_COLORS = {
           "grass": (120, 200, 80),   # 綠
            "fire": (240, 128, 48),    # 紅
            "water": (104, 144, 240),  # 藍
        }

    # 物品翻頁邏輯 
    def prev_item_page(self):
        if self.current_item_page > 0:
            self.current_item_page -= 1

    def next_item_page(self):
        total = len(self.game_manager.bag._items_data)
        max_page = (total - 1) // self.items_per_page
        if self.current_item_page < max_page:
            self.current_item_page += 1

    # 怪獸翻頁邏輯
    def prev_monster_page(self):
        if self.current_monster_page > 0:
            self.current_monster_page -= 1
            
    def next_monster_page(self):
        total = len(self.game_manager.bag._monsters_data)
        max_page = (total - 1) // self.items_per_page
        if self.current_monster_page < max_page:
            self.current_monster_page += 1

    # 輔助函式：獲取快取圖片
    def get_cached_sprite(self, path: str, size: int):
        if path not in self.sprite_cache:
            try:
                img = load_img(path)
                img = pg.transform.scale(img, (size, size))
                self.sprite_cache[path] = img
            except Exception as e:
                Logger.warning(f"Failed to load sprite {path}: {e}")
                surf = pg.Surface((size, size))
                surf.fill((150, 150, 150))
                self.sprite_cache[path] = surf
        return self.sprite_cache[path]
    
    def update(self, dt: float):
        super().update(dt)
        if not self.is_open: return

        # 更新物品按鈕
        total_items = len(self.game_manager.bag._items_data)
        max_item_page = (total_items - 1) // self.items_per_page
        
        if self.current_item_page > 0:
            self.btn_item_prev.update(dt)
        if total_items > 0 and self.current_item_page < max_item_page:
            self.btn_item_next.update(dt)

        # 更新怪獸按鈕
        total_monsters = len(self.game_manager.bag._monsters_data)
        max_monster_page = (total_monsters - 1) // self.items_per_page
        
        if self.current_monster_page > 0:
            self.btn_monster_prev.update(dt)
        if total_monsters > 0 and self.current_monster_page < max_monster_page:
            self.btn_monster_next.update(dt)
    

    def draw(self, screen: pg.Surface):
        self.draw_background(screen)
        if not self.is_open: return

        title_backpack = self.font_title.render("Backpack", True, (0, 0, 0))
        title_rect = title_backpack.get_rect(centerx=self.rect.centerx, y=self.rect.y + 30)
        screen.blit(title_backpack, title_rect)

        all_items = self.game_manager.bag._items_data
        total_items = len(all_items)
        
        # 物品頁碼計算
        max_item_page = (total_items - 1) // self.items_per_page if total_items > 0 else 0
        item_title_text = f"Items ({self.current_item_page + 1}/{max_item_page + 1})"
        item_title = self.font_item.render(item_title_text, True, (0, 0, 0))
        screen.blit(item_title, (self.rect.x + 50, self.rect.y + 90))

        # 物品切片
        i_start = self.current_item_page * self.items_per_page
        i_end = i_start + self.items_per_page
        page_items = all_items[i_start:i_end]

        ## 繪製物品 ##
        for i, item in enumerate(page_items):
            # 計算統一的 Y 座標
            base_y = self.rect.y + 120 + (i * self.item_height) 
            
            # 底框
            bg_rect = pg.Rect(self.rect.x + 30, base_y, 250, self.item_height - 10)
            pg.draw.rect(screen, (225, 225, 225), bg_rect, border_radius=8)
            pg.draw.rect(screen, (100, 100, 100), bg_rect, 2, border_radius=8)

            item_name = item.get("name", "Unknown")
            item_count = item.get("count", 1)
            sprite_path = item.get("sprite_path", None)

            # Icon
            icon_size = 50
            icon_x = self.rect.x + 45
            icon_y_offset = (bg_rect.height - icon_size) // 2
            
            if sprite_path:
                image = self.get_cached_sprite(sprite_path, icon_size)
                screen.blit(image, (icon_x, base_y + icon_y_offset))
            else:
                pg.draw.rect(screen, (200, 200, 200), (icon_x, base_y + icon_y_offset, icon_size, icon_size))

            # Text
            text_x = icon_x + icon_size + 15
            text_surf = self.font_item.render(f"{item_name}", True, (0, 0, 0))
            count_surf = self.font_item.render(f"x {item_count}", True, (50, 50, 50))
            
            screen.blit(text_surf, (text_x, base_y + 20))
            screen.blit(count_surf, (text_x, base_y + 40))
            
        # 物品翻頁按鈕
        if self.current_item_page > 0: self.btn_item_prev.draw(screen)
        if total_items > 0 and self.current_item_page < max_item_page: self.btn_item_next.draw(screen)

        ## Monsters ##
        all_monsters = self.game_manager.bag._monsters_data
        total_monsters = len(all_monsters)
        
        # 頁碼計算
        max_monster_page = (total_monsters - 1) // self.items_per_page if total_monsters > 0 else 0
        monster_title_text = f"Monsters ({self.current_monster_page + 1}/{max_monster_page + 1})"
        monster_title = self.font_item.render(monster_title_text, True, (0, 0, 0))
        screen.blit(monster_title, (self.rect.centerx + 50, self.rect.y + 90))

        m_start = self.current_monster_page * self.items_per_page
        m_end = m_start + self.items_per_page
        page_monsters = all_monsters[m_start:m_end]

        # 繪製怪獸
        for i, monster in enumerate(page_monsters):
            
            # 格子
            base_y = self.rect.y + 120 + (i * self.item_height)
            bg_rect = pg.Rect(self.rect.centerx + 20, base_y, 260, self.item_height - 10)
            
            pg.draw.rect(screen, (240, 240, 240), bg_rect, border_radius=8)
            pg.draw.rect(screen, (100, 100, 100), bg_rect, 2, border_radius=8)

            # 取得資料
            m_name = monster.get("name")
            db_data = self.game_manager.monster_database.get(m_name, {})
            
            # 讀取屬性與經驗
            m_type = db_data.get("type", "normal") 
            m_exp = monster.get("exp", 0)
            m_level = monster.get("level", 1)

            # 升級所需經驗
            req_exp = (m_level + 1) ** 2
            
            m_hp = monster.get("hp")
            base_hp = db_data.get("base_hp", 40)
            m_max = Monster.calculate_max_hp(base_hp, m_level)
            if m_hp > m_max: m_hp = m_max
            if m_hp < 0: m_hp = 0

            sprite_path = db_data.get("sprite_path", None)

            # Icon
            icon_size = 60 # 放大 Icon
            icon_x = self.rect.centerx + 30
            icon_y_offset = (bg_rect.height - icon_size) // 2
            
            if sprite_path:
                image = self.get_cached_sprite(sprite_path, icon_size)
                screen.blit(image, (icon_x, base_y + icon_y_offset))
            else:
                pg.draw.rect(screen, (200, 200, 200), (icon_x, base_y + icon_y_offset, icon_size, icon_size))

            # 文字
            text_x = icon_x + icon_size + 15
            
            # 等級與名稱
            name_surf = self.font_item.render(f"Lv.{m_level} {m_name}", True, (0, 0, 0))
            screen.blit(name_surf, (text_x, base_y + 10))

            # 血量
            hp_color = (200, 50, 50) if m_hp < m_max * 0.2 else (50, 50, 50)
            hp_surf = self.font_item.render(f"HP: {int(m_hp)}/{m_max}", True, hp_color)
            screen.blit(hp_surf, (text_x, base_y + 30))

            # 屬性
            type_color = self.TYPE_COLORS.get(m_type.lower(), (100, 100, 100))
            type_surf = self.font_item.render(f"[{m_type.upper()}]", True, type_color)
            screen.blit(type_surf, (text_x + hp_surf.get_width() + 10, base_y + 30))

            # 經驗值
            exp_text = f"EXP: {m_exp} / {req_exp}"
            exp_surf = self.font_item.render(exp_text, True, (80, 80, 180)) # 藍紫色字體
            screen.blit(exp_surf, (text_x, base_y + 50))

        # 怪獸翻頁按鈕
        if self.current_monster_page > 0: self.btn_monster_prev.draw(screen)
        if total_monsters > 0 and self.current_monster_page < max_monster_page: self.btn_monster_next.draw(screen)