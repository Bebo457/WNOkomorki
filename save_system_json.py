import json
import numpy as np
import os
import pygame
import shared
from bridge import Bridge
from cell import Cell
from unit import Unit



class SaveSystemJSON:
    def __init__(self, level):
        self.level = level
        self.save_directory = "json_saves"
        self.save_filename = "game_save.json"
        self.save_path = os.path.join(self.save_directory, self.save_filename)

        # Create save directory if it doesn't exist
        if not os.path.exists(self.save_directory):
            os.makedirs(self.save_directory)

    def convert_to_serializable(self, data):
        """Konwertuje obiekty NumPy array i inne niestandardowe typy na typy serializowalne."""
        if isinstance(data, np.ndarray):
            return data.tolist()
        elif isinstance(data, (np.int_, np.intc, np.intp, np.int8, np.int16, np.int32, np.int64)):
            return int(data)
        elif isinstance(data, (np.float_, np.float16, np.float32, np.float64)):
            return float(data)
        elif isinstance(data, dict):
            return {k: self.convert_to_serializable(v) for k, v in data.items()}
        elif isinstance(data, list) or isinstance(data, tuple):
            return [self.convert_to_serializable(item) for item in data]
        return data

    def save_game(self, return_data=False):
        """Save the current game state to a JSON file or return data structure if return_data=True"""
        try:
            # Create data structure
            game_data = {
                "shared_variables": {
                    "game_state": shared.game_state,
                    "game_mode": shared.game_mode,
                    "ip_address": shared.ip_address if hasattr(shared, "ip_address") else "127.0.0.1",
                    "port": shared.port if hasattr(shared, "port") else 8080
                },
                "level_data": {
                    "active_player": self.level.active_player,
                    "stage": self.level.stage,
                    "players": [],
                    "cells": [],
                    "bridges": [],
                    "ui_state": {},
                    "ai_state": {}
                }
            }

            # Save players data
            for i, player in enumerate(self.level.players):
                player_data = {
                    "id": i,
                    "color": player.color,
                    "coins": float(player.coins),
                    "timer": float(player.timer),
                    "lost": player.lost
                }
                game_data["level_data"]["players"].append(player_data)

            # Save cells data
            cells_dict = {}  # For bridge references
            for cell in self.level.cells:
                cell_data = {
                    "id": cell.id,
                    "type": cell.type,
                    "power": float(cell.power),
                    "tier": cell.tier,
                    "color": cell.color,
                    "position": self.convert_to_serializable(cell.position),
                    "activated_connection": cell.activated_connection,
                    "enemy_connections": cell.enemy_connections,
                    "last_attacked_by": str(cell.last_attacked_by),
                    "will_move": cell.will_move,
                    "new_pos": self.convert_to_serializable(cell.new_pos),
                    "has_any_bridge": cell.has_any_bridge,
                    "ghost_bridges": []
                }

                # Save ghost bridges
                for ghost_bridge in cell.ghost_bridges:
                    ghost_bridge_data = {
                        "start_cell_id": ghost_bridge[0].id,
                        "end_cell_id": ghost_bridge[1].id
                    }
                    cell_data["ghost_bridges"].append(ghost_bridge_data)

                cells_dict[cell.id] = cell
                game_data["level_data"]["cells"].append(cell_data)

            # Save bridges data
            bridge_count = 0
            for cell in self.level.cells:
                for bridge in cell.bridges:
                    bridge_data = {
                        "id": bridge_count,
                        "parent_id": bridge.parent.id,
                        "destination_id": bridge.destination.id,
                        "color": bridge.color,
                        "length": float(bridge.length),
                        "len": float(bridge.len),
                        "len_px": int(bridge.len_px),
                        "finished": bridge.finished,
                        "comp_len_px": float(bridge.comp_len_px),
                        "stored_power": float(bridge.stored_power),
                        "is_half_bridge": bridge.is_half_bridge,
                        "collapse": bridge.collapse,
                        "thickness": int(bridge.thickness),
                        "gap_length": int(bridge.gap_length),
                        "spawn_cooldown": float(bridge.spawn_cooldown),
                        "can_spawn_this_turn": bridge.can_spawn_this_turn,
                        "pvp_units": int(bridge.pvp_units),
                        "units": []
                    }

                    # Save enemy_bridge reference if it exists
                    if bridge.enemy_bridge is not None:
                        # Find the bridge's index in its parent's bridges list
                        for idx, other_bridge in enumerate(bridge.enemy_bridge.parent.bridges):
                            if other_bridge is bridge.enemy_bridge:
                                bridge_data["enemy_bridge_parent_id"] = bridge.enemy_bridge.parent.id
                                bridge_data["enemy_bridge_index"] = idx
                                break

                    # Save units on the bridge
                    for unit in bridge.units:
                        unit_data = {
                            "position": self.convert_to_serializable(unit.position),
                            "radius": float(unit.radius),
                            "dead": unit.dead,
                            "color": [unit.color[0], unit.color[1], unit.color[2]]
                        }
                        bridge_data["units"].append(unit_data)

                    game_data["level_data"]["bridges"].append(bridge_data)
                    bridge_count += 1

            # Save level UI state
            ui_state = {
                "activated_cell_connection": self.level.activated_cell_connection,
                "clicked_cell_id": self.level.clicked_cell_id,
                "lock": self.level.lock,
                "cutting": self.level.cutting,
                "is_shop_open": self.level.is_shop_open,
                "placing_cell": str(self.level.placing_cell),
                "context_on": self.level.context_on
            }

            # Save cutting start position if cutting is active
            if self.level.cutting:
                ui_state["cutting_start_pos"] = {
                    "x": float(self.level.cutting_start_pos[0]),
                    "y": float(self.level.cutting_start_pos[1])
                }

            game_data["level_data"]["ui_state"] = ui_state

            # Save AI state
            game_data["level_data"]["ai_state"] = {
                "action_timer": float(self.level.AI.action_timer)
            }

            # Jeśli return_data=True, zwróć dane zamiast zapisywać do pliku
            if return_data:
                return game_data

            # Write data to file as JSON
            with open(self.save_path, 'w', encoding='utf-8') as f:
                json.dump(self.convert_to_serializable(game_data), f, ensure_ascii=False, indent=4)

            print(f"Game saved successfully to {self.save_path}")
            return True

        except Exception as e:
            print(f"Error saving game: {e}")
            import traceback
            traceback.print_exc()
            return False if not return_data else None

    def load_game_from_data(self, game_data):
        """Load game state from provided data structure instead of a file"""

        try:
            # Load shared variables
            shared_vars = game_data["shared_variables"]
            shared.game_state = shared_vars["game_state"]
            shared.game_mode = shared_vars["game_mode"]
            shared.ip_address = shared_vars["ip_address"]
            shared.port = int(shared_vars["port"])

            # zmienna, która upewnia się że po odczytaniu danych w trybie
            # online będzie odpowiedni stan gry, nieważne co
            shared.target_game_state = game_data["shared_variables"]["game_state"]

            # First, reset the level
            self.level.reinit()

            # Load level data
            level_data = game_data["level_data"]

            # Load stage
            self.level.stage = int(level_data["stage"])

            # Load active player
            self.level.active_player = int(level_data["active_player"])

            # Load players data
            players_data = level_data["players"]
            for i, player_data in enumerate(players_data):
                if i < len(self.level.players):
                    self.level.players[i].color = player_data["color"]
                    self.level.players[i].coins = float(player_data["coins"])
                    self.level.players[i].timer = float(player_data["timer"])
                    self.level.players[i].lost = player_data["lost"]

            # Load cells data
            cells_dict = {}  # To store cells by ID for bridge references
            cells_data = level_data["cells"]

            for cell_data in cells_data:
                cell_id = int(cell_data["id"])
                cell_type = cell_data["type"]
                power = float(cell_data["power"])
                tier = int(cell_data["tier"])
                color = cell_data["color"]

                # Load position
                position = np.array(cell_data["position"])

                # Create cell
                cell = Cell(cell_type, power, tier, color, position, cell_id)

                # Load additional properties
                cell.activated_connection = cell_data["activated_connection"]
                cell.enemy_connections = int(cell_data["enemy_connections"])

                last_attacked_by = cell_data["last_attacked_by"]
                cell.last_attacked_by = None if last_attacked_by == "None" else last_attacked_by

                cell.will_move = cell_data["will_move"]
                cell.new_pos = np.array(cell_data["new_pos"])
                cell.has_any_bridge = cell_data["has_any_bridge"]

                # Store cell in our dictionary and add to level
                cells_dict[cell_id] = cell
                self.level.cells.append(cell)

            # Now load bridges
            bridges_dict = {}  # To store bridges for enemy_bridge references
            bridges_data = level_data["bridges"]

            for bridge_data in bridges_data:
                bridge_id = int(bridge_data["id"])
                parent_id = int(bridge_data["parent_id"])
                destination_id = int(bridge_data["destination_id"])

                # Get parent and destination cells
                parent_cell = cells_dict[parent_id]
                destination_cell = cells_dict[destination_id]

                # Create bridge
                bridge = Bridge(parent_cell, destination_cell)

                # Set bridge properties
                bridge.color = bridge_data["color"]
                bridge.length = float(bridge_data["length"])
                bridge.len = float(bridge_data["len"])
                bridge.len_px = int(bridge_data["len_px"])
                bridge.finished = bridge_data["finished"]
                bridge.comp_len_px = float(bridge_data["comp_len_px"])
                bridge.stored_power = float(bridge_data["stored_power"])
                bridge.is_half_bridge = bridge_data["is_half_bridge"]
                bridge.collapse = bridge_data["collapse"]
                bridge.thickness = int(bridge_data["thickness"])
                bridge.gap_length = int(bridge_data["gap_length"])
                bridge.spawn_cooldown = float(bridge_data["spawn_cooldown"])
                bridge.can_spawn_this_turn = bridge_data["can_spawn_this_turn"]
                bridge.pvp_units = int(bridge_data["pvp_units"])

                # Store the bridge for enemy_bridge references
                bridges_dict[bridge_id] = {
                    "bridge": bridge,
                    "enemy_bridge_parent_id": bridge_data.get("enemy_bridge_parent_id"),
                    "enemy_bridge_index": bridge_data.get("enemy_bridge_index")
                }

                # Load units on the bridge
                units_data = bridge_data.get("units", [])
                for unit_data in units_data:
                    # Create unit
                    unit = Unit(bridge)
                    unit.position = np.array(unit_data["position"])
                    unit.radius = float(unit_data["radius"])
                    unit.dead = unit_data["dead"]

                    # Load color (RGB tuple)
                    color_data = unit_data["color"]
                    unit.color = tuple(color_data)

                    # Add unit to bridge
                    bridge.units.append(unit)

                # Add bridge to parent cell
                parent_cell.bridges.append(bridge)

            # Second pass to set enemy_bridge references
            for bridge_info in bridges_dict.values():
                bridge = bridge_info["bridge"]
                parent_id = bridge_info.get("enemy_bridge_parent_id")
                index = bridge_info.get("enemy_bridge_index")

                if parent_id is not None and index is not None:
                    if parent_id in cells_dict and 0 <= index < len(cells_dict[parent_id].bridges):
                        bridge.enemy_bridge = cells_dict[parent_id].bridges[index]

            # Load ghost bridges
            for cell_data in cells_data:
                cell_id = int(cell_data["id"])
                cell = cells_dict[cell_id]

                ghost_bridges_data = cell_data.get("ghost_bridges", [])
                for ghost_bridge_data in ghost_bridges_data:
                    start_cell_id = int(ghost_bridge_data["start_cell_id"])
                    end_cell_id = int(ghost_bridge_data["end_cell_id"])

                    if start_cell_id in cells_dict and end_cell_id in cells_dict:
                        cell.ghost_bridges.append((cells_dict[start_cell_id], cells_dict[end_cell_id]))

            # Load UI state
            ui_state = level_data["ui_state"]
            self.level.activated_cell_connection = ui_state["activated_cell_connection"]
            self.level.clicked_cell_id = int(ui_state["clicked_cell_id"])
            self.level.lock = ui_state["lock"]
            self.level.cutting = ui_state["cutting"]

            # Load cutting start position if it exists
            cutting_pos = ui_state.get("cutting_start_pos")
            if cutting_pos:
                self.level.cutting_start_pos = (
                    float(cutting_pos["x"]),
                    float(cutting_pos["y"])
                )

            self.level.is_shop_open = ui_state["is_shop_open"]

            placing_cell = ui_state["placing_cell"]
            self.level.placing_cell = None if placing_cell == "None" else placing_cell

            self.level.context_on = ui_state["context_on"]

            # Load AI state
            ai_state = level_data["ai_state"]
            if ai_state:
                self.level.AI.action_timer = float(ai_state["action_timer"])

            # Setup UI based on game state
            if shared.game_state == 'pvp_setup':
                shared.pvp_menu.enable()
                shared.timer_menu.enable()
                if self.level.is_shop_open:
                    self.level.shop_menu.enable()
            elif shared.game_state == 'pvp_turn':
                shared.timer_menu.enable()
                self.level.pvp_main_menu.enable()
            elif shared.game_state == 'level_classic':
                self.level.classic_mode_menu.enable()
            else:
                pass

            print(f"Game loaded successfully from data structure")
            return True

        except Exception as e:
            print(f"Error loading game from data: {e}")
            import traceback
            traceback.print_exc()
            return False

    def load_game(self):
        """Load game state from the JSON file"""
        try:
            if not os.path.exists(self.save_path):
                print(f"Save file not found: {self.save_path}")
                return False

            # Load JSON file
            with open(self.save_path, 'r', encoding='utf-8') as f:
                game_data = json.load(f)

            # Load shared variables
            shared_vars = game_data["shared_variables"]
            shared.game_state = shared_vars["game_state"]
            shared.game_mode = shared_vars["game_mode"]
            shared.ip_address = shared_vars["ip_address"]
            shared.port = int(shared_vars["port"])

            # First, reset the level
            self.level.reinit()

            # Load level data
            level_data = game_data["level_data"]

            # Load stage
            self.level.stage = int(level_data["stage"])

            # Load active player
            self.level.active_player = int(level_data["active_player"])

            # Load players data
            players_data = level_data["players"]
            for i, player_data in enumerate(players_data):
                if i < len(self.level.players):
                    self.level.players[i].color = player_data["color"]
                    self.level.players[i].coins = float(player_data["coins"])
                    self.level.players[i].timer = float(player_data["timer"])
                    self.level.players[i].lost = player_data["lost"]

            # Load cells data
            cells_dict = {}  # To store cells by ID for bridge references
            cells_data = level_data["cells"]

            for cell_data in cells_data:
                cell_id = int(cell_data["id"])
                cell_type = cell_data["type"]
                power = float(cell_data["power"])
                tier = int(cell_data["tier"])
                color = cell_data["color"]

                # Load position
                position = np.array(cell_data["position"])

                # Create cell
                cell = Cell(cell_type, power, tier, color, position, cell_id)

                # Load additional properties
                cell.activated_connection = cell_data["activated_connection"]
                cell.enemy_connections = int(cell_data["enemy_connections"])

                last_attacked_by = cell_data["last_attacked_by"]
                cell.last_attacked_by = None if last_attacked_by == "None" else last_attacked_by

                cell.will_move = cell_data["will_move"]
                cell.new_pos = np.array(cell_data["new_pos"])
                cell.has_any_bridge = cell_data["has_any_bridge"]

                # Store cell in our dictionary and add to level
                cells_dict[cell_id] = cell
                self.level.cells.append(cell)

            # Now load bridges
            bridges_dict = {}  # To store bridges for enemy_bridge references
            bridges_data = level_data["bridges"]

            for bridge_data in bridges_data:
                bridge_id = int(bridge_data["id"])
                parent_id = int(bridge_data["parent_id"])
                destination_id = int(bridge_data["destination_id"])

                # Get parent and destination cells
                parent_cell = cells_dict[parent_id]
                destination_cell = cells_dict[destination_id]

                # Create bridge
                bridge = Bridge(parent_cell, destination_cell)

                # Set bridge properties
                bridge.color = bridge_data["color"]
                bridge.length = float(bridge_data["length"])
                bridge.len = float(bridge_data["len"])
                bridge.len_px = int(bridge_data["len_px"])
                bridge.finished = bridge_data["finished"]
                bridge.comp_len_px = float(bridge_data["comp_len_px"])
                bridge.stored_power = float(bridge_data["stored_power"])
                bridge.is_half_bridge = bridge_data["is_half_bridge"]
                bridge.collapse = bridge_data["collapse"]
                bridge.thickness = int(bridge_data["thickness"])
                bridge.gap_length = int(bridge_data["gap_length"])
                bridge.spawn_cooldown = float(bridge_data["spawn_cooldown"])
                bridge.can_spawn_this_turn = bridge_data["can_spawn_this_turn"]
                bridge.pvp_units = int(bridge_data["pvp_units"])

                # Store the bridge for enemy_bridge references
                bridges_dict[bridge_id] = {
                    "bridge": bridge,
                    "enemy_bridge_parent_id": bridge_data.get("enemy_bridge_parent_id"),
                    "enemy_bridge_index": bridge_data.get("enemy_bridge_index")
                }

                # Load units on the bridge
                units_data = bridge_data.get("units", [])
                for unit_data in units_data:
                    # Create unit
                    unit = Unit(bridge)
                    unit.position = np.array(unit_data["position"])
                    unit.radius = float(unit_data["radius"])
                    unit.dead = unit_data["dead"]

                    # Load color (RGB tuple)
                    color_data = unit_data["color"]
                    unit.color = tuple(color_data)

                    # Add unit to bridge
                    bridge.units.append(unit)

                # Add bridge to parent cell
                parent_cell.bridges.append(bridge)

            # Second pass to set enemy_bridge references
            for bridge_info in bridges_dict.values():
                bridge = bridge_info["bridge"]
                parent_id = bridge_info.get("enemy_bridge_parent_id")
                index = bridge_info.get("enemy_bridge_index")

                if parent_id is not None and index is not None:
                    if parent_id in cells_dict and 0 <= index < len(cells_dict[parent_id].bridges):
                        bridge.enemy_bridge = cells_dict[parent_id].bridges[index]

            # Load ghost bridges
            for cell_data in cells_data:
                cell_id = int(cell_data["id"])
                cell = cells_dict[cell_id]

                ghost_bridges_data = cell_data.get("ghost_bridges", [])
                for ghost_bridge_data in ghost_bridges_data:
                    start_cell_id = int(ghost_bridge_data["start_cell_id"])
                    end_cell_id = int(ghost_bridge_data["end_cell_id"])

                    if start_cell_id in cells_dict and end_cell_id in cells_dict:
                        cell.ghost_bridges.append((cells_dict[start_cell_id], cells_dict[end_cell_id]))

            # Load UI state
            ui_state = level_data["ui_state"]
            self.level.activated_cell_connection = ui_state["activated_cell_connection"]
            self.level.clicked_cell_id = int(ui_state["clicked_cell_id"])
            self.level.lock = ui_state["lock"]
            self.level.cutting = ui_state["cutting"]

            # Load cutting start position if it exists
            cutting_pos = ui_state.get("cutting_start_pos")
            if cutting_pos:
                self.level.cutting_start_pos = (
                    float(cutting_pos["x"]),
                    float(cutting_pos["y"])
                )

            self.level.is_shop_open = ui_state["is_shop_open"]

            placing_cell = ui_state["placing_cell"]
            self.level.placing_cell = None if placing_cell == "None" else placing_cell

            self.level.context_on = ui_state["context_on"]

            # Load AI state
            ai_state = level_data["ai_state"]
            if ai_state:
                self.level.AI.action_timer = float(ai_state["action_timer"])

            # Setup UI based on game state
            if shared.game_state == 'pvp_setup':
                shared.pvp_menu.enable()
                shared.timer_menu.enable()
                if self.level.is_shop_open:
                    self.level.shop_menu.enable()
            elif shared.game_state == 'pvp_turn':
                shared.timer_menu.enable()
                self.level.pvp_main_menu.enable()
            elif shared.game_state == 'level_classic':
                self.level.classic_mode_menu.enable()

            print(f"Game loaded successfully from {self.save_path}")
            return True

        except Exception as e:
            print(f"Error loading game: {e}")
            import traceback
            traceback.print_exc()
            return False

    def load_game_from_data2(self, game_data):
        """Load game state from provided data structure instead of a file"""
        try:
            # Load shared variables
            shared_vars = game_data["shared_variables"]
            shared.game_mode = shared_vars["game_mode"]
            shared.ip_address = shared_vars["ip_address"]
            shared.port = int(shared_vars["port"])

            # First, reset the level
            self.level.reinit()

            # Load level data
            level_data = game_data["level_data"]

            # Load stage
            self.level.stage = int(level_data["stage"])

            # Load active player
            self.level.active_player = int(level_data["active_player"])

            # Load players data
            players_data = level_data["players"]
            for i, player_data in enumerate(players_data):
                if i < len(self.level.players):
                    self.level.players[i].color = player_data["color"]
                    self.level.players[i].coins = float(player_data["coins"])
                    self.level.players[i].timer = float(player_data["timer"])
                    self.level.players[i].lost = player_data["lost"]

            # Load cells data
            cells_dict = {}  # To store cells by ID for bridge references
            cells_data = level_data["cells"]

            for cell_data in cells_data:
                cell_id = int(cell_data["id"])
                cell_type = cell_data["type"]
                power = float(cell_data["power"])
                tier = int(cell_data["tier"])
                color = cell_data["color"]

                # Load position
                position = np.array(cell_data["position"])

                # Create cell
                cell = Cell(cell_type, power, tier, color, position, cell_id)

                # Load additional properties
                cell.activated_connection = cell_data["activated_connection"]
                cell.enemy_connections = int(cell_data["enemy_connections"])

                last_attacked_by = cell_data["last_attacked_by"]
                cell.last_attacked_by = None if last_attacked_by == "None" else last_attacked_by

                cell.will_move = cell_data["will_move"]
                cell.new_pos = np.array(cell_data["new_pos"])
                cell.has_any_bridge = cell_data["has_any_bridge"]

                # Store cell in our dictionary and add to level
                cells_dict[cell_id] = cell
                self.level.cells.append(cell)

            # Now load bridges
            bridges_dict = {}  # To store bridges for enemy_bridge references
            bridges_data = level_data["bridges"]

            for bridge_data in bridges_data:
                bridge_id = int(bridge_data["id"])
                parent_id = int(bridge_data["parent_id"])
                destination_id = int(bridge_data["destination_id"])

                # Get parent and destination cells
                parent_cell = cells_dict[parent_id]
                destination_cell = cells_dict[destination_id]

                # Create bridge
                bridge = Bridge(parent_cell, destination_cell)

                # Set bridge properties
                bridge.color = bridge_data["color"]
                bridge.length = float(bridge_data["length"])
                bridge.len = float(bridge_data["len"])
                bridge.len_px = int(bridge_data["len_px"])
                bridge.finished = bridge_data["finished"]
                bridge.comp_len_px = float(bridge_data["comp_len_px"])
                bridge.stored_power = float(bridge_data["stored_power"])
                bridge.is_half_bridge = bridge_data["is_half_bridge"]
                bridge.collapse = bridge_data["collapse"]
                bridge.thickness = int(bridge_data["thickness"])
                bridge.gap_length = int(bridge_data["gap_length"])
                bridge.spawn_cooldown = float(bridge_data["spawn_cooldown"])
                bridge.can_spawn_this_turn = bridge_data["can_spawn_this_turn"]
                bridge.pvp_units = int(bridge_data["pvp_units"])

                # Store the bridge for enemy_bridge references
                bridges_dict[bridge_id] = {
                    "bridge": bridge,
                    "enemy_bridge_parent_id": bridge_data.get("enemy_bridge_parent_id"),
                    "enemy_bridge_index": bridge_data.get("enemy_bridge_index")
                }

                # Load units on the bridge
                units_data = bridge_data.get("units", [])
                for unit_data in units_data:
                    # Create unit
                    unit = Unit(bridge)
                    unit.position = np.array(unit_data["position"])
                    unit.radius = float(unit_data["radius"])
                    unit.dead = unit_data["dead"]

                    # Load color (RGB tuple)
                    color_data = unit_data["color"]
                    unit.color = tuple(color_data)

                    # Add unit to bridge
                    bridge.units.append(unit)

                # Add bridge to parent cell
                parent_cell.bridges.append(bridge)

            # Second pass to set enemy_bridge references
            for bridge_info in bridges_dict.values():
                bridge = bridge_info["bridge"]
                parent_id = bridge_info.get("enemy_bridge_parent_id")
                index = bridge_info.get("enemy_bridge_index")

                if parent_id is not None and index is not None:
                    if parent_id in cells_dict and 0 <= index < len(cells_dict[parent_id].bridges):
                        bridge.enemy_bridge = cells_dict[parent_id].bridges[index]

            # Load ghost bridges
            for cell_data in cells_data:
                cell_id = int(cell_data["id"])
                cell = cells_dict[cell_id]

                ghost_bridges_data = cell_data.get("ghost_bridges", [])
                for ghost_bridge_data in ghost_bridges_data:
                    start_cell_id = int(ghost_bridge_data["start_cell_id"])
                    end_cell_id = int(ghost_bridge_data["end_cell_id"])

                    if start_cell_id in cells_dict and end_cell_id in cells_dict:
                        cell.ghost_bridges.append((cells_dict[start_cell_id], cells_dict[end_cell_id]))

            # Load UI state
            ui_state = level_data["ui_state"]
            self.level.activated_cell_connection = ui_state["activated_cell_connection"]
            self.level.clicked_cell_id = int(ui_state["clicked_cell_id"])
            self.level.lock = ui_state["lock"]
            self.level.cutting = ui_state["cutting"]

            # Load cutting start position if it exists
            cutting_pos = ui_state.get("cutting_start_pos")
            if cutting_pos:
                self.level.cutting_start_pos = (
                    float(cutting_pos["x"]),
                    float(cutting_pos["y"])
                )

            self.level.is_shop_open = ui_state["is_shop_open"]

            placing_cell = ui_state["placing_cell"]
            self.level.placing_cell = None if placing_cell == "None" else placing_cell

            self.level.context_on = ui_state["context_on"]

            # Load AI state
            ai_state = level_data["ai_state"]
            if ai_state:
                self.level.AI.action_timer = float(ai_state["action_timer"])

            # Setup UI based on game state
            if shared.game_state == 'pvp_setup':
                shared.pvp_menu.enable()
                shared.timer_menu.enable()
                if self.level.is_shop_open:
                    self.level.shop_menu.enable()
            elif shared.game_state == 'pvp_turn':
                shared.timer_menu.enable()
                self.level.pvp_main_menu.enable()
            elif shared.game_state == 'level_classic':
                self.level.classic_mode_menu.enable()

            print(f"Game loaded successfully from data structure")
            return True

        except Exception as e:
            print(f"Error loading game from data: {e}")
            import traceback
            traceback.print_exc()
            return False