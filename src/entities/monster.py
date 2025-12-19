import pygame as pg
from src.sprites import Sprite
from src.utils import GameSettings, Logger, Position, load_img
import math

class Monster:
    def __init__(self, data: dict, is_player: bool, game_manager):
        self.game_manager = game_manager
        self.is_player = is_player
        self.data = data

        self.id = data.get("name", "Sproutkit")
        self.name = data.get("name", "Sproutkit")
        self.level = data.get("level", 5)
        self.exp = data.get("exp", 0)
        
        # 確保 game_manager 已經載入了 monsters.json
        if hasattr(game_manager, "monster_database"):
            self.species_data = game_manager.monster_database.get(self.id, {})
        else:
            Logger.error("Monster Database not found in GameManager!")
            self.species_data = {}

        # 物種屬性
        self.name = self.species_data.get("name", "Unknown")
        self.type = self.species_data.get("type", "grass")
        
        # 計算能力值
        self.max_hp = 0
        self.attack = 0
        self.defense = 0
        self.recalculate_stats()

        self.hp = data.get("hp", self.max_hp)
        if self.hp > self.max_hp: self.hp = self.max_hp
        if self.hp < 0: self.hp = 0

        # 圖片
        battle_path = self.species_data.get("sprite_battle_path", "")
        self.sprite: Sprite | None = None
        self._setup_sprite(battle_path)

    @staticmethod
    def calculate_max_hp(base_hp: int, level: int) -> int:
        return int(base_hp * (1 + level * 0.05) + (level * 2))
    def recalculate_stats(self):
        base_hp = self.species_data.get("base_hp", 50)
        base_atk = self.species_data.get("base_attack", 10)
        base_dfn = self.species_data.get("base_defense", 10)
        
        self.max_hp = Monster.calculate_max_hp(base_hp, self.level)
        self.attack = int(base_atk * (1 + self.level * 0.05) + (self.level * 0.5))
        self.defense = int(base_dfn * (1 + self.level * 0.05) + (self.level * 0.5))

    # checkpoint 3-4: 經驗值與升級
    def gain_exp(self, amount: int):
        '''獲得經驗值並檢查升級'''
        logs = []
        self.exp += amount
        logs.append(f"Gained {amount} EXP!")
        
        while True:
            required_exp = (self.level + 1) ** 2 # 經驗值曲線
            if self.exp >= required_exp:
                lvl_logs = self.level_up()
                logs.extend(lvl_logs)
            else:
                break
        return logs

    def level_up(self):
        '''升級處理'''
        logs = []
        self.level += 1
        logs.append(f"{self.name} grew to Lv.{self.level}!")

        # 檢查進化
        evo_logs = self.check_evolution()
        logs.extend(evo_logs)
        return logs
    
    def check_evolution(self):
        '''檢查是否達到進化條件'''
        evo_data = self.species_data.get("evolution")
        if evo_data:
            req_level = evo_data.get("level", 100)
            next_id = evo_data.get("next_id")
            
            if self.level >= req_level and next_id:
                return self.evolve(next_id)
        return []

    def evolve(self, next_id: str):
        '''進化邏輯'''
        logs = []
        old_name = self.name
        logs.append(f"What? {self.name} is evolving!")
        
        # 更新 ID
        self.id = next_id
        
        # 重新讀取物種資料
        self.species_data = self.game_manager.monster_database.get(self.id, {})
        self.name = self.species_data.get("name", self.name)
        self.type = self.species_data.get("type", self.type)
        
        # 重新計算能力值
        old_max_hp = self.max_hp
        self.recalculate_stats()
        self.hp += (self.max_hp - old_max_hp)
        
        # 更新圖片
        battle_path = self.species_data.get("sprite_battle_path", "")
        self._setup_sprite(battle_path)
        
        logs.append(f"Congratulations! Your {old_name}")
        logs.append(f"evolved into {self.name}!")

        return logs

    ## 處理圖片           
    def _setup_sprite(self, path: str):
        if not path: return
        try:
            temp = Sprite(path)
            full_img = temp.image
            
            sheet_w = full_img.get_width()
            sheet_h = full_img.get_height()
            single_w = sheet_w // 2

            # 根據是否為玩家決定切左邊還是右邊
            start_x = single_w if self.is_player else 0
            crop_rect = pg.Rect(start_x, 0, single_w, sheet_h)
            cropped_img = full_img.subsurface(crop_rect)

            final_img = pg.transform.scale(cropped_img, (300, 300))

            # 建立 Sprite
            self.sprite = Sprite(path)
            self.sprite.image = final_img
            self.sprite.rect = final_img.get_rect()

            # 設定畫面位置
            if self.is_player:
                p_x = 50
                p_y = GameSettings.SCREEN_HEIGHT - 440 
                self.sprite.update_pos(Position(p_x, p_y))
            else:
                e_x = GameSettings.SCREEN_WIDTH - 350
                e_y = 80
                self.sprite.update_pos(Position(e_x, e_y))

        except Exception as e:
            Logger.error(f"Failed to load sprite for {self.name}: {e}")

    def draw(self, screen: pg.Surface):
        if self.sprite:
            self.sprite.draw(screen)

    def take_damage(self, amount: int):
        self.hp -= amount
        if self.hp < 0: self.hp = 0