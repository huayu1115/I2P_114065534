import pygame as pg
from src.interface.windows.window import Window
from src.interface.components import Button
from src.utils import GameSettings, Logger
from src.core.services import sound_manager
from src.core import GameManager

class SettingWindow(Window):
    def __init__(self, game_manager: GameManager, font_title: pg.font.Font, font_item: pg.font.Font, on_game_reload_callback):
        """
        on_game_reload_callback: 當讀檔成功時呼叫的函式，用來更新 GameScene 的 manager
        """
        super().__init__(game_manager, 600, 500)
        
        self.font_title = font_title
        self.font_item = font_item
        self.on_game_reload_callback = on_game_reload_callback
        
        self.is_muted = False 

        # 標題與文字
        self.text_title = self.font_title.render("Settings", True, (0, 0, 0))
        self.text_volume_label = self.font_item.render("Volume", True, (0, 0, 0))
        self.text_save_label = self.font_item.render("Save", True, (0, 0, 0))
        self.text_load_label = self.font_item.render("Load ", True, (0, 0, 0))

        # 靜音按鈕
        btn_x = self.rect.centerx - 60
        btn_y = self.rect.centery - 50
        btn_w, btn_h = 40, 25

        self.mute_button_off = Button(
            "UI/raw/UI_Flat_ToggleRightOff01a.png",
            "UI/raw/UI_Flat_ToggleRightOff01a.png",
            btn_x, btn_y, btn_w, btn_h,
            on_click=self.toggle_mute
        )

        self.mute_button_on = Button(
            "UI/raw/UI_Flat_ToggleRightOn01a.png",
            "UI/raw/UI_Flat_ToggleRightOn01a.png",   
            btn_x, btn_y, btn_w, btn_h,
            on_click=self.toggle_mute
        )

        # 音量條
        bar_width, bar_height = 300, 20
        bar_x = self.rect.centerx - bar_width // 2
        bar_y = (self.rect.centery) - 100
        self.volume_bar_rect = pg.Rect(bar_x, bar_y, bar_width, bar_height)

        # 滑桿
        self.handle_size = 20
        self.volume_handle_rect = pg.Rect(0, 0, self.handle_size, self.handle_size) 
        self._update_handle_pos() # 根據目前音量設定初始位置

        # 存檔、讀檔
        self.save_button = Button(
            "UI/button_load.png",
            "UI/button_load_hover.png",
            self.rect.centerx - 85,
            self.rect.centerx - 100,
            35, 35,
            on_click=self.save_game
        ) 
        self.load_button = Button(
            "UI/button_load.png",
            "UI/button_load_hover.png",
            self.rect.centerx + 25,
            self.rect.centerx - 100,
            35, 35,
            on_click=self.load_game
        )

    ## 更新滑桿位置
    def _update_handle_pos(self):
        handle_x = self.volume_bar_rect.x + int(GameSettings.AUDIO_VOLUME * self.volume_bar_rect.width) - self.handle_size // 2
        handle_y = self.volume_bar_rect.centery - self.handle_size // 2
        self.volume_handle_rect.topleft = (handle_x, handle_y)

    def toggle_mute(self):
        if self.is_muted:
            self.is_muted = False
            sound_manager.resume_all()  
        else:
            self.is_muted = True
            sound_manager.pause_all() 

    def save_game(self):
        save_path = "saves/game0.json"
        self.game_manager.save(save_path)
        Logger.info(f"Game saved to {save_path}")

    def load_game(self):
        save_path = "saves/game0.json"
        new_manager = GameManager.load(save_path)
        
        if new_manager:
            self.game_manager = new_manager
            ## 通知 GameScene 更新 manager !!!
            if self.on_game_reload_callback:
                self.on_game_reload_callback(new_manager)
            Logger.info("Game Reloaded!")
        else:
            Logger.error("Save file not found!")

    def update(self, dt: float):
        super().update(dt)
        
        if not self.is_open:
            return

        self.save_button.update(dt)
        self.load_button.update(dt)
        
        if self.is_muted:
            self.mute_button_on.update(dt)
        else:
            self.mute_button_off.update(dt)

        # 音量條邏輯
        if pg.mouse.get_pressed()[0]:  
            mx, my = pg.mouse.get_pos()
            
            detect_rect = self.volume_bar_rect.inflate(20, 20) # 擴大判定範圍比較好拉動
            if detect_rect.collidepoint(mx, my):
                # 計算音量比例
                ratio = (mx - self.volume_bar_rect.x) / self.volume_bar_rect.width
                ratio = max(0, min(1, ratio))
                
                # 更新設定
                GameSettings.AUDIO_VOLUME = ratio
                if sound_manager.current_bgm:
                    sound_manager.current_bgm.set_volume(ratio)
                
                # 更新滑桿位置
                self._update_handle_pos()

    def draw(self, screen: pg.Surface):

        self.draw_background(screen)
        
        if not self.is_open:
            return

        # 標題
        text_rect = self.text_title.get_rect(center=(self.rect.centerx, self.rect.top + 80))
        screen.blit(self.text_title, text_rect)

        # 音量區塊
        text_rect = self.text_volume_label.get_rect(center=(self.rect.centerx - 120, self.volume_bar_rect.y - 20))
        screen.blit(self.text_volume_label, text_rect)
        
        # 數值
        volume_text = self.font_item.render(f"{int(GameSettings.AUDIO_VOLUME * 100)}%", True, (50, 50, 50))
        screen.blit(volume_text, (self.rect.centerx + 200, self.volume_bar_rect.y))

        # 音量條
        pg.draw.rect(screen, (204, 102, 0), self.volume_bar_rect)  
        fill_width = int(self.volume_bar_rect.width * GameSettings.AUDIO_VOLUME)
        pg.draw.rect(screen, (255, 178, 102), (self.volume_bar_rect.x, self.volume_bar_rect.y, fill_width, self.volume_bar_rect.height))
        # 滑桿
        pg.draw.rect(screen, (255, 255, 255), self.volume_handle_rect)
        pg.draw.rect(screen, (0, 0, 0), self.volume_handle_rect, 2)

        # 靜音按鈕
        if self.is_muted:
            self.mute_button_on.draw(screen)
        else:
            self.mute_button_off.draw(screen)
        
        status_text = f"Mute: {'ON' if self.is_muted else 'OFF'}"
        text_surface = self.font_item.render(status_text, True, (0, 0, 0))
        text_rect = text_surface.get_rect(center=(self.rect.centerx - 110, self.rect.centery - 40))
        screen.blit(text_surface, text_rect)

        # 存讀檔區塊
        self.save_button.draw(screen)
        self.load_button.draw(screen)
        
        save_label_rect = self.text_save_label.get_rect(center=(self.save_button.hitbox.centerx, self.save_button.hitbox.bottom + 15))
        screen.blit(self.text_save_label, save_label_rect)
        
        load_label_rect = self.text_load_label.get_rect(center=(self.load_button.hitbox.centerx, self.load_button.hitbox.bottom + 15))
        screen.blit(self.text_load_label, load_label_rect)