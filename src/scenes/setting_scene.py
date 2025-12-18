'''
[TODO HACKATHON 5]
Try to mimic the menu_scene.py or game_scene.py to create this new scene
'''
import pygame as pg

from src.utils import GameSettings
from src.sprites import BackgroundSprite
from src.scenes.scene import Scene
from src.interface.components import Button
from src.core.services import scene_manager, sound_manager, input_manager
from typing import override

class SettingScene(Scene):
    background: BackgroundSprite
    panel: pg.Rect
    close_button: Button
    volume_bar_rect: pg.Rect
    volume_handle_rect: pg.Rect
    volume: float

    def __init__(self):
        super().__init__()
        self.background = BackgroundSprite("backgrounds/background1.png")
        self.font_title = pg.font.Font("assets/fonts/Pokemon Solid.ttf", 30)
        self.font = pg.font.Font("././assets/fonts/Minecraft.ttf", 15)
        self.is_muted = False

        ## 文字
        self.text_title = self.font_title.render("Settings", True, (0, 0, 0))
        self.text_volume_label = self.font.render("Volume", True, (0, 0, 0))
        
        ## 面板位置和大小
        panel_width, panel_height = 600, 500
        self.panel = pg.Rect(
            (GameSettings.SCREEN_WIDTH - panel_width) // 2,
            (GameSettings.SCREEN_HEIGHT - panel_height) // 2,
            panel_width,
            panel_height
        )

        self.close_button = Button(
            "UI/button_x.png",
            "UI/button_x_hover.png",
            self.panel.right - 45,
            self.panel.y + 10,
            35, 35,
            on_click = lambda: scene_manager.change_scene("menu")
        )

        ## 靜音按鈕 ##
        btn_x = self.panel.centerx - 60
        btn_y = self.panel.centery - 50
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

        ## 音量條
        bar_width, bar_height = 300, 20
        bar_x = self.panel.centerx - bar_width // 2
        bar_y = (self.panel.centery) - 100
        self.volume_bar_rect = pg.Rect(bar_x, bar_y, bar_width, bar_height)

        ## 音量滑桿
        handle_size = 20
        handle_x = bar_x + int(GameSettings.AUDIO_VOLUME * bar_width) - handle_size // 2
        handle_y = bar_y + bar_height // 2 - handle_size // 2
        self.volume_handle_rect = pg.Rect(handle_x, handle_y, handle_size, handle_size)



    def toggle_mute(self):
        # 恢復播放
        if self.is_muted:
            self.is_muted = False
            sound_manager.resume_all()  
        # 暫停所有聲音
        else:
            self.is_muted = True
            sound_manager.pause_all()   

    @override
    def enter(self) -> None:
        sound_manager.play_bgm("RBY 101 Opening (Part 1).ogg")
        pass

    @override
    def exit(self) -> None:
        pass

    @override
    def update(self, dt: float) -> None:
       
        ## 關閉按鈕
        self.close_button.update(dt)

        ## 音量條控制
        if pg.mouse.get_pressed()[0]:  
            mx, my = pg.mouse.get_pos()
            if self.volume_bar_rect.collidepoint(mx, my):
                # 計算音量比例
                ratio = (mx - self.volume_bar_rect.x) / self.volume_bar_rect.width
                ratio = max(0, min(1, ratio))
                GameSettings.AUDIO_VOLUME = ratio
                # 設定音量
                if sound_manager.current_bgm:
                    sound_manager.current_bgm.set_volume(ratio)

        ## 靜音按鈕 ##
        if self.is_muted:
            self.mute_button_on.update(dt)
        else:
            self.mute_button_off.update(dt)


    @override
    def draw(self, screen: pg.Surface) -> None:
        self.background.draw(screen)

        # 畫面板底框
        pg.draw.rect(screen, (255, 153, 51), self.panel)
        pg.draw.rect(screen, (255, 178, 102), self.panel, 10)  

        # 畫關閉按鈕
        self.close_button.draw(screen)

        # 標題
        text_surface = self.font_title.render("Setting", True, (0, 0, 0))
        text_rect = text_surface.get_rect(center=(self.panel.centerx, self.panel.top + 80))
        screen.blit(text_surface, text_rect)

        # 畫音量條
        pg.draw.rect(screen, (204, 102, 0), self.volume_bar_rect)  

        # 根據音量比例畫出目前音量大小
        fill_width = int(self.volume_bar_rect.width * GameSettings.AUDIO_VOLUME)
        pg.draw.rect(screen, (255, 178, 102), (self.volume_bar_rect.x, self.volume_bar_rect.y, fill_width, self.volume_bar_rect.height))

        # 更新滑桿位置
        self.volume_handle_rect.x = (
            self.volume_bar_rect.x + int(GameSettings.AUDIO_VOLUME * self.volume_bar_rect.width) - self.volume_handle_rect.width // 2
        )
        # 畫滑桿
        pg.draw.rect(screen, (255, 255, 255), self.volume_handle_rect)
        pg.draw.rect(screen, (0, 0, 0), self.volume_handle_rect, 2)

        # 文字 -- 音量條
        text_rect = self.text_volume_label.get_rect(center=(self.panel.centerx - 120, self.volume_bar_rect.y - 20))
        volume_text = self.font.render(f"{int(GameSettings.AUDIO_VOLUME * 100)}%", True, (50, 50, 50))
        screen.blit(self.text_volume_label, text_rect)
        screen.blit(volume_text, (self.panel.centerx + 200, self.volume_bar_rect.y))

        ## 禁音
        if self.is_muted:
            self.mute_button_on.draw(screen)
        else:
            self.mute_button_off.draw(screen)
        status_text = f"Mute: {'ON' if self.is_muted else 'OFF'}"
        text_surface = self.font.render(status_text, True, (0, 0, 0))
        text_rect = text_surface.get_rect(center=(self.panel.centerx - 110, self.panel.centery-40))
        screen.blit(text_surface, text_rect)