'''check point 2 - 5: Enemy Interaction'''
import pygame as pg
import random
from src.utils import BattleType
from src.scenes.scene import Scene
from src.core import GameManager
from src.utils import GameSettings, Logger, Position
from src.interface.components import Button
from src.core.services import scene_manager
from src.sprites import BackgroundSprite, Sprite

from src.entities.monster import Monster
from src.interface.health_bar import HealthBar
from src.interface.battle_dashboard import BattleDashboard


class BattleScene(Scene):
    background: BackgroundSprite
    font: pg.font.Font

    dashboard: BattleDashboard
    hp_bar: HealthBar
    
    battle_type: BattleType = BattleType.WILD

    player: Monster | None = None
    enemy: Monster | None = None 

    def __init__(self):
        super().__init__()
        self.background = BackgroundSprite("backgrounds/background1.png")
        self.font = pg.font.Font("./assets/fonts/Minecraft.ttf", 24)
        self.game_manager = None 

        self.turn_timer = 0.0
        self.state = "PLAYER"

        self.hp_bar = HealthBar("./assets/fonts/Minecraft.ttf", 24)
        
        self.dashboard = BattleDashboard(
            self.font,
            on_fight=self.player_attack,
            on_switch=self.switch_monster,
            on_run=self.run_away,
            on_catch=self.try_catch_monster
        )

    ## 初始化戰鬥 ##
    def setup_battle(self, game_manager, enemy_data, battle_type: BattleType):

        self.game_manager = game_manager
        self.battle_type = battle_type
        
        self.enemy = Monster(enemy_data, is_player=False, game_manager=self.game_manager)
        self.enemy.hp = self.enemy.max_hp

        if self.battle_type == BattleType.WILD:
            self.log_text = f"A wild {self.enemy.name} appeared!"
            self.dashboard.show_catch_button(True) 
        else:
            self.log_text = f"Trainer wants to battle!"
            self.dashboard.show_catch_button(False)

        self.state = "PLAYER"

    ## 捕捉邏輯 ##
    def try_catch_monster(self):
        if self.state != "PLAYER" or not self.enemy: return

        # 精靈球邏輯
        bag_items = self.game_manager.bag._items_data
        pokeball = next((i for i in bag_items if i["name"] == "Pokeball"), None)

        if not pokeball or pokeball.get("count", 0) <= 0:
            self.log_text = "You don't have any Pokeballs!"
            return
            
        pokeball["count"] -= 1
        Logger.info(f"Used a Pokeball. Remaining: {pokeball['count']}")

        if pokeball["count"] <= 0:
             bag_items.remove(pokeball)

        # 捕捉怪獸放入背包
        Logger.info("Player threw a Ball!")
        self.state = "WON"
        self.log_text = f"Gotcha! {self.enemy.name} was caught!"
        if self.game_manager and self.game_manager.bag:    
            data = self.enemy.data.copy() # 複製怪獸資料並更新當前血量
            data["hp"] = self.enemy.hp    
            self.game_manager.bag._monsters_data.append(data) # 加入背包列表
            Logger.info(f"Added {self.enemy.name} to bag.")

        self.turn_timer = 0

    ## 攻擊邏輯 ##    
    def player_attack(self):
        if self.state != "PLAYER" or not self.enemy: 
            return
        
        Logger.info("Player chose to Fight!")
        base_dmg = self.player.attack
        damage = int(base_dmg)
        self.enemy.take_damage(damage)
        self.log_text = f"You dealt {damage} damage!"

        if self.enemy.hp <= 0:
            self.enemy.hp = 0
            self.state = "WON"
            self.log_text = f"You defeated {self.enemy.name}!"
            self.turn_timer = 0
        else:
            self.state = "ENEMY"
            self.turn_timer = 0

    ## 逃跑邏輯 (資料回寫)##
    def run_away(self):
        Logger.info("Player chose to Run!")
        if self.player and self.player.data:
            self.player.data["hp"] = self.player.hp
            Logger.info(f"Battle ended. HP saved: {self.player.hp}")
        scene_manager.change_scene("game")

    ## 戰鬥結束處理 (資料回寫) ##
    def _end_battle(self):
        if self.player and self.player.data:
            self.player.data["hp"] = self.player.hp
            Logger.info(f"Battle ended. HP saved: {self.player.hp}")
        scene_manager.change_scene("game")

    ## 切換怪獸邏輯 ##
    def switch_monster(self):
        if self.state != "PLAYER": 
            return
        if not self.all_monsters: 
            return

        found_index = -1
        total_monsters = len(self.all_monsters)

        for i in range(1, total_monsters):
            check_index = (self.current_monster_index + i) % total_monsters
            if self.all_monsters[check_index].get("hp", 0) > 0:
                found_index = check_index
                break

        if found_index == -1:
            self.log_text = "No other Pokemon available!"
            return

        if self.player:
            self.player.data["hp"] = self.player.hp

        self.current_monster_index = found_index
        new_data = self.all_monsters[found_index]
        self.player = Monster(new_data, is_player=True, game_manager=self.game_manager)

        self.log_text = f"Go! {self.player.name}!"
        self.state = "ENEMY"
        self.turn_timer = 0

   ## 自動切換邏輯: 當前怪獸死掉時觸發 ##
    def _auto_switch(self) -> bool:
        if self.player:
            self.player.data["hp"] = 0

        found_index = -1
        for i, m_data in enumerate(self.all_monsters):
            if m_data.get("hp", 0) > 0:
                found_index = i
                break
        
        if found_index == -1:
            return False 

        self.current_monster_index = found_index
        new_data = self.all_monsters[found_index]
        self.player = Monster(new_data, is_player=True, game_manager=self.game_manager)
        
        self.log_text = f"Go {self.player.name}!"
        return True

    def enter(self):
        # 檢查是否成功接收到 game_manager
        if self.game_manager is None:
            Logger.error("GameManager not set in BattleScene!")
            return
        
        if self.game_manager and self.game_manager.bag:
            monsters = getattr(self.game_manager.bag, "_monsters_data", [])
            
            self.all_monsters = monsters 
            self.current_monster_index = -1
            
            if monsters:
                found_alive = False
                for i, m_data in enumerate(monsters):
                    if m_data.get("hp", 0) > 0:
                        self.player = Monster(m_data, is_player=True, game_manager=self.game_manager)
                        self.current_monster_index = i
                        found_alive = True
                        break
                if not found_alive:
                    self.log_text = "You have no energy to fight..."
                    self.state = "LOST"
                return
        
    ## update 支援四種狀態 ##
    def update(self, dt: float):
        if self.state == "PLAYER":
            self.dashboard.update(dt)
        elif self.state == "ENEMY":
            self.turn_timer += dt
            if self.turn_timer > 1.0:
                if self.player:
                    base_dmg = self.enemy.attack
                    dmg = int(base_dmg)
                    self.player.take_damage(dmg)
                    self.log_text = f"{self.enemy.name} attacked! {dmg} dmg"
                if self.turn_timer > 2.5:
                    if self.player.hp <= 0:
                        self.player.hp = 0
                        if self._auto_switch():
                            self.state = "PLAYER"
                        else:
                            self.state = "LOST"
                            self.log_text = "You fainted..."
                    else:
                        self.state = "PLAYER"
                    self.turn_timer = 0

        elif self.state in ["WON", "LOST"]:
            self.turn_timer += dt
            if self.turn_timer > 2.0:
                self._end_battle()
       
    def draw(self, screen: pg.Surface):
        self.background.draw(screen)
        
        ## 繪製儀錶板 ##
        self.dashboard.draw(screen)
         
        ## 繪製對手 ##
        if self.enemy:
            self.enemy.draw(screen)
            rect = self.enemy.sprite.rect if self.enemy.sprite else pg.Rect(0,0,0,0)
            enemy_name_display = f"Lv.{self.enemy.level} {self.enemy.name}"
            self.hp_bar.draw(screen, rect.x + 10, 70, self.enemy.hp, self.enemy.max_hp, enemy_name_display)
            
        ## 繪製玩家 ##
        if self.player:
            self.player.draw(screen)
            rect = self.player.sprite.rect if self.player.sprite else pg.Rect(0,0,0,0)
            player_name_display = f"Lv.{self.player.level} {self.player.name}"
            self.hp_bar.draw(screen, rect.x + 50, rect.top + 80, self.player.hp, self.player.max_hp, player_name_display)

        ## 戰鬥訊息 ##
        if self.log_text:
            log_txt = self.font.render(self.log_text, True, (255, 255, 255))
            log_rect = log_txt.get_rect(center=(GameSettings.SCREEN_WIDTH // 2, self.dashboard.rect.top - 30))
            bg_rect = log_rect.inflate(20, 10)
            s = pg.Surface((bg_rect.width, bg_rect.height))
            s.set_alpha(150)
            s.fill((0,0,0))
            screen.blit(s, bg_rect.topleft)
            screen.blit(log_txt, log_rect)
