import pygame as pg
from src.utils import GameSettings
from src.interface.components import Button

class BattleDashboard:
    def __init__(self, font: pg.font.Font, on_fight, on_switch, on_run, on_heal, on_power, on_def, on_catch):
        self.font = font
        
        # 儀表板
        self.height = 140
        self.rect = pg.Rect(
            0, 
            GameSettings.SCREEN_HEIGHT - self.height, 
            GameSettings.SCREEN_WIDTH, 
            self.height
        )

        self.menu_state = 'MAIN'

        # 按鈕共用參數
        btn_width, btn_height = 150, 50
        btn_y = self.rect.centery - (btn_height // 2)
        
        # 按鈕圖片路徑
        img_normal = "UI/raw/UI_Flat_Button02a_3.png"
        img_hover = "UI/raw/UI_Flat_Button02a_1.png"

        # Fight
        self.btn_fight = Button(img_normal, img_hover, 50, btn_y, btn_width, btn_height, on_click=on_fight)
        
        # Bag 
        self.btn_bag = Button(img_normal, img_hover, 220, btn_y, btn_width, btn_height, on_click=self.open_bag_menu)

        # Switch
        self.btn_switch = Button(img_normal, img_hover, 390, btn_y, btn_width, btn_height, on_click=on_switch)
        
        # Run
        self.btn_run = Button(img_normal, img_hover, 560, btn_y, btn_width, btn_height, on_click=on_run)

        # Catch
        self.show_catch = False
        self.btn_catch = Button(img_normal, img_hover, 730, btn_y, btn_width, btn_height, on_click=on_catch)


        # 恢復藥水
        self.btn_heal = Button(img_normal, img_hover, 100, btn_y, btn_width, btn_height, on_click=on_heal)
        # 力量藥水
        self.btn_power = Button(img_normal, img_hover, 300, btn_y, btn_width, btn_height, on_click=on_power)
        # 防禦藥水
        self.btn_def = Button(img_normal, img_hover, 500, btn_y, btn_width, btn_height, on_click=on_def)
        # 返回主選單
        self.btn_back = Button(img_normal, img_hover, 700, btn_y, btn_width, btn_height, on_click=self.back_to_main)

    def show_catch_button(self, show: bool):
        self.show_catch = show

    def open_bag_menu(self):
        self.menu_state = 'BAG'

    def back_to_main(self):
        self.menu_state = 'MAIN'

    def update(self, dt: float):
        if self.menu_state == 'MAIN':
            self.btn_fight.update(dt)
            self.btn_bag.update(dt)
            self.btn_switch.update(dt)
            self.btn_run.update(dt)
            if self.show_catch:
                self.btn_catch.update(dt)
        
        elif self.menu_state == 'BAG':
            self.btn_heal.update(dt)
            self.btn_power.update(dt)
            self.btn_def.update(dt)
            self.btn_back.update(dt)

    def draw(self, screen: pg.Surface):
        if self.menu_state == 'MAIN':
            # 畫主選單按鈕
            self.btn_fight.draw(screen)
            self.btn_bag.draw(screen)
            self.btn_switch.draw(screen)
            self.btn_run.draw(screen)
            
            self._draw_text(screen, "Fight", self.btn_fight)
            self._draw_text(screen, "Bag", self.btn_bag)
            self._draw_text(screen, "Monsters", self.btn_switch)
            self._draw_text(screen, "Run", self.btn_run)

            if self.show_catch:
                self.btn_catch.draw(screen)
                self._draw_text(screen, "Catch", self.btn_catch)

        elif self.menu_state == 'BAG':
            # 畫背包選單按鈕
            self.btn_heal.draw(screen)
            self.btn_power.draw(screen)
            self.btn_def.draw(screen)
            self.btn_back.draw(screen)

            self._draw_text(screen, "Heal Potion", self.btn_heal)
            self._draw_text(screen, "Str Potion", self.btn_power)
            self._draw_text(screen, "Def Potion", self.btn_def)
            self._draw_text(screen, "Back", self.btn_back)

    # 輔助函式：將文字置中畫在按鈕上
    def _draw_text(self, screen, text, button):
        txt_surf = self.font.render(text, True, (0, 0, 0))
        rect = getattr(button, 'hitbox', button.hitbox)
        txt_rect = txt_surf.get_rect(center=rect.center)
        screen.blit(txt_surf, txt_rect)