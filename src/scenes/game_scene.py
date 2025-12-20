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
from src.interface.components.minimap import Minimap
from src.core.services import input_manager, scene_manager

from src.interface.windows.menu_window import MenuWindow
from src.interface.windows.bag_window import BagWindow
from src.interface.windows.setting_window import SettingWindow
from src.interface.windows.shop_window import ShopWindow
from src.interface.windows.navigation_window import NavigationWindow

from src.entities.entity import Entity
from src.utils import Direction
from src.interface.components.chat_overlay import ChatOverlay

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

    '''check point 3 -3: 對話框'''
    _chat_bubbles: dict[int, tuple[str, float]]
    _last_chat_id_seen: int
    chat_overlay: ChatOverlay | None
    
    '''check point 3 -6: 導航'''
    nav_button: Button
    nav_window: NavigationWindow
    
    def __init__(self):
        super().__init__()
        # Game Manager
        manager = GameManager.load("saves/game0.json")
        if manager is None:
            Logger.error("Failed to load game manager")
            exit(1)
        self.game_manager = manager

        self._chat_bubbles = {}
        self._last_chat_id_seen = 0
        self.chat_overlay = None
        
        # Online Manager
        if GameSettings.IS_ONLINE:
            self.online_manager = OnlineManager()

            # checkpoint3-3: 初始化 ChatOverlay
            self.chat_overlay = ChatOverlay(
                send_callback=self.online_manager.send_chat,
                get_messages=self.online_manager.get_recent_chat
            )
        else:
            self.online_manager = None
        self.remote_players: dict[int, Entity] = {} # 存 id 對應的 Entity
        
        ## 字型
        self.font_title = pg.font.Font("././assets/fonts/Pokemon Solid.ttf", 30)
        self.font_item = pg.font.Font("././assets/fonts/Minecraft.ttf", 20)
        self.font_bag = pg.font.Font("././assets/fonts/Minecraft.ttf", 15)
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
        self.bag_window = BagWindow(self.game_manager, self.font_title, self.font_bag)

        self.bag_button = Button(
            "UI/button_backpack.png",
            "UI/button_backpack_hover.png",
            px - 50, py - 150,
            35, 35,
            on_click = self.bag_window.toggle
        )

        ## check point 3 - 6: 初始化導航 ##
        self.nav_window = NavigationWindow(self.game_manager, self.font_title, self.font_item)

        self.nav_button = Button(
            "UI/button_play.png", 
            "UI/button_play_hover.png",
            px - 50, py - 200,
            35, 35,
            on_click=self.nav_window.toggle
        )


        ## check point 3-2: Shop Overlay 初始化 shop ##
        self.shop_window = ShopWindow(self.game_manager, self.font_title, self.font_bag)
        ## check point 3-5: 初始化小地圖 ##
        self.minimap = Minimap(self.game_manager, self.font_item)
        ## 初始化等級限制表
        self.min_level_requirements = self._generate_min_levels()


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
        self.nav_button.update(dt)

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

        elif self.nav_window.is_open:
            self.nav_window.update(dt)

        elif self.chat_overlay and self.chat_overlay.is_open:
            self.chat_overlay.update(dt)
            
        else: ## 正常遊戲 ##
            # Check if there is assigned next scene
            self.game_manager.try_switch_map()
            
            # checkpoint 3-3: 偵測開啟聊天室的按鍵，開啟聊天時暫停移動
            if self.chat_overlay and not self.chat_overlay.is_open:
                if input_manager.key_pressed(pg.K_t):
                    self.chat_overlay.open()
                    return
            
            # Update player and other data
            if self.game_manager.player:
                self.game_manager.player.update(dt)

                player = self.game_manager.player
                
                # 檢查是否踩在草叢上，縮小判定範圍
                hitbox = player.animation.rect.inflate(-10, -10)
                in_grass = self.game_manager.current_map.check_in_grass(hitbox)

                # 在草叢上且按下空白鍵
                if in_grass and input_manager.key_pressed(pg.K_SPACE):
                    Logger.info("Wild Monster Encountered!")

                    if not self.check_team_alive():
                        self.log_text = "You have no energy to battle! Please heal!"
                        self.log_timer = 1.0
                        return
                    
                    # 隨機生成遭遇等級
                    encounter_level = random.randint(2, 40)
                    # 篩選怪獸
                    valid_monsters = []
                    db = self.game_manager.monster_database
                    
                    for name in db.keys():
                        # 從快取表中讀取該怪獸的最低等級
                        required_lv = self.min_level_requirements.get(name, 1)
                        # 遭遇等級必須 >= 該怪獸的最低需求
                        if encounter_level >= required_lv:
                            valid_monsters.append(name)

                    if not valid_monsters:
                        valid_monsters = list(db.keys())

                    # 生成怪獸
                    species = random.choice(valid_monsters)
                    enemy_data = db[species].copy()
                    
                    enemy_data["level"] = encounter_level
                    
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


            '''Nurse Interaction'''
            current_nurses = self.game_manager.nurses.get(self.game_manager.current_map_key, [])
            for nurse in current_nurses:
                nurse.update(dt)

                if nurse.detected and input_manager.key_pressed(pg.K_SPACE):
                    msg = nurse.heal_team()

                    self.log_text = msg
                    self.log_timer = 2.0
                
            # Update others
            self.game_manager.bag.update(dt)

            # checkpoint 3-3: 更新對話資料(助教已做好)
            if self.online_manager:
                try:
                    msgs = self.online_manager.get_recent_chat(50)
                    max_id = self._last_chat_id_seen
                    now = time.monotonic()
                    for m in msgs:
                        mid = int(m.get("id", 0))
                        if mid <= self._last_chat_id_seen:
                            continue
                        sender = int(m.get("from", -1))
                        text = str(m.get("text", ""))
                        if sender >= 0 and text:
                            self._chat_bubbles[sender] = (text, now + 5.0)
                        if mid > max_id:
                            max_id = mid
                    self._last_chat_id_seen = max_id
                except Exception:
                    pass
         
            
            # checkpoint 3-3: 玩家增加 direction, is_moving 更新
            if self.game_manager.player is not None and self.online_manager is not None:
                player = self.game_manager.player

                dir_str = player.direction.name.lower()
                is_moving = player.dis.x != 0 or player.dis.y != 0

                _ = self.online_manager.update(
                    self.game_manager.player.position.x, 
                    self.game_manager.player.position.y,
                    self.game_manager.current_map.path_name,
                    dir_str,
                    is_moving
                )

            # checkpoint 3-3: 同步其他玩家
            if self.online_manager:
                list_online = self.online_manager.get_list_players()
                current_map_name = self.game_manager.current_map.path_name
                valid_ids = set() # 記錄這幀還在的玩家

                for p_data in list_online:
                    # 只處理同一張地圖的玩家
                    if p_data["map"] != current_map_name:
                        continue
                    
                    pid = p_data["id"]
                    valid_ids.add(pid)

                    # 若是新玩家就創建一個 Entity
                    if pid not in self.remote_players:
                        self.remote_players[pid] = Entity(
                            p_data["x"], p_data["y"], self.game_manager, "character/ow1.png"
                        )
                    
                    # 取得該玩家的 Entity
                    remote_ent = self.remote_players[pid]
                    
                    # 同步位置
                    remote_ent.position.x = p_data["x"]
                    remote_ent.position.y = p_data["y"]
                    
                    # 同步方向 (將字串轉回 Enum)
                    d_str = p_data.get("direction", "down")
                    if d_str == "up": remote_ent.direction = Direction.UP
                    elif d_str == "down": remote_ent.direction = Direction.DOWN
                    elif d_str == "left": remote_ent.direction = Direction.LEFT
                    elif d_str == "right": remote_ent.direction = Direction.RIGHT
                    
                    # 同步動畫狀態
                    remote_is_moving = p_data.get("is_moving", False)
                    if remote_is_moving:
                        remote_ent.update(dt) # 移動: 正常更新動畫
                    else:
                        remote_ent.update(0)  # 靜止: 只更新方向
                        remote_ent.animation.accumulator = 0 # 強制重置為第一幀 (站立姿勢)

                # 清除已經離開或切換地圖的玩家
                for pid in list(self.remote_players.keys()):
                    if pid not in valid_ids:
                        del self.remote_players[pid]


        
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

        for nurse in self.game_manager.nurses.get(self.game_manager.current_map_key, []):
            nurse.draw(screen, camera)

        self.game_manager.bag.draw(screen)
        
        if self.online_manager and self.game_manager.player:
            list_online = self.online_manager.get_list_players()
            for player in list_online:
                if player["map"] == self.game_manager.current_map.path_name:
                    camera = self.game_manager.player.camera

                    # checkpoint 3-3: 繪製其他線上玩家
                    for entity in self.remote_players.values():
                        entity.draw(screen, camera)
            try:
                # checkpoint 3-3: 繪製對話
                self._draw_chat_bubbles(screen, camera)
            except Exception:
                pass

        # 繪製 Chat Overlay
        if self.chat_overlay:
            self.chat_overlay.draw(screen)

        # 繪製小地圖
        if not self.bag_window.is_open and not self.menu_window.is_open:
            self.minimap.draw(screen)

        ## buttons ##
        self.menu_button.draw(screen)
        self.setting_button.draw(screen)
        self.bag_button.draw(screen)
        self.nav_button.draw(screen)

        ## window ##
        self.menu_window.draw(screen)
        self.setting_window.draw(screen)
        self.bag_window.draw(screen)
        self.shop_window.draw(screen)
        self.nav_window.draw(screen)

        if self.log_text:
            log_txt = self.font_item.render(self.log_text, True, (255, 255, 255))
            log_rect = log_txt.get_rect(center=(GameSettings.SCREEN_WIDTH // 2, GameSettings.SCREEN_HEIGHT - 100))
            bg_rect = log_rect.inflate(20, 10)
            s = pg.Surface((bg_rect.width, bg_rect.height))
            s.set_alpha(150)
            s.fill((0,0,0))
            screen.blit(s, bg_rect.topleft)
            screen.blit(log_txt, log_rect)

    def _draw_chat_bubbles(self, screen: pg.Surface, camera: PositionCamera) -> None:
        if not self.online_manager:
            return
        
        # checkpoint 3-3: 移除過期的對話
        now = time.monotonic()
        expired = [pid for pid, (_, ts) in self._chat_bubbles.items() if ts <= now]
        for pid in expired:
            del self._chat_bubbles[pid]
        if not self._chat_bubbles:
            return
        
        font = self.font_item

        # checkpoint 3-3: 繪製自己的對話氣泡
        local_pid = self.online_manager.player_id
        if self.game_manager.player and local_pid in self._chat_bubbles:
            text, _ = self._chat_bubbles[local_pid]
            self._draw_chat_bubble_for_pos(
                screen, camera, 
                self.game_manager.player.position, 
                text, font
            )

        # checkpoint 3-3: 繪製其他玩家的對話氣泡
        for pid, (text, _) in self._chat_bubbles.items():
            if pid == local_pid:
                continue
            
            # 從 remote_players 找到該玩家的 Entity
            if pid in self.remote_players:
                remote_ent = self.remote_players[pid]
                self._draw_chat_bubble_for_pos(
                    screen, camera, 
                    remote_ent.position, 
                    text, font
                )

        """
        DRAWING CHAT BUBBLES:
        - When a player sends a chat message, the message should briefly appear above
        that player's character in the world, similar to speech bubbles in RPGs.
        - Each bubble should last only a few seconds before fading or disappearing.
        - Only players currently visible on the map should show bubbles.

         What you need to think about:
            ------------------------------
            1. **Which players currently have messages?**
            You will have a small structure mapping player IDs to the text they sent
            and the time the bubble should disappear.

            2. **How do you know where to place the bubble?**
            The bubble belongs above the player's *current position in the world*.
            The game already tracks each player’s world-space location.
            Convert that into screen-space and draw the bubble there.

            3. **How should bubbles look?**
            You decide. The visual style is up to you:
            - A rounded rectangle, or a simple box.
            - Optional border.
            - A small triangle pointing toward the character's head.
            - Enough padding around the text so it looks readable.

            4. **How do bubbles disappear?**
            Compare the current time to the stored expiration timestamp.
            Remove any bubbles that have expired.

            5. **In what order should bubbles be drawn?**
            Draw them *after* world objects but *before* UI overlays.

        Reminder:
        - For the local player, you can use the self.game_manager.player.position to get the player's position
        - For other players, maybe you can find some way to store other player's last position?
        - For each player with a message, maybe you can call a helper to actually draw a single bubble?
        """

    # checkpoint 3-3: 根據 pos 繪製氣泡
    def _draw_chat_bubble_for_pos(self, screen: pg.Surface, camera: PositionCamera, world_pos: Position, text: str, font: pg.font.Font):
        rect_screen = camera.transform_rect(pg.Rect(world_pos.x, world_pos.y, GameSettings.TILE_SIZE, GameSettings.TILE_SIZE))
        
        # 氣泡座標
        center_x = rect_screen.centerx
        bottom_y = rect_screen.top - 10

        text_surf = font.render(text, True, (0, 0, 0))
        w, h = text_surf.get_size()

        # 氣泡背景
        padding = 8
        bubble_rect = pg.Rect(0, 0, w + padding * 2, h + padding * 2)
        bubble_rect.centerx = center_x
        bubble_rect.bottom = bottom_y
        pg.draw.rect(screen, (255, 255, 255), bubble_rect, 0, 8)
        pg.draw.rect(screen, (0, 0, 0), bubble_rect, 2, 8)

        tri_points = [
            (center_x - 5, bubble_rect.bottom),
            (center_x + 5, bubble_rect.bottom),
            (center_x, bubble_rect.bottom + 6)
        ]
        pg.draw.polygon(screen, (255, 255, 255), tri_points)
        pg.draw.polygon(screen, (0, 0, 0), tri_points, 2)

        # 繪製文字
        text_rect = text_surf.get_rect(center=bubble_rect.center)
        screen.blit(text_surf, text_rect)

        """
        Steps:
            ------------------
            1. Convert a player’s world position into a location on the screen.
            (Use the camera system provided by the game engine.)

            2. Decide where "above the player" is.
            Typically a little above the sprite’s head.

            3. Measure the rendered text to determine bubble size.
            Add padding around the text.
        """

    def _generate_min_levels(self) -> dict[str, int]:
        """從資料庫解析怪獸的最低出現等級"""
        db = self.game_manager.monster_database
        min_levels = {name: 1 for name in db.keys()}
        
        # 遍歷資料庫尋找進化關係
        for name, data in db.items():
            evo_data = data.get("evolution")
            
            # 如果這隻怪獸有進化資訊
            if evo_data:
                next_id = evo_data.get("next_id")
                level_req = evo_data.get("level")
                
                # 更新下一階怪獸的最低等級限制
                if next_id and level_req:
                    # 如果資料庫裡有這隻怪獸，就更新它的最低等級
                    if next_id in min_levels:
                        min_levels[next_id] = level_req
                        
        return min_levels