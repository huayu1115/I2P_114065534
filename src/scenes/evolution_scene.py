import pygame as pg
from src.scenes.scene import Scene
from src.utils import GameSettings, Logger, load_img
from src.core.services import scene_manager

class EvolutionScene(Scene):
    def __init__(self, game_manager):
        super().__init__()
        self.game_manager = game_manager
        self.font = pg.font.Font("./assets/fonts/Minecraft.ttf", 30)
        
        self.monster = None
        self.next_id = None
        
        self.timer = 0
        self.state = 0 # 0:開始 1:動畫中 2:結束等待
        
        # 動畫資源
        self.old_sprite = None
        self.new_sprite = None
        self.current_img = None
        self.text = ""

    def setup(self, monster, next_id):
        self.monster = monster
        self.next_id = next_id
        self.timer = 0
        self.state = 0
        self.text = f"What? {self.monster.name} is evolving!"
        
        # 準備舊圖片
        if self.monster.sprite:
            self.old_sprite = self.monster.sprite.image
        
        # 預先載入新圖片
        next_data = self.game_manager.monster_database.get(next_id, {})
        path = next_data.get("sprite_battle_path", "")
        if path:
            try:
                sheet = load_img(path)
                self.new_sprite = pg.transform.scale(sheet, (300, 300)) 
            except:
                self.new_sprite = self.old_sprite 
        
        self.current_img = self.old_sprite

    def update(self, dt: float):
        self.timer += dt
        
        # 顯示文字
        if self.state == 0:
            if self.timer > 1.5:
                self.state = 1
                self.timer = 0
        
        # 閃爍動畫
        elif self.state == 1:
            if int(self.timer * 5) % 2 == 0:
                self.current_img = self.old_sprite
            else:
                self.current_img = self.new_sprite

            if self.timer > 2.0:
                self.monster.evolve(self.next_id)
                self.current_img = self.monster.sprite.image # 確保是用切好的新圖
                self.text = f"Congratulations! Your pokemon evolved!"
                self.state = 2
                self.timer = 0
        
        # 顯示結果，等待按鍵離開
        elif self.state == 2:
            keys = pg.key.get_pressed()
            if self.timer > 0.5 and keys[pg.K_SPACE]: 
                scene_manager.change_scene("game")

    def draw(self, screen: pg.Surface):
        screen.fill((0, 0, 0))

        if self.current_img:
            rect = self.current_img.get_rect(center=(GameSettings.SCREEN_WIDTH // 2, GameSettings.SCREEN_HEIGHT // 2 - 50))
            screen.blit(self.current_img, rect)

        txt_surf = self.font.render(self.text, True, (255, 255, 255))
        txt_rect = txt_surf.get_rect(center=(GameSettings.SCREEN_WIDTH // 2, GameSettings.SCREEN_HEIGHT - 100))
        screen.blit(txt_surf, txt_rect)