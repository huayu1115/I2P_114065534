import pygame as pg
from src.interface.windows.window import Window
from src.interface.components import Button
from src.core import GameManager
from src.utils import GameSettings, Logger, load_img 

class ShopWindow(Window):
    def __init__(self, game_manager: GameManager, font_title: pg.font.Font, font_item: pg.font.Font):
        super().__init__(game_manager, 600, 500) 
        self.font_title = font_title
        self.font_item = font_item
        
        self.merchant_goods = []
        self.action_buttons = []
        self.mode = "BUY"
        
        # 圖片快取，避免重複讀取硬碟
        self.sprite_cache = {}

        # 頁面排版設定
        self.columns = 2
        self.item_height = 80
        self.gap_x = 15
        self.gap_y = 15

        # 標籤按鈕 (Buy / Sell)
        btn_width, btn_height = 80, 30
        img_normal = "UI/raw/UI_Flat_Button02a_3.png"
        img_hover = "UI/raw/UI_Flat_Button02a_1.png"

        self.btn_tab_buy = Button(
            img_normal, img_hover,
            self.rect.x + 50, self.rect.y + 60,
            btn_width, btn_height,
            on_click=lambda: self.switch_mode("BUY")
        )

        self.btn_tab_sell = Button(
            img_normal, img_hover,
            self.rect.x + 140, self.rect.y + 60,
            btn_width, btn_height,
            on_click=lambda: self.switch_mode("SELL")
        )

    # 獲取快取圖片
    def get_cached_sprite(self, path: str, size: int):
        if not path: return None
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

    def setup_shop(self, goods: list[dict]):
        self.merchant_goods = goods
        self.switch_mode("BUY")
        if not self.is_open:
            self.toggle()

    def switch_mode(self, mode: str):
        self.mode = mode
        self.refresh_items()

    def refresh_items(self):
        '''根據當前模式重新生成按鈕，並計算網格位置'''
        self.action_buttons.clear()
        
        # 決定顯示的列表
        if self.mode == "BUY":
            display_list = self.merchant_goods
            btn_img = "UI/button_shop.png"
            btn_hover_img = "UI/button_shop_hover.png"
            action_func = self.buy_item
        else:
            bag_data = self.game_manager.bag._items_data
            display_list = [item for item in bag_data if item["name"] != "Coins"]
            btn_img = "UI/button_shop.png"
            btn_hover_img = "UI/button_shop_hover.png"
            action_func = self.sell_item

        # 網格計算參數
        start_x = self.rect.x + 30
        start_y = self.rect.y + 110
        # 計算寬度: (總寬 - 兩邊留白 - 中間間隔) / 2
        card_width = (self.rect.width - 60 - self.gap_x) // self.columns
        
        # 生成按鈕
        for i, item in enumerate(display_list):
            # 計算網格座標
            col = i % self.columns
            row = i // self.columns
            
            item_x = start_x + col * (card_width + self.gap_x)
            item_y = start_y + row * (self.item_height + self.gap_y)
            
            # 按鈕位置
            btn_size = 35
            btn_x = item_x + card_width - btn_size - 10
            btn_y = item_y + (self.item_height - btn_size) // 2
            
            # 建立按鈕
            btn = Button(
                btn_img,
                btn_hover_img,
                btn_x, btn_y,
                btn_size, btn_size,
                on_click=lambda target=item: action_func(target)
            )
            self.action_buttons.append(btn)

    def get_item_price(self, item_name: str) -> int:
        for key, data in self.game_manager.item_database.items():
            if data["name"] == item_name:
                return data.get("price", 1)
        return 0

    def buy_item(self, item_data: dict):
        price = item_data.get("price", 0)
        name = item_data.get("name", "Unknown")
        
        bag_items = self.game_manager.bag._items_data
        coins_item = next((i for i in bag_items if i["name"] == "Coins"), None)
        current_money = coins_item["count"] if coins_item else 0  
        
        if current_money >= price:
            if coins_item:
                coins_item["count"] -= price 
            
            existing_item = next((i for i in bag_items if i["name"] == name), None)
            if existing_item:
                existing_item["count"] = existing_item.get("count", 1) + 1
            else:
                new_item = item_data.copy()
                new_item["count"] = 1
                if "price" in new_item: del new_item["price"]
                bag_items.append(new_item)
            
            Logger.info(f"Bought {name} for {price}.")
        else:
            Logger.info("Not enough money!")

    def sell_item(self, item_data: dict):
        name = item_data.get("name", "Unknown")
        original_price = self.get_item_price(name)
        sell_price = original_price // 2
        if sell_price <= 0: sell_price = 1
            
        bag_items = self.game_manager.bag._items_data
        coins_item = next((i for i in bag_items if i["name"] == "Coins"), None)
        
        if coins_item:
            coins_item["count"] += sell_price
        else: 
            bag_items.append({"name": "Coins", "count": sell_price, "sprite_path": "ingame_ui/coin.png"})

        if item_data["count"] > 1:
            item_data["count"] -= 1
        else:
            bag_items.remove(item_data)
            self.refresh_items() # 物品沒了要重整清單

        Logger.info(f"Sold {name} for {sell_price}.")

    def update(self, dt: float):
        if not self.is_open: return
        super().update(dt)
        self.btn_close.update(dt)
        self.btn_tab_buy.update(dt)
        self.btn_tab_sell.update(dt)
        
        for btn in self.action_buttons:
            btn.update(dt)

    def draw(self, screen: pg.Surface):
        if not self.is_open: return
        self.draw_background(screen)

        # 標題
        title_text = f"Shop - {self.mode}"
        title = self.font_title.render(title_text, True, (0, 0, 0))
        screen.blit(title, (self.rect.centerx - title.get_width()//2 + 50, self.rect.y + 40))

        # 繪製分頁按鈕
        self.btn_tab_buy.draw(screen)
        self.btn_tab_sell.draw(screen)
        self._draw_text(screen, "Buy", self.btn_tab_buy)
        self._draw_text(screen, "Sell", self.btn_tab_sell)

        # 顯示金錢
        bag_items = self.game_manager.bag._items_data
        coins = next((i for i in bag_items if i["name"] == "Coins"), None)
        money_val = coins["count"] if coins else 0
        money_surf = self.font_item.render(f"Coins: ${money_val}", True, (255, 215, 0))
        screen.blit(money_surf, (self.rect.x + 40, self.rect.bottom - 40))

        # 繪製網格列表內容
        start_x = self.rect.x + 30
        start_y = self.rect.y + 110
        card_width = (self.rect.width - 60 - self.gap_x) // self.columns

        if self.mode == "BUY":
            display_list = self.merchant_goods
        else:
            display_list = [item for item in self.game_manager.bag._items_data if item["name"] != "Coins"]

        for i, item in enumerate(display_list):
            # 計算位置
            col = i % self.columns
            row = i // self.columns
            x = start_x + col * (card_width + self.gap_x)
            y = start_y + row * (self.item_height + self.gap_y)
            
            # 繪製底框
            bg_rect = pg.Rect(x, y, card_width, self.item_height)
            pg.draw.rect(screen, (225, 225, 225), bg_rect, border_radius=8)
            pg.draw.rect(screen, (100, 100, 100), bg_rect, 2, border_radius=8)

            # 顯示圖片
            icon_size = 50
            icon_x = x + 10
            icon_y = y + (self.item_height - icon_size) // 2
            
            sprite_path = item.get("sprite_path")
            if sprite_path:
                image = self.get_cached_sprite(sprite_path, icon_size)
                if image:
                    screen.blit(image, (icon_x, icon_y))
            else:
                pg.draw.rect(screen, (180, 180, 180), (icon_x, icon_y, icon_size, icon_size))

            # 顯示文字
            name = item.get("name", "Unknown")
            count = item.get("count", 1)
            text_x = icon_x + icon_size + 10
            
            name_surf = self.font_item.render(name, True, (0, 0, 0))
            screen.blit(name_surf, (text_x, y + 15))

            if self.mode == "BUY":
                price = item.get("price", 0)
                price_surf = self.font_item.render(f"${price}", True, (200, 50, 50)) # 紅色價格
                screen.blit(price_surf, (text_x, y + 40))
            else:
                # 賣出模式顯示持有量與賣價
                original_price = self.get_item_price(name)
                sell_price = original_price // 2
                
                info_text = f"Have: {count}"
                info_surf = self.font_item.render(info_text, True, (80, 80, 80))
                screen.blit(info_surf, (text_x, y + 35))
                
                sell_text = f"Sell: ${sell_price}"
                sell_surf = self.font_item.render(sell_text, True, (50, 150, 50)) # 綠色賣價
                screen.blit(sell_surf, (text_x, y + 55))

        # 繪製所有按鈕
        for btn in self.action_buttons:
            btn.draw(screen)

    def _draw_text(self, screen, text, button):
        txt_surf = self.font_item.render(text, True, (0, 0, 0))
        rect = getattr(button, 'hitbox', button.hitbox)
        txt_rect = txt_surf.get_rect(center=rect.center)
        screen.blit(txt_surf, txt_rect)