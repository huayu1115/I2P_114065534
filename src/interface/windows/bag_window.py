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
        self.items_per_page = 6
        self.item_height = 55 
        self.current_item_page = 0
        self.current_monster_page = 0

        self.btn_item_prev = Button(
            "UI/button_back.png",
            "UI/button_back_hover.png",
            self.rect.centerx - 185, self.rect.bottom - 50,
            35, 35,
            on_click=self.prev_item_page
        )
        
        self.btn_item_next = Button(
            "UI/button_play.png",
            "UI/button_play_hover.png",
            self.rect.centerx - 160, self.rect.bottom - 50,
            35, 35,
            on_click=self.next_item_page
        )

        self.btn_monster_prev = Button(
            "UI/button_back.png",
            "UI/button_back_hover.png",
            self.rect.centerx + 110, self.rect.bottom - 50,
            35, 35,
            on_click=self.prev_monster_page
        )
        
        self.btn_monster_next = Button(
            "UI/button_play.png",
            "UI/button_play_hover.png",
            self.rect.centerx + 135, self.rect.bottom - 50,
            35, 35,
            on_click=self.next_monster_page
        )

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
                surf = pg.Surface((size, size)) # 產生一個替代用的色塊
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

        # 繪製物品 (包含格子)
        for i, item in enumerate(page_items):
            # 計算統一的 Y 座標
            base_y = self.rect.y + 120 + (i * self.item_height)
            
            # 1. 畫格子 (寬度設稍微窄一點 220，區分左右)
            bg_rect = pg.Rect(self.rect.x + 30, base_y, 220, 50)
            pg.draw.rect(screen, (255, 255, 255), bg_rect, border_radius=5) # 白底
            pg.draw.rect(screen, (100, 100, 100), bg_rect, 2, border_radius=5) # 灰框

            # 2. 準備資料
            item_name = item.get("name", "Unknown")
            item_count = item.get("count", 1)
            sprite_path = item.get("sprite_path", None)

            # 3. 畫 Icon
            icon_size = 35
            icon_x = self.rect.x + 40
            icon_y_offset = (50 - icon_size) // 2
            
            if sprite_path:
                image = self.get_cached_sprite(sprite_path, icon_size)
                screen.blit(image, (icon_x, base_y + icon_y_offset))
            else:
                # 沒圖就畫個小方塊代替
                pg.draw.rect(screen, (200, 200, 200), (icon_x, base_y + icon_y_offset, icon_size, icon_size))

            # 4. 畫文字
            text_x = icon_x + icon_size + 10
            text_surf = self.font_item.render(f"{item_name} x{item_count}", True, (0, 0, 0))
            # 垂直置中文字
            text_rect = text_surf.get_rect(midleft=(text_x, base_y + 25))
            screen.blit(text_surf, text_rect)

        # 繪製物品翻頁按鈕
        if self.current_item_page > 0:
            self.btn_item_prev.draw(screen)
        if total_items > 0 and self.current_item_page < max_item_page:
            self.btn_item_next.draw(screen)


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
            bg_rect = pg.Rect(self.rect.centerx + 20, base_y, 250, 50)
            pg.draw.rect(screen, (255, 255, 255), bg_rect, border_radius=5)
            pg.draw.rect(screen, (100, 100, 100), bg_rect, 2, border_radius=5)

            # 資料
            m_name = monster.get("name")
            db_data = self.game_manager.monster_database.get(m_name, {})
            sprite_path = db_data.get("sprite_path", None)
            m_level = monster.get("level", 1)
            m_hp = monster.get("hp")
            base_hp = db_data.get("base_hp", 40)
            m_max = Monster.calculate_max_hp(base_hp, m_level)
            if m_hp > m_max: m_hp = m_max
            if m_hp < 0: m_hp = 0

            # Icon
            icon_size = 35
            icon_x = self.rect.centerx + 25
            icon_y_offset = (50 - icon_size) // 2
            
            if sprite_path:
                image = self.get_cached_sprite(sprite_path, icon_size)
                screen.blit(image, (icon_x, base_y + icon_y_offset))
            else:
                pg.draw.rect(screen, (200, 200, 200), (icon_x, base_y + icon_y_offset, icon_size, icon_size))

            # 文字
            text_x = icon_x + icon_size + 10
        
            name_surf = self.font_item.render(f"Lv.{m_level} {m_name}", True, (0, 0, 0))
            screen.blit(name_surf, (text_x, base_y + 5))

            hp_color = (200, 50, 50) if m_hp < m_max * 0.2 else (0, 0, 0)
            hp_surf = self.font_item.render(f"HP: {m_hp}/{m_max}", True, hp_color)
            screen.blit(hp_surf, (text_x, base_y + 25))

        # 繪製怪獸翻頁按鈕
        if self.current_monster_page > 0:
            self.btn_monster_prev.draw(screen)
        if total_monsters > 0 and self.current_monster_page < max_monster_page:
            self.btn_monster_next.draw(screen)