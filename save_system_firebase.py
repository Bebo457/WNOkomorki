import firebase_admin
from firebase_admin import credentials, firestore
import numpy as np
import os
import pygame
import shared
import datetime
import json


class SaveSystemFirebase:
    def __init__(self, level):
        self.level = level
        self.initialized = False
        self.db = None

        # Ścieżka do pliku uwierzytelniającego Firebase
        # W praktyce powinieneś umieścić swój własny plik kluczy serwisowych
        self.credentials_path = 'firebase_credentials.json'

        # Kolekcja, w której będziemy przechowywać zapisy gry
        self.collection_name = 'game_saves'

        # Inicjalizacja Firebase, jeśli plik uwierzytelniający istnieje
        self._initialize_firebase()

    def _initialize_firebase(self):
        """Inicjalizuje połączenie z Firebase, jeśli plik uwierzytelniający istnieje"""
        try:
            if os.path.exists(self.credentials_path):
                # Sprawdzenie, czy Firebase nie jest już zainicjalizowany
                if not firebase_admin._apps:
                    cred = credentials.Certificate(self.credentials_path)
                    firebase_admin.initialize_app(cred)

                self.db = firestore.client()
                self.initialized = True
                print("Firebase został zainicjalizowany")

                # Włączenie trybu offline (persistencja)
                self.db.collection(self.collection_name).document('dummy').set({
                    'dummy': True
                })
            else:
                print(f"Brak pliku uwierzytelniającego Firebase: {self.credentials_path}")
        except Exception as e:
            print(f"Błąd inicjalizacji Firebase: {e}")

    def _convert_to_serializable(self, data):
        """Konwertuje obiekty NumPy array i inne niestandardowe typy na typy serializowalne."""
        if isinstance(data, np.ndarray):
            return data.tolist()
        elif isinstance(data, (np.int_, np.intc, np.intp, np.int8, np.int16, np.int32, np.int64)):
            return int(data)
        elif isinstance(data, (np.float_, np.float16, np.float32, np.float64)):
            return float(data)
        elif isinstance(data, dict):
            return {k: self._convert_to_serializable(v) for k, v in data.items()}
        elif isinstance(data, list) or isinstance(data, tuple):
            return [self._convert_to_serializable(item) for item in data]
        return data

    def get_save_metadata(self):
        """Tworzy metadane dla zapisu gry."""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Pobranie typu rozgrywki i poziomu dla lepszego opisu
        game_type = "Tryb klasyczny" if shared.game_state == 'level_classic' else "Tryb PvP"
        level_info = f"Poziom {self.level.stage}" if hasattr(self.level,
                                                             'stage') and self.level.stage > 0 else "Niestandardowy"

        return {
            "timestamp": timestamp,
            "description": f"{game_type} - {level_info}",
            "save_id": f"{timestamp.replace(' ', '_').replace(':', '-')}"
        }

    def save_game(self):
        """Zapisuje aktualny stan gry do bazy danych Firebase."""
        if not self.initialized:
            print("Firebase nie jest zainicjalizowany. Zapis nie jest możliwy.")
            return False

        try:
            # Metadane zapisu
            metadata = self.get_save_metadata()
            save_id = metadata["save_id"]

            # Zbieranie danych z shared
            shared_data = {
                "game_state": shared.game_state,
                "game_mode": shared.game_mode,
                "ip_address": shared.ip_address if hasattr(shared, "ip_address") else "127.0.0.1",
                "port": shared.port if hasattr(shared, "port") else 8080
            }

            # Zbieranie danych poziomu
            level_data = {
                "active_player": self.level.active_player,
                "stage": self.level.stage,
                "players": []
            }

            # Dane graczy
            for i, player in enumerate(self.level.players):
                player_data = {
                    "id": i,
                    "color": player.color,
                    "coins": float(player.coins),
                    "timer": float(player.timer),
                    "lost": player.lost
                }
                level_data["players"].append(player_data)

            # Dane komórek
            cells_data = []
            for cell in self.level.cells:
                cell_data = {
                    "id": cell.id,
                    "type": cell.type,
                    "power": float(cell.power),
                    "tier": cell.tier,
                    "color": cell.color,
                    "position": self._convert_to_serializable(cell.position),
                    "activated_connection": cell.activated_connection,
                    "enemy_connections": cell.enemy_connections,
                    "last_attacked_by": str(cell.last_attacked_by),
                    "will_move": cell.will_move,
                    "new_pos": self._convert_to_serializable(cell.new_pos),
                    "has_any_bridge": cell.has_any_bridge,
                    "ghost_bridges": []
                }

                # Zapisywanie ghost_bridges (mostów-duchów)
                for ghost_bridge in cell.ghost_bridges:
                    ghost_bridge_data = {
                        "start_cell_id": ghost_bridge[0].id,
                        "end_cell_id": ghost_bridge[1].id
                    }
                    cell_data["ghost_bridges"].append(ghost_bridge_data)

                cells_data.append(cell_data)

            # Dane mostów
            bridges_data = []
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

                    # Referencja do enemy_bridge
                    if bridge.enemy_bridge is not None:
                        for idx, other_bridge in enumerate(bridge.enemy_bridge.parent.bridges):
                            if other_bridge is bridge.enemy_bridge:
                                bridge_data["enemy_bridge_parent_id"] = bridge.enemy_bridge.parent.id
                                bridge_data["enemy_bridge_index"] = idx
                                break

                    # Jednostki na moście
                    for unit in bridge.units:
                        unit_data = {
                            "position": self._convert_to_serializable(unit.position),
                            "radius": float(unit.radius),
                            "dead": unit.dead,
                            "color": unit.color
                        }
                        bridge_data["units"].append(unit_data)

                    bridges_data.append(bridge_data)
                    bridge_count += 1

            # Dane stanu UI
            ui_state = {
                "activated_cell_connection": self.level.activated_cell_connection,
                "clicked_cell_id": self.level.clicked_cell_id,
                "lock": self.level.lock,
                "cutting": self.level.cutting,
                "is_shop_open": self.level.is_shop_open,
                "placing_cell": str(self.level.placing_cell),
                "context_on": self.level.context_on
            }

            # Zapis pozycji początkowej cięcia, jeśli aktywne
            if self.level.cutting:
                ui_state["cutting_start_pos"] = {
                    "x": float(self.level.cutting_start_pos[0]),
                    "y": float(self.level.cutting_start_pos[1])
                }

            # Dane AI
            ai_state = {
                "action_timer": float(self.level.AI.action_timer)
            }

            # Łączenie wszystkich danych
            complete_save_data = {
                "metadata": metadata,
                "shared": shared_data,
                "level_data": level_data,
                "cells": cells_data,
                "bridges": bridges_data,
                "ui_state": ui_state,
                "ai_state": ai_state
            }

            # Zapisanie danych do Firestore
            self.db.collection(self.collection_name).document(save_id).set(
                self._convert_to_serializable(complete_save_data)
            )

            print(f"Gra została zapisana w Firebase z ID: {save_id}")
            return True

        except Exception as e:
            print(f"Błąd podczas zapisywania gry do Firebase: {e}")
            import traceback
            traceback.print_exc()
            return False

    def get_all_saves(self):
        """Pobiera listę wszystkich zapisów gry."""
        if not self.initialized:
            print("Firebase nie jest zainicjalizowany. Odczyt nie jest możliwy.")
            return []

        try:
            saves = self.db.collection(self.collection_name).get()
            return [save.to_dict() for save in saves if 'metadata' in save.to_dict()]
        except Exception as e:
            print(f"Błąd podczas pobierania zapisów gry: {e}")
            return []

    def load_game(self, save_id=None):
        """Wczytuje zapisaną grę z bazy danych Firebase."""
        if not self.initialized:
            print("Firebase nie jest zainicjalizowany. Odczyt nie jest możliwy.")
            return False

        try:
            # Jeśli nie podano ID, spróbuj załadować ostatni zapis
            if save_id is None:
                saves = self.get_all_saves()
                if not saves:
                    print("Brak zapisów gry do wczytania.")
                    return False

                # Sortuj według znacznika czasu (najnowszy pierwszy)
                saves.sort(key=lambda x: x.get('metadata', {}).get('timestamp', ''), reverse=True)
                save_data = saves[0]
            else:
                # Wczytaj określony zapis
                save_doc = self.db.collection(self.collection_name).document(save_id).get()
                if not save_doc.exists:
                    print(f"Zapis o ID {save_id} nie istnieje.")
                    return False
                save_data = save_doc.to_dict()

            # Najpierw zresetuj poziom
            self.level.reinit()

            # Wczytywanie danych z shared
            shared_data = save_data.get("shared", {})
            shared.game_state = shared_data.get("game_state", "main_menu")
            shared.game_mode = shared_data.get("game_mode", "None")
            shared.ip_address = shared_data.get("ip_address", "127.0.0.1")
            shared.port = shared_data.get("port", 8080)

            # Wczytywanie danych poziomu
            level_data = save_data.get("level_data", {})

            # Wczytywanie stage
            self.level.stage = level_data.get("stage", 0)

            # Wczytywanie aktywnego gracza
            self.level.active_player = level_data.get("active_player", 0)

            # Wczytywanie danych graczy
            players_data = level_data.get("players", [])
            for i, player_data in enumerate(players_data):
                if i < len(self.level.players):
                    self.level.players[i].color = player_data.get("color", "BLUE" if i == 0 else "RED")
                    self.level.players[i].coins = float(player_data.get("coins", 100))
                    self.level.players[i].timer = float(player_data.get("timer", shared.timer_time))
                    self.level.players[i].lost = player_data.get("lost", False)

            # Słownik do przechowywania komórek według ID
            cells_dict = {}

            # Wczytywanie komórek
            cells_data = save_data.get("cells", [])
            from cell import Cell

            for cell_data in cells_data:
                # Tworzenie nowej komórki
                position = np.array(cell_data.get("position", [0, 0]))
                cell = Cell(
                    cell_data.get("type", "BASIC"),
                    float(cell_data.get("power", 10)),
                    int(cell_data.get("tier", 1)),
                    cell_data.get("color", "BLUE"),
                    position,
                    int(cell_data.get("id", -1))
                )

                # Ustawianie dodatkowych właściwości
                cell.activated_connection = cell_data.get("activated_connection", False)
                cell.enemy_connections = int(cell_data.get("enemy_connections", 0))

                last_attacked_by = cell_data.get("last_attacked_by", "None")
                cell.last_attacked_by = None if last_attacked_by == "None" else last_attacked_by

                cell.will_move = cell_data.get("will_move", False)
                cell.new_pos = np.array(cell_data.get("new_pos", position))
                cell.has_any_bridge = cell_data.get("has_any_bridge", False)

                # Dodaj komórkę do słownika i poziomu
                cells_dict[cell.id] = cell
                self.level.cells.append(cell)

            # Słownik do przechowywania mostów
            bridges_dict = {}

            # Wczytywanie mostów
            bridges_data = save_data.get("bridges", [])
            from bridge import Bridge
            from unit import Unit

            for bridge_data in bridges_data:
                # Pobierz komórki rodzica i celu
                parent_id = bridge_data.get("parent_id", -1)
                destination_id = bridge_data.get("destination_id", -1)

                if parent_id in cells_dict and destination_id in cells_dict:
                    parent_cell = cells_dict[parent_id]
                    destination_cell = cells_dict[destination_id]

                    # Utwórz most
                    bridge = Bridge(parent_cell, destination_cell)

                    # Ustawianie właściwości mostu
                    bridge.color = bridge_data.get("color", parent_cell.color)
                    bridge.length = float(bridge_data.get("length", 0))
                    bridge.len = float(bridge_data.get("len", 0))
                    bridge.len_px = int(bridge_data.get("len_px", 0))
                    bridge.finished = bridge_data.get("finished", False)
                    bridge.comp_len_px = float(bridge_data.get("comp_len_px", 0))
                    bridge.stored_power = float(bridge_data.get("stored_power", 0))
                    bridge.is_half_bridge = bridge_data.get("is_half_bridge", False)
                    bridge.collapse = bridge_data.get("collapse", False)
                    bridge.thickness = int(bridge_data.get("thickness", 10))
                    bridge.gap_length = int(bridge_data.get("gap_length", 2))
                    bridge.spawn_cooldown = float(bridge_data.get("spawn_cooldown", 0))
                    bridge.can_spawn_this_turn = bridge_data.get("can_spawn_this_turn", False)
                    bridge.pvp_units = int(bridge_data.get("pvp_units", 0))

                    # Przechowywanie mostu do późniejszego ustawienia enemy_bridge
                    bridge_id = bridge_data.get("id", -1)
                    bridges_dict[bridge_id] = {
                        "bridge": bridge,
                        "enemy_bridge_parent_id": bridge_data.get("enemy_bridge_parent_id"),
                        "enemy_bridge_index": bridge_data.get("enemy_bridge_index")
                    }

                    # Wczytywanie jednostek
                    units_data = bridge_data.get("units", [])
                    for unit_data in units_data:
                        unit = Unit(bridge)
                        unit.position = np.array(unit_data.get("position", [0, 0]))
                        unit.radius = float(unit_data.get("radius", 5))
                        unit.dead = unit_data.get("dead", False)

                        # Konwersja koloru - może być przechowywany jako tuple lub lista
                        color_data = unit_data.get("color", (0, 0, 0))
                        if isinstance(color_data, (list, tuple)):
                            unit.color = tuple(color_data)

                        bridge.units.append(unit)

                    # Dodanie mostu do rodzica
                    parent_cell.bridges.append(bridge)

            # Druga iteracja do ustawienia enemy_bridge
            for bridge_info in bridges_dict.values():
                bridge = bridge_info["bridge"]
                parent_id = bridge_info.get("enemy_bridge_parent_id")
                index = bridge_info.get("enemy_bridge_index")

                if parent_id is not None and index is not None:
                    if parent_id in cells_dict and 0 <= index < len(cells_dict[parent_id].bridges):
                        bridge.enemy_bridge = cells_dict[parent_id].bridges[index]

            # Wczytywanie ghost_bridges
            for cell_data in cells_data:
                cell_id = cell_data.get("id", -1)
                if cell_id in cells_dict:
                    cell = cells_dict[cell_id]
                    ghost_bridges_data = cell_data.get("ghost_bridges", [])

                    for ghost_bridge_data in ghost_bridges_data:
                        start_cell_id = ghost_bridge_data.get("start_cell_id", -1)
                        end_cell_id = ghost_bridge_data.get("end_cell_id", -1)

                        if start_cell_id in cells_dict and end_cell_id in cells_dict:
                            cell.ghost_bridges.append((cells_dict[start_cell_id], cells_dict[end_cell_id]))

            # Wczytywanie stanu UI
            ui_state = save_data.get("ui_state", {})
            self.level.activated_cell_connection = ui_state.get("activated_cell_connection", False)
            self.level.clicked_cell_id = int(ui_state.get("clicked_cell_id", -1))
            self.level.lock = ui_state.get("lock", False)
            self.level.cutting = ui_state.get("cutting", False)

            # Wczytywanie pozycji początkowej cięcia
            cutting_start_pos = ui_state.get("cutting_start_pos")
            if cutting_start_pos:
                self.level.cutting_start_pos = (
                    float(cutting_start_pos.get("x", 0)),
                    float(cutting_start_pos.get("y", 0))
                )

            self.level.is_shop_open = ui_state.get("is_shop_open", False)

            placing_cell = ui_state.get("placing_cell", "None")
            self.level.placing_cell = None if placing_cell == "None" else placing_cell

            self.level.context_on = ui_state.get("context_on", False)

            # Wczytywanie stanu AI
            ai_state = save_data.get("ai_state", {})
            self.level.AI.action_timer = float(ai_state.get("action_timer", 0))

            # Konfiguracja interfejsu w zależności od stanu gry
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

            print(f"Gra została wczytana z Firebase")
            return True

        except Exception as e:
            print(f"Błąd podczas wczytywania gry z Firebase: {e}")
            import traceback
            traceback.print_exc()
            return False

    def delete_save(self, save_id):
        """Usuwa zapis gry o podanym ID."""
        if not self.initialized:
            print("Firebase nie jest zainicjalizowany. Usunięcie nie jest możliwe.")
            return False

        try:
            self.db.collection(self.collection_name).document(save_id).delete()
            print(f"Usunięto zapis o ID: {save_id}")
            return True
        except Exception as e:
            print(f"Błąd podczas usuwania zapisu gry: {e}")
            return False

    def show_save_dialog(self):
        """Wyświetla dialog wyboru zapisu do wczytania."""
        # Ta funkcja może być rozbudowana w przyszłości, jeśli potrzebny
        # będzie interfejs graficzny do wyboru zapisów
        saves = self.get_all_saves()
        if not saves:
            print("Brak dostępnych zapisów gry.")
            return None

        print("Dostępne zapisy gry:")
        for i, save in enumerate(saves):
            metadata = save.get('metadata', {})
            print(f"{i + 1}. {metadata.get('description', 'Brak opisu')} - {metadata.get('timestamp', 'Brak daty')}")

        return saves