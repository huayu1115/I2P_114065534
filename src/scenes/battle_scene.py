'''check point 2 - 5: Enemy Interaction'''
import pygame as pg
import random
from enum import Enum, auto
from typing import Optional

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

# 使用 Enum 管理戰鬥狀態
class BattleState(Enum):
    PLAYER_TURN = auto()
    ENEMY_TURN = auto()
    WON = auto()
    LOST = auto()
    RUNNING = auto()

# 屬性相剋表
ELEMENT_ADVANTAGE = {
    'fire': 'grass',
    'water': 'fire',
    'grass': 'water'
}

class BattleScene(Scene):
    background: BackgroundSprite
    font: pg.font.Font
    dashboard: BattleDashboard
    hp_bar: HealthBar

    TURN_DELAY_ATTACK = 1.0  # 敵人思考時間
    TURN_DELAY_END = 2.0     # 回合結束等待時間
    BATTLE_END_DELAY = 2.0   # 戰鬥結束後的等待時間

    def __init__(self):
        super().__init__()
        self.background = BackgroundSprite("backgrounds/background1.png")
        self.font = pg.font.Font("./assets/fonts/Minecraft.ttf", 24)

        self.game_manager: Optional[GameManager] = None 
        self.turn_timer = 0.0
        self.state: BattleState = BattleState.PLAYER_TURN

        # 戰鬥相關實體
        self.player: Optional[Monster] = None
        self.enemy: Optional[Monster] = None 
        self.all_monsters: list[dict] = []
        self.current_monster_index = -1
        self.battle_type = BattleType.WILD
        self.log_text = ""

        # UI 元件
        self.hp_bar = HealthBar("./assets/fonts/Minecraft.ttf", 20)
        self.dashboard = BattleDashboard(
            self.font,
            on_fight=self.player_attack,
            on_switch=self.switch_monster,
            on_run=self.run_away,
            on_heal=self.on_use_heal_potion,
            on_power=self.on_use_power_potion,
            on_def=self.on_use_def_potion,
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

        self.state = BattleState.PLAYER_TURN
        self.turn_timer = 0

    def enter(self):
        """場景進入時，載入玩家隊伍資料"""
        if self.game_manager is None:
            Logger.error("GameManager not set in BattleScene!")
            return
        
        if self.game_manager and self.game_manager.bag:
            self.all_monsters = getattr(self.game_manager.bag, "_monsters_data", [])
            self.current_monster_index = -1
            
            # 找第一隻存活的怪獸
            found_alive = False
            for i, m_data in enumerate(self.all_monsters):
                if m_data.get("hp", 0) > 0:
                    self.player = Monster(m_data, is_player=True, game_manager=self.game_manager)
                    self.current_monster_index = i
                    found_alive = True
                    break
            
            if not found_alive:
                self.log_text = "You have no energy to fight..."
                self.state = BattleState.LOST

    ## 攻擊邏輯 ##    
    def player_attack(self):
        if self.state != BattleState.PLAYER_TURN or not self.enemy: 
            return
        Logger.info("Player chose to Fight!")
        
        # 呼叫傷害計算
        dmg, dmg_text = self._calculate_damage(self.player, self.enemy)
        
        self.enemy.take_damage(dmg)
        self.log_text = f"You dealt {dmg_text} damage!"

        if self.enemy.hp <= 0:
            self.enemy.hp = 0
            self.state = BattleState.WON
            self.log_text = f"You defeated {self.enemy.name}!"
        else:
            self.state = BattleState.ENEMY_TURN
        
        self.turn_timer = 0

    ## 捕捉邏輯 ##
    def try_catch_monster(self):
        if self.state != BattleState.PLAYER_TURN or not self.enemy: return

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

        Logger.info("Player threw a Ball!")
        self.state = BattleState.WON
        self.log_text = f"Gotcha! {self.enemy.name} was caught!"

        # 加入背包列表
        if self.game_manager and self.game_manager.bag:    
            data = self.enemy.data.copy()
            data["hp"] = self.enemy.hp    
            self.game_manager.bag._monsters_data.append(data) 
            Logger.info(f"Added {self.enemy.name} to bag.")

        self.turn_timer = 0

    ## 逃跑邏輯 (資料回寫)##
    def run_away(self):
        Logger.info("Player chose to Run!")
        self._save_player_state()
        scene_manager.change_scene("game")

    ## 切換怪獸邏輯 ##
    def switch_monster(self):
        if self.state != BattleState.PLAYER_TURN: return
        if not self.all_monsters: return

        found_index = -1
        total = len(self.all_monsters)
        for i in range(1, total):
            check_index = (self.current_monster_index + i) % total
            if self.all_monsters[check_index].get("hp", 0) > 0:
                found_index = check_index
                break

        if found_index == -1:
            self.log_text = "No other Pokemon available!"
            return

        self._switch_monster(found_index)
        self.state = BattleState.ENEMY_TURN
        self.turn_timer = 0
    
    # checkpoint 3-4: 藥水功能，搭配 _use_item 輔助函式
    def on_use_heal_potion(self):
        def effect():
            heal_amount = 50 # 設定回復量
            old_hp = self.player.hp
            self.player.hp += heal_amount
            if self.player.hp > self.player.max_hp:
                self.player.hp = self.player.max_hp
            recovered = self.player.hp - old_hp
            return f"Used Healing Potion! Recovered {recovered} HP."

        self._use_item("Heal Potion", effect)

    def on_use_power_potion(self):
        def effect():
            boost = 10 # 設定攻擊提升量
            self.player.attack += boost
            return f"Used Strength Potion! Attack rose by {boost}!"
            
        self._use_item("Strength Potion", effect)

    def on_use_def_potion(self):
        def effect():
            boost = 10 # 設定防禦提升量
            self.player.defense += boost
            return f"Used Defense Potion! Defense rose by {boost}!"

        self._use_item("Defense Potion", effect)

    ## update 支援四種狀態 ##
    def update(self, dt: float):
        if self.state == BattleState.PLAYER_TURN:
            self.dashboard.update(dt)
        
        elif self.state == BattleState.ENEMY_TURN:
            self._process_enemy_turn(dt)

        elif self.state in [BattleState.WON, BattleState.LOST]:
            self.turn_timer += dt
            if self.turn_timer > self.BATTLE_END_DELAY:
                self._save_player_state()
                scene_manager.change_scene("game")

       
    def draw(self, screen: pg.Surface):
        self.background.draw(screen)
        self.dashboard.draw(screen)
         
        ## 繪製對手 ##
        if self.enemy:
            self.enemy.draw(screen)
            rect = self.enemy.sprite.rect if self.enemy.sprite else pg.Rect(0,0,0,0)
            enemy_name_display = f"Lv.{self.enemy.level} {self.enemy.name}"
            self.hp_bar.draw(screen, rect.x + 10, 70, self.enemy.hp, self.enemy.max_hp, enemy_name_display, self.enemy.type)
            
        ## 繪製玩家 ##
        if self.player:
            self.player.draw(screen)
            rect = self.player.sprite.rect if self.player.sprite else pg.Rect(0,0,0,0)
            player_name_display = f"Lv.{self.player.level} {self.player.name}"
            self.hp_bar.draw(screen, rect.x + 50, rect.top + 80, self.player.hp, self.player.max_hp, player_name_display, self.player.type)

        ## 戰鬥訊息 ##
        if self.log_text:
            self._draw_log_text(screen)

    # checkpoint 3-4: 計算屬性相剋的傷害
    def _calculate_damage(self, attacker: Monster, defender: Monster) -> tuple[int, str]:
        """傷害計算，回傳 (final_damage, log_message_suffix)"""
        base_dmg = int(max(1, attacker.attack - defender.defense))
        
        attacker_type = attacker.type
        defender_type = defender.type

        final_damage = base_dmg
        damage_info = f"{base_dmg}"

        # 屬性相剋判斷
        if ELEMENT_ADVANTAGE.get(attacker_type) == defender_type:
            bonus = int(base_dmg * 0.5)
            if bonus < 1: bonus = 1
            final_damage = base_dmg + bonus
            damage_info = f"{base_dmg} ( + {bonus} )"
        
        elif ELEMENT_ADVANTAGE.get(defender_type) == attacker_type:
            reduction = int(base_dmg * 0.5)
            final_damage = base_dmg - reduction
            damage_info = f"{base_dmg} ( - {reduction} )"
        
        else:
            damage_info = f"{base_dmg} ( + 0 )"

        return final_damage, damage_info
    
    def _switch_monster(self, new_index: int):
        """執行切換怪獸的動作"""
        if self.player:
            self.player.data["hp"] = self.player.hp # 保存舊怪獸血量

        self.current_monster_index = new_index
        new_data = self.all_monsters[new_index]
        self.player = Monster(new_data, is_player=True, game_manager=self.game_manager)
        self.log_text = f"Go! {self.player.name}!"

    def _auto_switch(self) -> bool:
        '''自動切換邏輯: 當前怪獸死掉時觸發'''
        if self.player:
            self.player.data["hp"] = 0

        for i, m_data in enumerate(self.all_monsters):
            if m_data.get("hp", 0) > 0:
                self._switch_monster(i)
                return True
        return False 

    def _save_player_state(self):
        """將當前血量寫回"""
        if self.player and self.player.data:
            self.player.data["hp"] = self.player.hp

    def _process_enemy_turn(self, dt: float):
        """處理敵方回合的計時與攻擊"""
        self.turn_timer += dt

        # 攻擊 
        if self.turn_timer > self.TURN_DELAY_ATTACK and "attacked" not in self.log_text:
             if self.player.hp > 0:
                dmg, dmg_text = self._calculate_damage(self.enemy, self.player)
                self.player.take_damage(dmg)
                self.log_text = f"{self.enemy.name} attacked! {dmg_text} dmg"
        
        # 回合結束判斷
        if self.turn_timer > self.TURN_DELAY_END:
            if self.player.hp <= 0:
                self.player.hp = 0
                if self._auto_switch():
                    self.state = BattleState.PLAYER_TURN
                else:
                    self.state = BattleState.LOST
                    self.log_text = "You fainted..."
            else:
                self.state = BattleState.PLAYER_TURN
            self.turn_timer = 0

    def _draw_log_text(self, screen: pg.Surface):
        log_txt = self.font.render(self.log_text, True, (255, 255, 255))
        log_rect = log_txt.get_rect(center=(GameSettings.SCREEN_WIDTH // 2, self.dashboard.rect.top - 30))
        bg_rect = log_rect.inflate(20, 10)
        
        s = pg.Surface((bg_rect.width, bg_rect.height))
        s.set_alpha(150)
        s.fill((0,0,0))
        
        screen.blit(s, bg_rect.topleft)
        screen.blit(log_txt, log_rect)

    ## 戰鬥結束處理 (資料回寫) ##
    def _end_battle(self):
        if self.player and self.player.data:
            self.player.data["hp"] = self.player.hp
            Logger.info(f"Battle ended. HP saved: {self.player.hp}")
        scene_manager.change_scene("game")


    # checkpoint 3-4: 道具使用輔助函式
    def _use_item(self, item_name: str, effect_callback):
        if self.state != BattleState.PLAYER_TURN or not self.player:
            return

        # 從背包找道具
        bag_items = self.game_manager.bag._items_data
        item = next((i for i in bag_items if i["name"] == item_name), None)

        if not item or item.get("count", 0) <= 0:
            self.log_text = f"You don't have any {item_name}!"
            return

        # 執行具體效果
        success_msg = effect_callback()
        
        # 扣除道具
        item["count"] -= 1
        if item["count"] <= 0:
            bag_items.remove(item)

        Logger.info(f"Used {item_name}. Remaining: {item['count']}")
        
        # 設定訊息並切換回合
        self.log_text = success_msg
        self.state = BattleState.ENEMY_TURN
        self.turn_timer = 0
        
        # 使用完道具後，讓 dashboard 回到主選單
        self.dashboard.back_to_main()