import pygame as pg
import threading
import time
import random
from src.utils import BattleType

from src.scenes.scene import Scene
from src.core import GameManager, OnlineManager
from src.utils import Logger, PositionCamera, GameSettings, Position
from src.core.services import sound_manager
from src.sprites import Sprite
from typing import override
from src.interface.components import Button
from src.core.services import input_manager, scene_manager

from src.interface.windows.menu_window import MenuWindow
from src.interface.windows.bag_window import BagWindow
from src.interface.windows.setting_window import SettingWindow
from src.interface.windows.shop_window import ShopWindow

class GameScene(Scene):
    game_manager: GameManager
    online_manager: OnlineManager | None
    sprite_online: Sprite

    '''check point 2 - 1: Overlay'''
    menu_button: Button
    menu_window: MenuWindow

    '''check point 2 - 4: Setting Overlay'''
    setting_button: Button
    setting_window: SettingWindow

    '''check point 2 - 3: Backpack Overlay'''
    bag_button: Button
    bag_window: BagWindow

    '''check point 3 -2: Shop Overlay'''
    shop_window: ShopWindow
    
    def __init__(self):
        super().__init__()
        # Game Manager
        manager = GameManager.load("saves/game0.json")
        if manager is None:
            Logger.error("Failed to load game manager")
            exit(1)
        self.game_manager = manager
        
        # Online Manager
        if GameSettings.IS_ONLINE:
            self.online_manager = OnlineManager()
        else:
            self.online_manager = None
        self.sprite_online = Sprite("ingame_ui/options1.png", (GameSettings.TILE_SIZE, GameSettings.TILE_SIZE))

        ## 字型
        self.font_title = pg.font.Font("././assets/fonts/Pokemon Solid.ttf", 30)
        self.font_item = pg.font.Font("././assets/fonts/Minecraft.ttf", 20)
        px, py = GameSettings.SCREEN_WIDTH , GameSettings.SCREEN_HEIGHT

        self.log_text = ""
        self.log_timer = 0.0

        ## check point 2 - 1: Overlay 初始化 menu ##
        self.menu_window = MenuWindow(self.game_manager, self.font_title)

        self.menu_button = Button(
            "UI/button_load.png",
            "UI/button_load_hover.png",
            px - 50, py - 50,
            35, 35,
            on_click = self.menu_window.toggle
        )

        ## check point 2 - 4: Setting Overlay 初始化 setting ##
        self.setting_window = SettingWindow(
            self.game_manager, 
            self.font_title, 
            self.font_item, 
            on_game_reload_callback=self.on_game_reload
        )

        self.setting_button = Button(
            "UI/button_setting.png",
            "UI/button_setting_hover.png",
            px - 50, py - 100,
            35, 35,
            on_click = self.setting_window.toggle
        )

        ## check point 2 - 3: Backpack Overlay 初始化 bag ##
        self.bag_window = BagWindow(self.game_manager, self.font_title, self.font_item)

        self.bag_button = Button(
            "UI/button_backpack.png",
            "UI/button_backpack_hover.png",
            px - 50, py - 150,
            35, 35,
            on_click = self.bag_window.toggle
        )

        ## check point 3 -2: Shop Overlay 初始化 shop ##
        self.shop_window = ShopWindow(self.game_manager, self.font_title, self.font_item)

    ## 當 SettingWindow 讀取存檔後，會呼叫此函式來更新所有場景中的參照 ##
    def on_game_reload(self, new_manager: GameManager):
        self.game_manager = new_manager
        self.menu_window.game_manager = new_manager
        self.bag_window.game_manager = new_manager
        self.shop_window.game_manager = new_manager
        Logger.info("GameScene reference updated successfully.")

    # 檢查背包中是否有任何怪獸 HP > 0
    def check_team_alive(self) -> bool:
        for monster in self.game_manager.bag._monsters_data:
            hp = monster.get("hp", monster.get("current_hp", 0))
            if hp > 0:
                return True
        return False
        
    @override
    def enter(self) -> None:
        sound_manager.play_bgm("RBY 103 Pallet Town.ogg")
        if self.online_manager:
            self.online_manager.enter()
        
    @override
    def exit(self) -> None:
        if self.online_manager:
            self.online_manager.exit()
        
    @override
    def update(self, dt: float):

        self.menu_button.update(dt)
        self.setting_button.update(dt)
        self.bag_button.update(dt)

        if self.log_timer > 0:
            self.log_timer -= dt
            if self.log_timer <= 0:
                self.log_text = ""
        
        if self.menu_window.is_open:
            self.menu_window.update(dt)
            
        elif self.setting_window.is_open:
            self.setting_window.update(dt)

        elif self.bag_window.is_open:
            self.bag_window.update(dt)

        elif self.shop_window.is_open:
            self.shop_window.update(dt)
            
        else: ## 正常遊戲 ##
            # Check if there is assigned next scene
            self.game_manager.try_switch_map()
            
            # Update player and other data
            if self.game_manager.player:
                self.game_manager.player.update(dt)

                player = self.game_manager.player
                is_moving = player.dis.x != 0 or player.dis.y != 0
                
                # 檢查是否踩在草叢上，縮小判定範圍
                hitbox = player.animation.rect.inflate(-10, -10)
                in_grass = self.game_manager.current_map.check_in_grass(hitbox)

                if is_moving and in_grass:
                    if random.random() < 0.05: 
                        Logger.info("Wild Monster Encountered!")

                        if not self.check_team_alive():
                            self.log_text = "You have no energy to battle! Please heal!"
                            self.log_timer = 1.0
                            Logger.info("You have no energy to battle! Please heal!")
                            return
                        
                        monster_keys = list(self.game_manager.monster_database.keys())
                        species = random.choice(monster_keys)
                        enemy_data = self.game_manager.monster_database[species].copy()
                        enemy_data["level"] = random.randint(1, 40)
                        
                        if "current_hp" in enemy_data: del enemy_data["current_hp"]
                        if "hp" in enemy_data: del enemy_data["hp"]

                        battle_scene = scene_manager._scenes["battle"]    
                        battle_scene.setup_battle(
                            self.game_manager, 
                            enemy_data,
                            BattleType.WILD
                        )
                        scene_manager.change_scene("battle")
                        return

            '''check point 2 - 5: Enemy Interaction'''
            for enemy in self.game_manager.current_enemy_trainers:
                enemy.update(dt)
                # 偵測是否發現玩家且玩家按下空白鍵
                if enemy.detected and input_manager.key_pressed(pg.K_SPACE):
                    Logger.info("Battle Triggered!")

                    if not self.check_team_alive():
                        self.log_text = "You have no energy to battle! Please heal!"
                        self.log_timer = 1.0
                        Logger.info("You have no energy to battle! Please heal!")
                        return

                    # 取得訓練家資料
                    t_id = enemy.trainer_id
                    trainer_data = self.game_manager.trainer_database.get(t_id)
                    if not trainer_data:
                        Logger.error(f"Trainer data for {t_id} not found!")
                        return
                    Logger.info(f"Fighting against {trainer_data['name']}")

                    first_monster_info = trainer_data["team"][0]
                    base_monster_data = self.game_manager.monster_database.get(first_monster_info["name"])

                    battle_monster_data = base_monster_data.copy()
                    battle_monster_data["level"] = first_monster_info["level"]

                    battle_scene = scene_manager._scenes["battle"]    
                    battle_scene.setup_battle(
                        self.game_manager, 
                        battle_monster_data,
                        BattleType.TRAINER
                    )
                    scene_manager.change_scene("battle")
                    return
                
            '''check point 3 -2: Shop Interaction'''
            for merchant in self.game_manager.merchants.get(self.game_manager.current_map_key, []):
                merchant.update(dt)
                if merchant.detected and input_manager.key_pressed(pg.K_SPACE):
                    Logger.info("Store Triggered!")
                    self.shop_window.setup_shop(merchant.goods)
                

            # Update others
            self.game_manager.bag.update(dt)
            
            if self.game_manager.player is not None and self.online_manager is not None:
                _ = self.online_manager.update(
                    self.game_manager.player.position.x, 
                    self.game_manager.player.position.y,
                    self.game_manager.current_map.path_name
                )
        
    @override
    def draw(self, screen: pg.Surface):        
        if self.game_manager.player:
            '''
            [TODO HACKATHON 3]
            Implement the camera algorithm logic here
            Right now it's hard coded, you need to follow the player's positions
            you may use the below example, but the function still incorrect, you may trace the entity.py
            camera = self.game_manager.player.camera
            '''
            # 使用玩家在中央的相機
            camera = self.game_manager.player.camera
            self.game_manager.current_map.draw(screen, camera)
            self.game_manager.player.draw(screen, camera)
        else:
            camera = PositionCamera(0, 0)
            self.game_manager.current_map.draw(screen, camera)

        for enemy in self.game_manager.current_enemy_trainers:
            enemy.draw(screen, camera)

        for merchant in self.game_manager.merchants.get(self.game_manager.current_map_key, []):
            merchant.draw(screen, camera)

        self.game_manager.bag.draw(screen)
        
        if self.online_manager and self.game_manager.player:
            list_online = self.online_manager.get_list_players()
            for player in list_online:
                if player["map"] == self.game_manager.current_map.path_name:
                    camera = self.game_manager.player.camera
                    pos = camera.transform_position_as_position(Position(player["x"], player["y"]))
                    self.sprite_online.update_pos(pos)
                    self.sprite_online.draw(screen)

        
        ## menu, setting, bag buttons ##
        self.menu_button.draw(screen)
        self.setting_button.draw(screen)
        self.bag_button.draw(screen)

        ## menu, setting, bag window ##
        self.menu_window.draw(screen)
        self.setting_window.draw(screen)
        self.bag_window.draw(screen)
        self.shop_window.draw(screen)

        if self.log_text:
            log_txt = self.font_item.render(self.log_text, True, (255, 255, 255))
            log_rect = log_txt.get_rect(center=(GameSettings.SCREEN_WIDTH // 2, GameSettings.SCREEN_HEIGHT - 100))
            bg_rect = log_rect.inflate(20, 10)
            s = pg.Surface((bg_rect.width, bg_rect.height))
            s.set_alpha(150)
            s.fill((0,0,0))
            screen.blit(s, bg_rect.topleft)
            screen.blit(log_txt, log_rect)