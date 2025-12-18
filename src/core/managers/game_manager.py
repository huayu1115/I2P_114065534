from __future__ import annotations
from src.utils import Logger, GameSettings, Position, Teleport
import json, os
import pygame as pg
from typing import TYPE_CHECKING
import shutil

if TYPE_CHECKING:
    from src.maps.map import Map
    from src.entities.player import Player
    from src.entities.enemy_trainer import EnemyTrainer
    from src.entities.merchant import Merchant
    from src.data.bag import Bag

class GameManager:
    # Entities
    player: Player | None
    enemy_trainers: dict[str, list[EnemyTrainer]]
    merchants: dict[str, list[Merchant]]
    bag: "Bag"

    # Databases
    item_database: dict[str, dict]
    monster_database: dict[str, dict]
    trainer_database: dict[str, dict]
    
    # Map properties
    current_map_key: str
    maps: dict[str, Map]
    
    # Changing Scene properties
    should_change_scene: bool
    next_map: str
    player_last_positions: dict[str, Position]
    player_spawns: dict[str, Position]
    
    def __init__(self, maps: dict[str, Map], start_map: str, 
                 player: Player | None,
                 enemy_trainers: dict[str, list[EnemyTrainer]], 
                 merchants: dict[str, list[Merchant]],
                 bag: Bag | None = None):
                     
        from src.data.bag import Bag
        # Game Properties
        self.maps = maps
        self.current_map_key = start_map
        self.player = player
        self.enemy_trainers = enemy_trainers
        self.merchants = merchants
        self.bag = bag if bag is not None else Bag([], [])

        self.item_database = self._load_database("src/data/items.json")
        self.monster_database = self._load_database("src/data/monsters.json")
        self.trainer_database = self._load_database("src/data/trainers.json")
        
        # Check If you should change scene
        self.should_change_scene = False
        self.next_map = ""
        self.player_last_positions = {}
        self.player_spawns = {}
        
    @property
    def current_map(self) -> Map:
        return self.maps[self.current_map_key]
        
    @property
    def current_enemy_trainers(self) -> list[EnemyTrainer]:
        return self.enemy_trainers[self.current_map_key]
        
    @property
    def current_teleporter(self) -> list[Teleport]:
        return self.maps[self.current_map_key].teleporters
    
    def switch_map(self, target: str) -> None:
        if target not in self.maps:
            Logger.warning(f"Map '{target}' not loaded; cannot switch.")
            return
        if self.player:
            current_map = self.current_map_key
            self.player_last_positions[current_map] = self.player.position.copy()
        
        self.next_map = target
        self.should_change_scene = True
            
    def try_switch_map(self) -> None:
        if self.should_change_scene:
            self.current_map_key = self.next_map
            self.next_map = ""
            self.should_change_scene = False
            if self.player:
                if self.current_map_key in self.player_last_positions:
                    self.player.position = self.player_last_positions[self.current_map_key]
                    if self.current_map_key == "map.tmx": 
                        self.player.position.y += GameSettings.TILE_SIZE
                else:
                    self.player.position = self.maps[self.current_map_key].spawn
            
    def check_collision(self, rect: pg.Rect) -> bool:
        if self.maps[self.current_map_key].check_collision(rect):
            return True
        for entity in self.enemy_trainers[self.current_map_key]:
            if rect.colliderect(entity.animation.rect):
                return True
        for entity in self.merchants[self.current_map_key]:
            if rect.colliderect(entity.animation.rect):
                return True
        return False
        
    def save(self, path: str) -> None:
        '''
        check point 2 - 4: Setting Overlay 存檔功能
        存檔功能: 先寫入暫存檔，確認寫入成功後再覆蓋原檔，避免寫入中斷導致檔案損毀
        '''
        tmp_path = f"{path}.tmp"
        try:
            with open(tmp_path, "w") as f:
                json.dump(self.to_dict(), f, indent=2)
            if os.path.exists(path): # 如果寫入成功，覆蓋舊檔
                os.remove(path)
            os.rename(tmp_path, path)
            Logger.info(f"Game saved to {path}")
        except Exception as e:
            if os.path.exists(tmp_path): # 如果失敗，刪除殘留的暫存檔
                os.remove(tmp_path)
            Logger.warning(f"Failed to save game: {e}")
             
    @classmethod
    def load(cls, path: str) -> "GameManager | None":
        '''
        check point 2 - 4: Setting Overlay 讀檔功能
        讀檔功能: 如果檔案為空或是找不到檔案, 則從backup恢復
        '''
        data = None
        backup_path = "saves/backup.json"

        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    content = f.read()
                    if not content.strip(): # 檢查檔案是否完全空白
                        raise json.JSONDecodeError("Empty file", "", 0)                  
                    f.seek(0)
                    data = json.load(f)                 
            except (json.JSONDecodeError, Exception) as e:
                Logger.warning(f"Failed to load {path} (Error: {e}). Trying backup...")
                data = None 
        else:
            Logger.warning(f"File {path} not found. Trying backup...")

        ## 從備份恢復 game0.json
        if data is None:
            if os.path.exists(backup_path):
                try:
                    Logger.info(f"Loading from backup: {backup_path}")
                    with open(backup_path, "r") as f:
                        data = json.load(f)
                    try:
                        shutil.copy(backup_path, path) # 複製 backup.json 到 game0.json
                        Logger.info(f"Restored {path} using {backup_path}")
                    except Exception as copy_error:
                        Logger.warning(f"Could not restore file: {copy_error}")

                except Exception as e:
                    Logger.error(f"Backup file is also corrupted or missing: {e}")
                    return None
            else:
                Logger.error(f"No backup file found at {backup_path}")
                return None

        return cls.from_dict(data)

    def to_dict(self) -> dict[str, object]:
        '''
        check point 2 - 4: Setting Overlay 保存玩家位置
        將當前遊戲狀態轉換為符合 game0.json 格式的字典
        包含: Map 列表(含傳送點、敵人、該地圖玩家位置)、全域玩家資料、背包資料。
        '''
        map_blocks: list[dict[str, object]] = []

        if self.player: # 將當前位置存入 player_spawns 字典
            self.player_spawns[self.current_map_key] = self.player.position

        for key, m in self.maps.items():
            block = m.to_dict()
            block["enemy_trainers"] = [t.to_dict() for t in self.enemy_trainers.get(key, [])]
            block["merchants"] = [t.to_dict() for t in self.merchants.get(key, [])]
            # 取得該地圖對應的座標
            saved_pos = self.player_spawns.get(key)
            if saved_pos is None:
                saved_pos = m.spawn

            ## 將像素座標轉回網格座標存入 JSON
            block["player"] = {
                "x": int(saved_pos.x / GameSettings.TILE_SIZE),
                "y": int(saved_pos.y / GameSettings.TILE_SIZE)
            }
            map_blocks.append(block)

        return {
            "map": map_blocks,
            "current_map": self.current_map_key,
            "player": self.player.to_dict() if self.player is not None else None,
            "bag": self.bag.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "GameManager":
        from src.maps.map import Map
        from src.entities.player import Player
        from src.entities.enemy_trainer import EnemyTrainer
        from src.entities.merchant import Merchant
        from src.data.bag import Bag
        
        Logger.info("Loading maps")
        maps_data = data["map"]
        maps: dict[str, Map] = {}
        player_spawns: dict[str, Position] = {}
        trainers: dict[str, list[EnemyTrainer]] = {}
        merchants: dict[str, list[Merchant]] = {}

        for entry in maps_data:
            path = entry["path"]
            maps[path] = Map.from_dict(entry)
            sp = entry.get("player")
            if sp:
                player_spawns[path] = Position(
                    sp["x"] * GameSettings.TILE_SIZE,
                    sp["y"] * GameSettings.TILE_SIZE
                )
        current_map = data["current_map"]
        gm = cls(
            maps, current_map,
            None, # Player
            trainers,
            merchants,
            bag=None
        )
        gm.player_spawns = player_spawns
        gm.current_map_key = current_map
        
        Logger.info("Loading enemy trainers")
        for m in data["map"]:
            raw_data = m["enemy_trainers"]
            gm.enemy_trainers[m["path"]] = [EnemyTrainer.from_dict(t, gm) for t in raw_data]
        
        Logger.info("Loading merchants")
        for m in data["map"]:
            raw_data = m["merchants"]
            gm.merchants[m["path"]] = [Merchant.from_dict(t, gm) for t in raw_data]
        
        Logger.info("Loading Player")
        if data.get("player"):
            gm.player = Player.from_dict(data["player"], gm)
        
        Logger.info("Loading bag")
        from src.data.bag import Bag as _Bag
        gm.bag = Bag.from_dict(data.get("bag", {})) if data.get("bag") else _Bag([], [])

        return gm
    
    def _load_database(self, path: str) -> dict:
        try:
            if os.path.exists(path):
                with open(path, "r", encoding='utf-8') as f:
                    data = json.load(f)
                    Logger.info(f"Loaded database: {path}")
                    return data
            else:
                Logger.warning(f"Database not found at {path}")
                return {}
        except Exception as e:
            Logger.error(f"Failed to load database {path}: {e}")
            return {}