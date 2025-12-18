import pygame as pg
from src.interface.windows.window import Window
from src.interface.components import Button
from src.core import GameManager
from src.utils import GameSettings, Logger

class ShopWindow(Window):
    def __init__(self, game_manager: GameManager, font_title: pg.font.Font, font_item: pg.font.Font):
        super().__init__(game_manager, 600, 500) 
        self.font_title = font_title
        self.font_item = font_item
        
        self.merchant_goods = []
        self.action_buttons = []
        self.mode = "BUY"

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

    def setup_shop(self, goods: list[dict]):
        '''每次與商人對話時呼叫此函式'''
        self.merchant_goods = goods
        self.switch_mode("BUY")
        if not self.is_open:
            self.toggle()

    def switch_mode(self, mode: str):
        self.mode = mode
        self.refresh_items()

    def refresh_items(self):
        '''根據當前模式重新生成列表與按鈕'''
        self.action_buttons.clear()
        start_y = self.rect.y + 110
        
        # 買模式 or 賣模式 (排除 Coins)
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

        # 生成列表按鈕
        for i, item in enumerate(display_list):
            btn = Button(
                btn_img,
                btn_hover_img,
                self.rect.right - 100, start_y + (i * 45),
                30, 30,
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
        
        # 檢查金錢是否足夠
        bag_items = self.game_manager.bag._items_data
        coins_item = next((i for i in bag_items if i["name"] == "Coins"), None)
        current_money = coins_item["count"] if coins_item else 0  
        if current_money >= price:
            if coins_item:
                coins_item["count"] -= price 
            
            # 加物品到背包 (檢查是否已擁有)
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
        
        # 計算賣價: 原價的一半
        original_price = self.get_item_price(name)
        sell_price = original_price // 2
        
        if sell_price <= 0:
            sell_price = 1
            
        # 增加金錢
        bag_items = self.game_manager.bag._items_data
        coins_item = next((i for i in bag_items if i["name"] == "Coins"), None)
        if coins_item:
            coins_item["count"] += sell_price
        else: # 如果背包沒錢，新增一筆
            bag_items.append({"name": "Coins", "count": sell_price, "sprite_path": "ingame_ui/coin.png"})

        # 扣除物品數量
        if item_data["count"] > 1:
            item_data["count"] -= 1
        else:
            bag_items.remove(item_data) # 數量歸零，從背包移除
            self.refresh_items() 

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
        screen.blit(title, (self.rect.centerx - title.get_width()//2+50, self.rect.y + 40))

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

        # 繪製列表內容
        start_y = self.rect.y + 110
        
        # 根據模式決定要繪製的資料
        if self.mode == "BUY":
            display_list = self.merchant_goods
        else:
            display_list = [item for item in self.game_manager.bag._items_data if item["name"] != "Coins"]

        for i, item in enumerate(display_list):
            name = item.get("name", "Unknown")
            count = item.get("count", 1)
            
            # 決定顯示價格
            if self.mode == "BUY":
                price = item.get("price", 0)
                text = f"{name} (${price})"
            else:
                # 賣出價格查詢
                original_price = self.get_item_price(name)
                sell_price = original_price // 2
                text = f"{name} x{count} (Sell: ${sell_price})"

            surf = self.font_item.render(text, True, (255, 255, 255))
            screen.blit(surf, (self.rect.x + 40, start_y + (i * 45) + 5))

        # 繪製列表按鈕
        for btn in self.action_buttons:
            btn.draw(screen)

    def _draw_text(self, screen, text, button):
        txt_surf = self.font_item.render(text, True, (0, 0, 0))
        rect = getattr(button, 'hitbox', button.hitbox)
        txt_rect = txt_surf.get_rect(center=rect.center)
        screen.blit(txt_surf, txt_rect)