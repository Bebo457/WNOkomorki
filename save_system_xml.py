import xml.etree.ElementTree as ET
import numpy as np
import os
import pygame
import shared
from bridge import Bridge
from cell import Cell
from unit import Unit



class SaveSystemXML:
    def __init__(self, level):
        self.level = level
        self.save_directory = "saves"
        self.save_filename = "game_save.xml"
        self.save_path = os.path.join(self.save_directory, self.save_filename)

        # Create save directory if it doesn't exist
        if not os.path.exists(self.save_directory):
            os.makedirs(self.save_directory)

    def save_game(self):
        """Save the current game state to an XML file"""
        try:
            # Create the root element
            root = ET.Element("game_save")

            # Save shared game variables
            shared_vars = ET.SubElement(root, "shared_variables")
            ET.SubElement(shared_vars, "game_state").text = shared.game_state
            ET.SubElement(shared_vars, "game_mode").text = shared.game_mode
            ET.SubElement(shared_vars, "ip_address").text = shared.ip_address if hasattr(shared,"ip_address") else "127.0.0.1"
            ET.SubElement(shared_vars, "port").text = str(shared.port) if hasattr(shared, "port") else "8080"

            # Save level data
            level_data = ET.SubElement(root, "level_data")

            # Save active player
            ET.SubElement(level_data, "active_player").text = str(self.level.active_player)

            # Save stage
            ET.SubElement(level_data, "stage").text = str(self.level.stage)

            # Save players data
            players = ET.SubElement(level_data, "players")
            for i, player in enumerate(self.level.players):
                player_elem = ET.SubElement(players, "player")
                ET.SubElement(player_elem, "id").text = str(i)
                ET.SubElement(player_elem, "color").text = player.color
                ET.SubElement(player_elem, "coins").text = str(player.coins)
                ET.SubElement(player_elem, "timer").text = str(player.timer)
                ET.SubElement(player_elem, "lost").text = str(player.lost)

            # Save cells data
            cells = ET.SubElement(level_data, "cells")
            for cell in self.level.cells:
                cell_elem = ET.SubElement(cells, "cell")
                ET.SubElement(cell_elem, "id").text = str(cell.id)
                ET.SubElement(cell_elem, "type").text = cell.type
                ET.SubElement(cell_elem, "power").text = str(cell.power)
                ET.SubElement(cell_elem, "tier").text = str(cell.tier)
                ET.SubElement(cell_elem, "color").text = cell.color

                # Save position as x,y
                position = ET.SubElement(cell_elem, "position")
                ET.SubElement(position, "x").text = str(cell.position[0])
                ET.SubElement(position, "y").text = str(cell.position[1])

                # Save other cell properties
                ET.SubElement(cell_elem, "activated_connection").text = str(cell.activated_connection)
                ET.SubElement(cell_elem, "enemy_connections").text = str(cell.enemy_connections)
                ET.SubElement(cell_elem, "last_attacked_by").text = str(cell.last_attacked_by)
                ET.SubElement(cell_elem, "will_move").text = str(cell.will_move)

                # Save new_pos as x,y
                new_pos = ET.SubElement(cell_elem, "new_pos")
                ET.SubElement(new_pos, "x").text = str(cell.new_pos[0])
                ET.SubElement(new_pos, "y").text = str(cell.new_pos[1])

                ET.SubElement(cell_elem, "has_any_bridge").text = str(cell.has_any_bridge)

                # Save ghost bridges
                ghost_bridges = ET.SubElement(cell_elem, "ghost_bridges")
                for ghost_bridge in cell.ghost_bridges:
                    ghost_bridge_elem = ET.SubElement(ghost_bridges, "ghost_bridge")
                    ET.SubElement(ghost_bridge_elem, "start_cell_id").text = str(ghost_bridge[0].id)
                    ET.SubElement(ghost_bridge_elem, "end_cell_id").text = str(ghost_bridge[1].id)

            # Save bridges data
            bridges = ET.SubElement(level_data, "bridges")
            bridge_count = 0
            for cell in self.level.cells:
                for bridge in cell.bridges:
                    bridge_elem = ET.SubElement(bridges, "bridge")
                    ET.SubElement(bridge_elem, "id").text = str(bridge_count)
                    bridge_count += 1
                    ET.SubElement(bridge_elem, "parent_id").text = str(bridge.parent.id)
                    ET.SubElement(bridge_elem, "destination_id").text = str(bridge.destination.id)
                    ET.SubElement(bridge_elem, "color").text = bridge.color
                    ET.SubElement(bridge_elem, "length").text = str(bridge.length)
                    ET.SubElement(bridge_elem, "len").text = str(bridge.len)
                    ET.SubElement(bridge_elem, "len_px").text = str(bridge.len_px)
                    ET.SubElement(bridge_elem, "finished").text = str(bridge.finished)
                    ET.SubElement(bridge_elem, "comp_len_px").text = str(bridge.comp_len_px)
                    ET.SubElement(bridge_elem, "stored_power").text = str(bridge.stored_power)
                    ET.SubElement(bridge_elem, "is_half_bridge").text = str(bridge.is_half_bridge)
                    ET.SubElement(bridge_elem, "collapse").text = str(bridge.collapse)
                    ET.SubElement(bridge_elem, "thickness").text = str(bridge.thickness)
                    ET.SubElement(bridge_elem, "gap_length").text = str(bridge.gap_length)
                    ET.SubElement(bridge_elem, "spawn_cooldown").text = str(bridge.spawn_cooldown)
                    ET.SubElement(bridge_elem, "can_spawn_this_turn").text = str(bridge.can_spawn_this_turn)
                    ET.SubElement(bridge_elem, "pvp_units").text = str(bridge.pvp_units)

                    # Save enemy_bridge reference if it exists
                    if bridge.enemy_bridge is not None:
                        # Find the bridge's index in its parent's bridges list
                        for idx, other_bridge in enumerate(bridge.enemy_bridge.parent.bridges):
                            if other_bridge is bridge.enemy_bridge:
                                ET.SubElement(bridge_elem, "enemy_bridge_parent_id").text = str(
                                    bridge.enemy_bridge.parent.id)
                                ET.SubElement(bridge_elem, "enemy_bridge_index").text = str(idx)
                                break

                    # Save units on the bridge
                    units = ET.SubElement(bridge_elem, "units")
                    for unit in bridge.units:
                        unit_elem = ET.SubElement(units, "unit")

                        # Save position
                        position = ET.SubElement(unit_elem, "position")
                        ET.SubElement(position, "x").text = str(unit.position[0])
                        ET.SubElement(position, "y").text = str(unit.position[1])

                        ET.SubElement(unit_elem, "radius").text = str(unit.radius)
                        ET.SubElement(unit_elem, "dead").text = str(unit.dead)
                        ET.SubElement(unit_elem, "color").text = str(unit.color[0]) + "," + str(
                            unit.color[1]) + "," + str(unit.color[2])

            # Save level UI state
            ui_state = ET.SubElement(level_data, "ui_state")
            ET.SubElement(ui_state, "activated_cell_connection").text = str(self.level.activated_cell_connection)
            ET.SubElement(ui_state, "clicked_cell_id").text = str(self.level.clicked_cell_id)
            ET.SubElement(ui_state, "lock").text = str(self.level.lock)
            ET.SubElement(ui_state, "cutting").text = str(self.level.cutting)

            # Save cutting start position if cutting is active
            if self.level.cutting:
                cutting_pos = ET.SubElement(ui_state, "cutting_start_pos")
                ET.SubElement(cutting_pos, "x").text = str(self.level.cutting_start_pos[0])
                ET.SubElement(cutting_pos, "y").text = str(self.level.cutting_start_pos[1])

            ET.SubElement(ui_state, "is_shop_open").text = str(self.level.is_shop_open)
            ET.SubElement(ui_state, "placing_cell").text = str(self.level.placing_cell)
            ET.SubElement(ui_state, "context_on").text = str(self.level.context_on)

            # Save AI state if needed
            ai_state = ET.SubElement(level_data, "ai_state")
            ET.SubElement(ai_state, "action_timer").text = str(self.level.AI.action_timer)

            # Create XML tree and save to file
            tree = ET.ElementTree(root)
            tree.write(self.save_path, encoding="utf-8", xml_declaration=True)

            print(f"Game saved successfully to {self.save_path}")
            return True

        except Exception as e:
            print(f"Error saving game: {e}")
            return False

    def load_game(self):
        """Load game state from the XML file"""
        try:
            if not os.path.exists(self.save_path):
                print(f"Save file not found: {self.save_path}")
                return False

            # Parse the XML file
            tree = ET.parse(self.save_path)
            root = tree.getroot()

            # Load shared variables
            shared_vars = root.find("shared_variables")
            shared.game_state = shared_vars.find("game_state").text
            shared.game_mode = shared_vars.find("game_mode").text
            shared.ip_address = shared_vars.find("ip_address").text
            shared.port = int(shared_vars.find("port").text)

            # First, reset the level
            self.level.reinit()

            # Load level data
            level_data = root.find("level_data")

            # Load stage
            self.level.stage = int(level_data.find("stage").text)

            # Load active player
            self.level.active_player = int(level_data.find("active_player").text)

            # Load players data
            players_elem = level_data.find("players")
            for i, player_elem in enumerate(players_elem.findall("player")):
                self.level.players[i].color = player_elem.find("color").text
                self.level.players[i].coins = float(player_elem.find("coins").text)
                self.level.players[i].timer = float(player_elem.find("timer").text)
                self.level.players[i].lost = player_elem.find("lost").text.lower() == "true"

            # Load cells data
            cells_dict = {}  # To store cells by ID for bridge references
            cells_elem = level_data.find("cells")

            for cell_elem in cells_elem.findall("cell"):
                cell_id = int(cell_elem.find("id").text)
                cell_type = cell_elem.find("type").text
                power = float(cell_elem.find("power").text)
                tier = int(cell_elem.find("tier").text)
                color = cell_elem.find("color").text

                # Load position
                pos_elem = cell_elem.find("position")
                position = np.array([
                    float(pos_elem.find("x").text),
                    float(pos_elem.find("y").text)
                ])

                # Create cell
                cell = Cell(cell_type, power, tier, color, position, cell_id)

                # Load additional properties
                cell.activated_connection = cell_elem.find("activated_connection").text.lower() == "true"
                cell.enemy_connections = int(cell_elem.find("enemy_connections").text)

                last_attacked_by = cell_elem.find("last_attacked_by").text
                cell.last_attacked_by = None if last_attacked_by == "None" else last_attacked_by

                cell.will_move = cell_elem.find("will_move").text.lower() == "true"

                # Load new_pos
                new_pos_elem = cell_elem.find("new_pos")
                cell.new_pos = np.array([
                    float(new_pos_elem.find("x").text),
                    float(new_pos_elem.find("y").text)
                ])

                cell.has_any_bridge = cell_elem.find("has_any_bridge").text.lower() == "true"

                # Store cell in our dictionary and add to level
                cells_dict[cell_id] = cell
                self.level.cells.append(cell)

            # Now load bridges
            bridges_elem = level_data.find("bridges")
            bridges_dict = {}  # To store bridges for enemy_bridge references

            for bridge_elem in bridges_elem.findall("bridge"):
                bridge_id = int(bridge_elem.find("id").text)
                parent_id = int(bridge_elem.find("parent_id").text)
                destination_id = int(bridge_elem.find("destination_id").text)

                # Get parent and destination cells
                parent_cell = cells_dict[parent_id]
                destination_cell = cells_dict[destination_id]

                # Create bridge
                bridge = Bridge(parent_cell, destination_cell)

                # Set bridge properties
                bridge.color = bridge_elem.find("color").text
                bridge.length = float(bridge_elem.find("length").text)
                bridge.len = float(bridge_elem.find("len").text)
                bridge.len_px = int(bridge_elem.find("len_px").text)
                bridge.finished = bridge_elem.find("finished").text.lower() == "true"
                bridge.comp_len_px = float(bridge_elem.find("comp_len_px").text)
                bridge.stored_power = float(bridge_elem.find("stored_power").text)
                bridge.is_half_bridge = bridge_elem.find("is_half_bridge").text.lower() == "true"
                bridge.collapse = bridge_elem.find("collapse").text.lower() == "true"
                bridge.thickness = int(bridge_elem.find("thickness").text)
                bridge.gap_length = int(bridge_elem.find("gap_length").text)
                bridge.spawn_cooldown = float(bridge_elem.find("spawn_cooldown").text)
                bridge.can_spawn_this_turn = bridge_elem.find("can_spawn_this_turn").text.lower() == "true"
                bridge.pvp_units = int(bridge_elem.find("pvp_units").text)

                # Store the bridge for enemy_bridge references
                bridges_dict[bridge_id] = bridge

                # Load units on the bridge
                units_elem = bridge_elem.find("units")
                if units_elem is not None:
                    for unit_elem in units_elem.findall("unit"):
                        # Create unit
                        unit = Unit(bridge)

                        # Load position
                        pos_elem = unit_elem.find("position")
                        unit.position = np.array([
                            float(pos_elem.find("x").text),
                            float(pos_elem.find("y").text)
                        ])

                        unit.radius = float(unit_elem.find("radius").text)
                        unit.dead = unit_elem.find("dead").text.lower() == "true"

                        # Load color (RGB tuple)
                        color_str = unit_elem.find("color").text
                        unit.color = tuple(map(int, color_str.split(',')))

                        # Add unit to bridge
                        bridge.units.append(unit)

                # Add bridge to parent cell
                parent_cell.bridges.append(bridge)

            # Second pass to set enemy_bridge references
            for bridge_elem in bridges_elem.findall("bridge"):
                bridge_id = int(bridge_elem.find("id").text)

                enemy_bridge_parent_id = bridge_elem.find("enemy_bridge_parent_id")
                enemy_bridge_index = bridge_elem.find("enemy_bridge_index")

                if enemy_bridge_parent_id is not None and enemy_bridge_index is not None:
                    parent_id = int(enemy_bridge_parent_id.text)
                    index = int(enemy_bridge_index.text)

                    if parent_id in cells_dict and 0 <= index < len(cells_dict[parent_id].bridges):
                        bridges_dict[bridge_id].enemy_bridge = cells_dict[parent_id].bridges[index]

            # Load ghost bridges
            for cell_elem in cells_elem.findall("cell"):
                cell_id = int(cell_elem.find("id").text)
                cell = cells_dict[cell_id]

                ghost_bridges_elem = cell_elem.find("ghost_bridges")
                if ghost_bridges_elem is not None:
                    for ghost_bridge_elem in ghost_bridges_elem.findall("ghost_bridge"):
                        start_cell_id = int(ghost_bridge_elem.find("start_cell_id").text)
                        end_cell_id = int(ghost_bridge_elem.find("end_cell_id").text)

                        if start_cell_id in cells_dict and end_cell_id in cells_dict:
                            cell.ghost_bridges.append((cells_dict[start_cell_id], cells_dict[end_cell_id]))

            # Load UI state
            ui_state = level_data.find("ui_state")
            self.level.activated_cell_connection = ui_state.find("activated_cell_connection").text.lower() == "true"
            self.level.clicked_cell_id = int(ui_state.find("clicked_cell_id").text)
            self.level.lock = ui_state.find("lock").text.lower() == "true"
            self.level.cutting = ui_state.find("cutting").text.lower() == "true"

            # Load cutting start position if it exists
            cutting_pos = ui_state.find("cutting_start_pos")
            if cutting_pos is not None:
                self.level.cutting_start_pos = (
                    float(cutting_pos.find("x").text),
                    float(cutting_pos.find("y").text)
                )

            self.level.is_shop_open = ui_state.find("is_shop_open").text.lower() == "true"

            placing_cell = ui_state.find("placing_cell").text
            self.level.placing_cell = None if placing_cell == "None" else placing_cell

            self.level.context_on = ui_state.find("context_on").text.lower() == "true"

            # Load AI state
            ai_state = level_data.find("ai_state")
            if ai_state is not None:
                self.level.AI.action_timer = float(ai_state.find("action_timer").text)

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