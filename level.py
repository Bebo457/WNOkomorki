from shared import WHITE, line_width
import shared
from bridge import Bridge
import math
import pygame
import numpy as np
import pygame_menu
from cell import Cell
from hand2 import HandGestureSystem
import cv2
from decision import SimpleAI
from save_system_xml import SaveSystemXML
# from save_system_firebase import SaveSystemFirebase
from save_system_json import SaveSystemJSON
from game_playback import GamePlayback
import online


class Player:
    def __init__(self, color):
        self.color = color
        self.coins = 100
        self.timer = shared.timer_time
        # True jeżeli gracz przegrał
        self.lost = False

class Level:
    def __init__(self):
        self.active = False
        self.cells = []
        self.activated_cell_connection = False
        self.clicked_cell_id = -1
        self.connections = []
        self.lock = False
        self.cutting_line = False
    #   mówi o tym czy w danym momencie aktywne jest przecinanie
        self.cutting = False
        self.cutting_start_pos = (0, 0)
    #   ZMIENNE DO TRYBU PVP
        self.active_player = 0
        self.side_menu_width = int(shared.width_px / 5)
        self.side_menu_height = shared.height_px
        # określa rozmiar mapy walki
        self.game_area_width = shared.width_px - self.side_menu_width
        self.game_area_height = shared.height_px
        self.start_zones_height = self.game_area_height
        self.start_zones_width = self.game_area_width/3
        # sklep pygame z kom
        self.shop_menu = pygame_menu.Menu('', shared.pvp_menu_width, 0.7 * shared.pvp_menu_height, theme=pygame_menu.themes.THEME_DARK)
        self.shop_menu.disable()
        self.shop_menu.set_relative_position(100, 0)
        self.shop_menu.add.button("Zwykła", self.place_cell_BASIC)
        self.shop_menu.add.button("Powrót", self.deactivate_shop)
        # true jeżeli otwarte jest menu sklepu
        self.is_shop_open = False
        # działa podczas stawiania komórki w fazie przygotowania, zawiera nazwę stawianej komórki
        self.placing_cell = None
        self.battle_area_surface = pygame.Surface((self.game_area_width, self.game_area_height))
        battle_texture = pygame.transform.scale(shared.purple_texture, (self.game_area_width, self.game_area_height))  # Skalowanie tekstury do rozmiaru powierzchni
        self.battle_area_surface.blit(battle_texture, (0, 0))
        # przechowuje zmienne związane z graczami w pvp
        player1 = Player('BLUE')
        player2 = Player('RED')
        self.players = [player1, player2]

        # menu końca gry
        self.end_menu = pygame_menu.Menu('', shared.end_menu_width, shared.end_menu_height , theme=pygame_menu.themes.THEME_DARK)
        self.end_menu.disable()
        self.end_menu.set_relative_position(50, 70)
        self.end_menu.add.button("Powrót do menu", self.return_to_main_menu)

        # menu boczne główne
        self.pvp_main_menu = pygame_menu.Menu('', shared.pvp_menu_width, 0.7*shared.pvp_menu_height, theme=pygame_menu.themes.THEME_DARK)
        self.pvp_main_menu.disable()
        self.pvp_main_menu.set_relative_position(100, 0)
        self.pvp_main_menu.add.button('Sterowanie gestem', self.start_gesture_system)
        self.pvp_main_menu.add.button("Zapisz (XML)", self.save_game_xml)
        self.pvp_main_menu.add.button("Załaduj grę (XML)", self.load_game_xml)
        self.pvp_main_menu.add.button("Zapisz (Firebase)", self.save_game_firebase)
        self.pvp_main_menu.add.button("Załaduj grę (Firebase)", self.load_game_firebase)
        self.pvp_main_menu.add.button("Zapisz (JSON)", self.save_game_json)
        self.pvp_main_menu.add.button("Załaduj grę (JSON)", self.load_game_json)
        self.pvp_main_menu.add.button("Powrót do menu", self.return_to_main_menu)

        #zmienna poziomu mówiąca czy włączone jest menu kontekstowe
        self.context_on = False

        self.classic_mode_menu = pygame_menu.Menu('', shared.pvp_menu_width, shared.pvp_menu_height, theme=pygame_menu.themes.THEME_DARK)
        self.classic_mode_menu.disable()
        self.classic_mode_menu.set_relative_position(100, 0)
        self.classic_mode_menu.add.button('Zapisz grę (XML)', self.save_game_xml)
        self.classic_mode_menu.add.button('Załaduj zapis (XML)', self.load_game_xml)
        self.classic_mode_menu.add.button('Zapisz grę (Firebase)', self.save_game_firebase)
        self.classic_mode_menu.add.button('Załaduj zapis (Firebase)', self.load_game_firebase)
        self.classic_mode_menu.add.button('Zapisz grę (JSON)', self.save_game_json)
        self.classic_mode_menu.add.button('Załaduj zapis (JSON)', self.load_game_json)
        self.classic_mode_menu.add.button("Powrót do menu", self.return_to_main_menu)
        # żeby nie nazywać tego level.level
        self.stage = 0

        # system gestow reki
        # Tworzenie obiektu do gestów dłoni
        self.gest_sys = HandGestureSystem()
        self.gest_sys.start()
        self.gest_sys_on = False
        self.x_cam = 0
        self.y_cam = 0
        self.fist = False
        # komórka zaznaczona przez kursor kamery
        self.cam_curs_cell = None

        self.game_mode = "None"

        #obiekt klasy AI
        self.AI = SimpleAI(self, 'RED')

        # inicjalizacja save system
        self.save_system_xml = SaveSystemXML(self)
        # self.save_system_firebase = SaveSystemFirebase(self)
        self.save_system_json = SaveSystemJSON(self)
        self.playback = GamePlayback(self)

        # menu odtwarzania
        self.playback_menu = pygame_menu.Menu('ODTWARZANIE NAGRANIA', shared.pvp_menu_width, 0.3 * shared.pvp_menu_height, theme=pygame_menu.themes.THEME_DARK)
        self.playback_menu.disable()
        self.playback_menu.set_relative_position(100, 0)
        self.playback_menu.add.button("Powrót do menu", self.stop_playback)
        # flagi do obsługi odtwarzania
        self.playback_active = False
        self.advance_to_next_frame = False

        # obsługa pvp
        self.online_active = False


    def stop_playback(self):
        """Zatrzymuje odtwarzanie nagrania i wraca do menu głównego"""
        self.playback.stop_playback()
        self.playback_menu.disable()
        self.playback_active = False
        self.advance_to_next_frame = False
        self.return_to_main_menu()

    def toggle_recording(self):
        """Włącza lub wyłącza nagrywanie rozgrywki"""
        is_recording = self.playback.toggle_recording()
        return is_recording

    def is_recording(self):
        """Sprawdza, czy nagrywanie jest aktywne"""
        return self.playback.recording_enabled

    def save_game_json(self):
        """Save the current game state to a JSON file"""
        return self.save_system_json.save_game()

    def load_game_json(self):
        """Load a game state from a JSON file"""
        return self.save_system_json.load_game()

    def save_game_firebase(self):
        pass
        """Save the current game state to Firebase"""
        # return self.save_system_firebase.save_game()

    def load_game_firebase(self):
        pass
        """Load a game state from Firebase"""
        # return self.save_system_firebase.load_game()

    def save_game_xml(self):
        """Save the current game state to an XML file"""
        return self.save_system_xml.save_game()

    def load_game_xml(self):
        """Load a game state from an XML file"""
        return self.save_system_xml.load_game()

    def start_gesture_system(self):
        if not self.gest_sys_on:
            if not self.gest_sys_on:
                self.gest_sys.start()
                self.gest_sys.enable_reading()
                self.gest_sys_on = True  # Flaga wskazująca aktywność systemu
                print("System gestów został uruchomiony.")
                # Otwieranie kamery
                shared.cap = cv2.VideoCapture(0)
                if not shared.cap.isOpened():
                    raise RuntimeError("Nie udało się otworzyć kamery.")
                self.gest_sys.enable_reading()
        else:
            if self.gest_sys.active:
                self.gest_sys.stop()
                self.gest_sys_on = False


    def addCell(self, cell):
        cell.id = len(self.cells)
        self.cells.append(cell)

    # LOOP TRYBU PVP
    def pvp_loop_setup(self):
        click = shared.click
        LMB = shared.LMB
        RMB = shared.RMB
        mouse_pos = shared.mouse_pos
        window = shared.window

        # DZIAŁANIE GRY

        if self.placing_cell is not None:
            if click and self.active_player == 0 and self.players[self.active_player].coins >= 20 and is_point_inside_area(mouse_pos, (shared.cell_radius, shared.cell_radius), (self.game_area_width/3 - shared.cell_radius, self.game_area_height - shared.cell_radius)):
                cell = Cell("BASIC", 10, 1, self.players[self.active_player].color, np.array([mouse_pos[0], mouse_pos[1]]))
                self.addCell(cell)
                self.players[0].coins -= 20
            elif click and self.active_player == 1 and self.players[self.active_player].coins >= 20 and is_point_inside_area(mouse_pos, (shared.cell_radius + 2/3 * self.game_area_width, shared.cell_radius), (self.game_area_width - shared.cell_radius, self.game_area_height - shared.cell_radius)):
                cell = Cell("BASIC", 10, 1, self.players[self.active_player].color, np.array([mouse_pos[0], mouse_pos[1]]))
                self.addCell(cell)
                self.players[1].coins -= 20
            if RMB:
                self.placing_cell = None

        # RYSOWANIE

        # Tworzenie powierzchni dla pola walki

        # Rysowanie paska bocznego (menu)
        battle_texture = pygame.transform.scale(shared.purple_texture, (self.game_area_width, self.game_area_height))
        self.battle_area_surface.blit(battle_texture, (0, 0))

        shared.timer_menu.draw(window)
        shared.timer_menu.update(shared.events)
        if self.is_shop_open:
            self.shop_menu.draw(window)
            self.shop_menu.update(shared.events)
        elif shared.game_state == 'pvp_setup':
            shared.pvp_menu.draw(window)
            shared.pvp_menu.update(shared.events)

        # Rysowanie przeźroczystych stref stawiania komórek na powierzchni bitwy
        # STREFA NIEBIESKA
        transparent_surface = pygame.Surface((self.start_zones_width, self.start_zones_height),pygame.SRCALPHA)
        pygame.draw.rect(transparent_surface, (0, 0, 255, 128),(0, 0, self.start_zones_width, self.start_zones_height))
        self.battle_area_surface.blit(transparent_surface, (0, 0))

        # STREFA CZERWONA
        transparent_surface_red = pygame.Surface((self.start_zones_width, self.start_zones_height), pygame.SRCALPHA)
        pygame.draw.rect(transparent_surface_red, (255, 0, 0, 128),(0, 0, self.start_zones_width, self.start_zones_height))
        self.battle_area_surface.blit(transparent_surface_red, (2 / 3 * self.game_area_width, 0))

        # kiedy stawiana będzie komórka rysowanie jej cienia
        if self.placing_cell is not None:
            pygame.draw.circle(self.battle_area_surface, shared.GRAY_TRANSPARENT, mouse_pos, shared.cell_radius)

        # Rysowanie timerów
        self.draw_timers()

        # Rysowanie napisu "Monety" na dole menu bocznego
        font = pygame.font.Font(None, 40)  # Czcionka (rozmiar 40)
        if self.active_player == 0:
            label = f"Niebieski: {self.players[0].coins}"
            text_surface = font.render(label, True, shared.BLUE)
        else:
            label = f"Czerwony: {self.players[1].coins}"
            text_surface = font.render(label, True, shared.RED)

        text_x = self.game_area_width + (self.side_menu_width // 2 - text_surface.get_width() // 2)  # Wycentrowanie na bocznym menu
        text_y = 0.65 * self.game_area_height  # Pozycja na dole menu bocznego
        shared.window.blit(text_surface, (text_x, text_y))  # Wyświetlenie napisu na ekranie

        # Rysowanie obrazka z teksturą "coin_texture"
        coin_size = shared.coin_size
        coin_texture = pygame.transform.scale(shared.coin_texture, (coin_size, coin_size))  # Skalowanie tekstury monety
        coin_x = self.game_area_width + (self.side_menu_width // 2 - text_surface.get_width() // 2) + text_surface.get_width() + 10  # Obok napisu
        coin_y = 0.65 * self.game_area_height - shared.coin_y_offset # Pozycja równoległa do napisu "Monety"
        shared.window.blit(coin_texture, (coin_x, coin_y))  # Wyświetlenie monety obok napisu

        # rysowanie powierzchni pola walki
        shared.window.blit(self.battle_area_surface, (0, 0))

        for cell in self.cells:
            cell.draw(shared.window, shared.font)

    def pvp_loop(self):
        click = shared.click
        LMB = shared.LMB
        RMB = shared.RMB
        mouse_pos = shared.mouse_pos
        window = shared.window

        # DZIAŁANIE
        # zmienna potrzebna do wykrywania przecinania
        any_cell_hovered = False
        # obsługa kliknięć myszką
        if shared.game_state == 'pvp_turn':
            # aktualizacja zegara
            self.pvp_check_for_win()
            self.players[self.active_player].timer -= shared.mnoznik
            # Przetwarzanie systemu gestów
            if self.gest_sys_on:
                # Pobieranie klatki obrazu z kamery
                ret, frame = shared.cap.read()
                if not ret:
                    print("Nie udało się odczytać klatki.")
                # Przetwarzanie klatki
                self.gest_sys.process_frame(frame)
                # Pobieranie danych gestów
                palm_x, palm_y = self.gest_sys.get_palm_coordinates_percentage(frame.shape[1], frame.shape[0])
                is_fist = self.gest_sys.get_fist_status()

            for cell in self.cells:
                # potrzebne do wykrycia połączeń
                cell.has_any_bridge = False
                cell.check_capture()
                if cell.is_hovered(mouse_pos):
                    any_cell_hovered = True
                if cell.activated_connection:
                    draw_dashed_line(window, cell.color, (cell.position[0], cell.position[1]), mouse_pos, 10, 3)
                if cell.is_clicked_lmb(LMB) and not self.activated_cell_connection and not self.lock and self.players[
                    self.active_player].color == cell.color and not cell.will_move:
                    cell.activated_connection = True
                    self.activated_cell_connection = True
                    self.clicked_cell_id = cell.id
                # zaznaczenie mostu do zbudowania
                if self.activated_cell_connection and cell.is_hovered(
                        mouse_pos) and LMB and not self.clicked_cell_id == cell.id and not cell.will_move:
                    # sprawdzanie czy nie ma już tam mostu
                    check = True
                    for bridge in self.cells[self.clicked_cell_id].bridges:
                        if bridge.parent == self.cells[self.clicked_cell_id] and bridge.destination == cell:
                            check = False
                    if check:
                        ghost_bridge = (self.cells[self.clicked_cell_id], cell)
                        self.cells[self.clicked_cell_id].ghost_bridges.append(ghost_bridge)
                        self.cells[self.clicked_cell_id].activated_connection = False
                        self.clicked_cell_id = -1
                        self.activated_cell_connection = False
                        self.lock = True
                if self.activated_cell_connection and RMB:
                    self.cells[self.clicked_cell_id].activated_connection = False
                    self.clicked_cell_id = -1
                    self.activated_cell_connection = False
                if self.lock:
                    self.lock = False
                    for cell1 in self.cells:
                        if cell1.is_hovered(mouse_pos):
                            self.lock = True
                # wykrywanie PPM na komórkę do otwierania menu kontekstowego
                if RMB and not self.activated_cell_connection and not self.cutting and cell.is_hovered(
                        shared.mouse_pos) and cell.color == self.players[self.active_player].color:
                    self.context_on = True
                    self.pvp_main_menu.disable()
                    for cell2 in self.cells:
                        cell2.context_menu.disable()
                    cell.context_menu.enable()
                elif RMB and self.context_on and not any_cell_hovered:
                    self.context_on = False
                    self.pvp_main_menu.enable()
                    cell.context_menu.disable()
            # pętla do sprawdzania czy ma jakiekolwiek połączenia (do ruszania)
            for cell in self.cells:
                for bridge in cell.bridges:
                    bridge.parent.has_any_bridge = True
                    bridge.destination.has_any_bridge = True
                for ghost in cell.ghost_bridges:
                    ghost[0].has_any_bridge = True
                    ghost[1].has_any_bridge = True

            # GESTY
            if self.gest_sys_on:
                ret, frame = shared.cap.read()
                x, y = self.gest_sys.get_palm_coordinates_percentage(frame.shape[1], frame.shape[0])
                self.fist = self.gest_sys.get_fist_status()
                x = x / 100
                y = y / 100
                x = 1 - x
                x = x * self.game_area_width
                y = y * self.game_area_height
                self.x_cam = x
                self.y_cam = y
            if self.gest_sys_on:
                # szuka najbliższej komórki
                for cell in self.cells:
                    dist = np.linalg.norm(np.array([self.x_cam, self.y_cam]) - cell.position)
                    if dist < cell.radius and cell.color == self.players[self.active_player].color:
                        self.cam_curs_cell = cell
                        self.cam_curs_cell.will_move = True
                if self.fist and self.cam_curs_cell is not None:
                    if np.linalg.norm(np.array([self.x_cam,
                                                self.y_cam]) - self.cam_curs_cell.position) <= shared.move_const * self.cam_curs_cell.radius:
                        self.cam_curs_cell.new_pos = np.array([self.x_cam, self.y_cam])
                    else:
                        kursor = np.array([self.x_cam, self.y_cam])
                        versor = (kursor - self.cam_curs_cell.position) / np.linalg.norm(
                            kursor - self.cam_curs_cell.position)
                        wektor = versor * (shared.move_const * self.cam_curs_cell.radius)
                        self.cam_curs_cell.new_pos = self.cam_curs_cell.position + wektor

            # PRZECINANIE
            if self.cutting and click:
                self.cutting = False
                for cell in self.cells:
                    if cell.color == self.players[self.active_player].color:
                        for bridge in cell.bridges:
                            intersect, int_point = line_intersection(self.cutting_start_pos, mouse_pos,
                                                                     bridge.real_start, bridge.real_end)
                            if intersect:
                                int_pos = np.array([int_point[0], int_point[1]])
                                bridge.can_spawn_this_turn = False
                                if bridge.finished:
                                    if not bridge.is_half_bridge:
                                        # odległość procentowa względem długości całego mostu od rodzica
                                        cutting_len = np.linalg.norm(int_pos - bridge.real_start)
                                        cut_bridge_ratio = cutting_len / bridge.len
                                        bridge.create_cut(cut_bridge_ratio)
                                    else:
                                        bridge.collapse = True
                                else:
                                    bridge.collapse = True
                    cell.ghost_bridges = [
                        ghost_bridge for ghost_bridge in cell.ghost_bridges
                        if not
                        line_intersection(self.cutting_start_pos, mouse_pos,
                                          (ghost_bridge[0].position[0], ghost_bridge[0].position[1]),
                                          (ghost_bridge[1].position[0], ghost_bridge[1].position[1]))[0]]


            elif not any_cell_hovered and not self.activated_cell_connection and click and is_point_inside_area(
                    mouse_pos, (0, 0), (self.game_area_width, self.game_area_height)):
                self.cutting = True
                self.cutting_start_pos = mouse_pos

            if self.cutting and RMB:
                self.cutting = False

            for cell in self.cells:
                # obsługa ruszania
                if cell.will_move and cell.context_menu.is_enabled():
                    if np.linalg.norm(np.array(
                            [mouse_pos[0], mouse_pos[1]]) - cell.position) <= cell.radius * shared.move_const and click:
                        self.cutting = False
                        cell.new_pos = np.array([mouse_pos[0], mouse_pos[1]])

        elif shared.game_state == 'pvp_wait':
            can_skip = True
            for cell in self.cells:
                cell.check_bridges_to_delete()
                cell.update_tier()
                cell.change_position()
                if cell.will_move:
                    can_skip = False
                for bridge in cell.bridges:
                    if bridge.pvp_units > 0:
                        can_skip = False
                    if bridge.can_spawn_this_turn:
                        bridge.action_pvp()
                    bridge.check_collapse()
                    bridge.building_bridge()
                    bridge.detect_half_bridge()
                    bridge.filter_dead_units()
                    if not bridge.finished or len(bridge.units) > 0:
                        can_skip = False
                    for unit in bridge.units:
                        unit.update_position()
            if can_skip:
                self.give_turn()

        # RYSOWANIE

        # Rysowanie paska bocznego (menu)
        battle_texture = pygame.transform.scale(shared.purple_texture, (self.game_area_width, self.game_area_height))
        self.battle_area_surface.blit(battle_texture, (0, 0))

        shared.timer_menu.draw(window)
        shared.timer_menu.update(shared.events)

        if shared.game_state != 'pvp_wait':
            if self.pvp_main_menu.is_enabled():
                self.pvp_main_menu.draw(window)
                self.pvp_main_menu.update(shared.events)
            elif self.context_on:
                for cell in self.cells:
                    if cell.context_menu.is_enabled():
                        cell.update_context_menu()
                        cell.context_menu.draw(shared.window)
                        cell.context_menu.update(shared.events)

        # Rysowanie timerów
        self.draw_timers()
        font = pygame.font.Font(None, 40)  # Czcionka (rozmiar 40)
        if self.active_player == 0:
            label = "Niebieski"
            text_surface = font.render(label, True, shared.BLUE)
        else:
            label = "Czerwony"
            text_surface = font.render(label, True, shared.RED)
        text_x = self.game_area_width + (
                    self.side_menu_width // 2 - text_surface.get_width() // 2)  # Wycentrowanie na bocznym menu
        text_y = 0.65 * self.game_area_height  # Pozycja na dole menu bocznego
        shared.window.blit(text_surface, (text_x, text_y))  # Wyświetlenie napisu na ekranie

        # rysowanie linii cięcia
        if self.cutting:
            pygame.draw.line(self.battle_area_surface, WHITE, self.cutting_start_pos, mouse_pos, line_width)

        # rysowanie powierzchni pola walki
        shared.window.blit(self.battle_area_surface, (0, 0))

        # rysowanie linii do łączenia komórek
        for cell in self.cells:
            if cell.activated_connection:
                draw_dashed_line(window, cell.color, (cell.position[0], cell.position[1]), mouse_pos, 10, 3)

            # obsługa rysowania rzeczy do przesuwania
            if cell.will_move and cell.context_menu.is_enabled():
                pygame.draw.circle(shared.window, shared.GRAY, cell.position, cell.radius * shared.move_const)
            if not (cell.position[0] == cell.new_pos[0] and cell.position[1] == cell.new_pos[1]):
                pygame.draw.line(shared.window, shared.BLACK, cell.position, cell.new_pos, shared.line_width)

        # rysowanie mostów, komórek i jednostek
        for cell in self.cells:
            for bridge in cell.bridges:
                if bridge.collapse and shared.game_state == 'pvp_turn':
                    if self.active_player == 0:
                        bridge.draw_bridge(shared.window, shared.LIGHT_BLUE)
                    else:
                        bridge.draw_bridge(shared.window, shared.LIGHT_RED)
                else:
                    bridge.draw_bridge(shared.window)
            for ghost_bridge in cell.ghost_bridges:
                draw_dashed_line(shared.window, ghost_bridge[0].color, ghost_bridge[0].position,
                                 ghost_bridge[1].position)
            cell.draw(shared.window, shared.font)

        for cell in self.cells:
            for bridge in cell.bridges:
                for unit in bridge.units:
                    unit.draw_unit(shared.window)

        # rysowanie okna zwycięzcy
        if shared.game_state == 'pvp_end':
            for player in self.players:
                if not player.lost:
                    if player.color == 'BLUE':
                        winner = 'Niebieski'
                        winner_color = player.color
                    elif player.color == 'RED':
                        winner = 'Czerwony'
                        winner_color = player.color
            draw_game_over_message(shared.window, winner, winner_color)
            self.end_menu.draw(shared.window)
            self.end_menu.update(shared.events)

        # rysowanie kursora gestów
        if self.gest_sys_on:
            fist = self.gest_sys.get_fist_status()
            if fist:
                pygame.draw.circle(shared.window, shared.DARK_RED, (self.x_cam, self.y_cam), shared.gest_cursor_radius)
            else:
                pygame.draw.circle(shared.window, shared.GREEN, (self.x_cam, self.y_cam), shared.gest_cursor_radius)

    def level_loop(self):
        click = shared.click
        LMB = shared.LMB
        RMB = shared.RMB
        mouse_pos = shared.mouse_pos
        window = shared.window
        # Rysowanie paska bocznego (menu)
        battle_texture = pygame.transform.scale(shared.purple_texture, (self.game_area_width, self.game_area_height))
        self.battle_area_surface.blit(battle_texture, (0, 0))

        window.blit(self.battle_area_surface, (0, 0))

        for cell in self.cells:
            cell.check_bridges_to_delete()
            cell.update_tier()
            for bridge in cell.bridges:
                bridge.check_collapse()
                bridge.building_bridge()
                bridge.detect_half_bridge()
                bridge.filter_dead_units()
                if bridge.finished and not bridge.collapse:
                    bridge.bridge_action()
                    for unit in bridge.units:
                        unit.update_position()
                # usuwanie komórek jeżeli most jest collapsed
                elif bridge.collapse:
                    bridge.units.clear()
        self.check_for_win_single_mode()
        self.AI.update()

        for cell in self.cells:
            for bridge in cell.bridges:
                bridge.draw_bridge(window)

        for cell in self.cells:
            for bridge in cell.bridges:
                for unit in bridge.units:
                    unit.draw_unit(window)

        # zmienna potrzebna do wykrywania przecinania
        any_cell_hovered = False

        # obsługa kliknięć myszką
        for cell in self.cells:
            cell.cell_state_update()
            if cell.is_hovered(mouse_pos):
                any_cell_hovered = True
            if cell.activated_connection:
                draw_dashed_line(window, cell.color, (cell.position[0], cell.position[1]), mouse_pos, 10, 3)
            cell.draw(window, shared.font)
            if cell.is_clicked_lmb(
                    LMB) and not self.activated_cell_connection and not self.lock and cell.color == 'BLUE':
                cell.activated_connection = True
                self.activated_cell_connection = True
                self.clicked_cell_id = cell.id
            if self.activated_cell_connection and cell.is_hovered(
                    mouse_pos) and LMB and not self.clicked_cell_id == cell.id:
                bridge_exists = False
                for bridge in self.cells[self.clicked_cell_id].bridges:
                    if bridge.destination == cell:
                        bridge_exists = True
                        break

                if not bridge_exists:
                    bridge = Bridge(self.cells[self.clicked_cell_id], cell)
                    bridge.id = len(self.cells[self.clicked_cell_id].bridges)
                    self.cells[self.clicked_cell_id].bridges.append(bridge)
                    self.cells[self.clicked_cell_id].activated_connection = False
                    self.clicked_cell_id = -1
                    self.activated_cell_connection = False
                    self.lock = True

            if self.activated_cell_connection and RMB:
                self.cells[self.clicked_cell_id].activated_connection = False
                self.clicked_cell_id = -1
                self.activated_cell_connection = False

            if self.lock:
                self.lock = False
                for cell1 in self.cells:
                    if cell1.is_hovered(mouse_pos):
                        self.lock = True

        # PRZECINANIE
        if self.cutting and click:
            self.cutting = False
            for cell in self.cells:
                for bridge in cell.bridges:
                    intersect, int_point = line_intersection(self.cutting_start_pos, mouse_pos, bridge.real_start,
                                                             bridge.real_end)
                    if intersect:
                        int_pos = np.array([int_point[0], int_point[1]])
                        if bridge.finished:
                            if not bridge.is_half_bridge:
                                # odległość procentowa względem długości całego mostu od rodzica
                                cutting_len = np.linalg.norm(int_pos - bridge.real_start)
                                cut_bridge_ratio = cutting_len / bridge.len
                                bridge.create_cut(cut_bridge_ratio)
                            else:
                                bridge.collapse = True
                        else:
                            bridge.collapse = True

        elif not any_cell_hovered and not self.activated_cell_connection and click:
            self.cutting = True
            self.cutting_start_pos = mouse_pos

        if self.cutting:
            pygame.draw.line(window, shared.WHITE, self.cutting_start_pos, mouse_pos, shared.line_width)

        if self.cutting and RMB:
            self.cutting = False

        if self.classic_mode_menu.is_enabled():
            self.classic_mode_menu.update(shared.events)
            self.classic_mode_menu.draw(window)

        # rysowanie okna zwycięzcy
        if shared.game_state == 'pvp_end':
            for player in self.players:
                if not player.lost:
                    if player.color == 'BLUE':
                        winner = 'Niebieski'
                        winner_color = player.color
                    elif player.color == 'RED':
                        winner = 'Czerwony'
                        winner_color = player.color
            draw_game_over_message(shared.window, winner, winner_color)
            self.end_menu.draw(shared.window)
            self.end_menu.update(shared.events)

    def draw_timers(self):
        mins1 = int(self.players[0].timer / 60)
        mins2 = int(self.players[1].timer / 60)
        sec1 = int(self.players[0].timer - mins1 * 60)
        sec2 = int(self.players[1].timer - mins2 * 60)

        timer1_text = f"{mins1:02}:{sec1:02}"  # Zapis w formacie MM:SS
        timer2_text = f"{mins2:02}:{sec2:02}"  # Zapis w formacie MM:SS

        font = pygame.font.Font(None, 50)

        if self.active_player == 0:
            timer1_surface = font.render(timer1_text, True, shared.BLUE)
            timer2_surface = font.render(timer2_text, True, shared.GRAY)
        else:
            timer1_surface = font.render(timer1_text, True, shared.GRAY)
            timer2_surface = font.render(timer2_text, True, shared.RED)

        shared.window.blit(timer1_surface, (0.85 * shared.width_px, self.game_area_height * 0.7 + shared.offset1))
        shared.window.blit(timer2_surface, (0.85 * shared.width_px, self.game_area_height * 0.7 + shared.offset2))

    def give_turn(self):
        if shared.game_state == 'pvp_setup':
            if self.active_player == 0:
                self.change_active_player()
            else:
                self.change_active_player()
                shared.game_state = 'pvp_turn'
                self.is_shop_open = False
                self.shop_menu.disable()
                shared.pvp_menu.disable()
                shared.timer_menu.enable()
                self.pvp_main_menu.enable()

                # Dodajemy snapshot na początku pierwszej tury
                if self.playback.recording_enabled:
                    self.playback.capture_snapshot()

        elif shared.game_state == 'pvp_turn':
            self.pvp_main_menu.enable()
            for cell in self.cells:
                cell.action_pvp()
                cell.context_menu.disable()
                for bridge in cell.bridges:
                    bridge.spawn_cooldown = shared.pvp_spawn_cooldown
                for g_bridge in cell.ghost_bridges:
                    bridge = Bridge(g_bridge[0], g_bridge[1])
                    bridge.id = len(cell.bridges)
                    g_bridge[0].bridges.append(bridge)
            for cell in self.cells:
                cell.ghost_bridges.clear()
            shared.game_state = 'pvp_wait'
            shared.pvp_menu.disable()
        elif shared.game_state == 'pvp_wait' and not self.playback_active:
            for cell in self.cells:
                for bridge in cell.bridges:
                    bridge.update_can_spawn_this_turn()
            shared.game_state = 'pvp_turn'
            self.change_active_player()
            shared.pvp_menu.enable()

            # Dodajemy snapshot na początku każdej nowej tury
            if self.playback.recording_enabled:
                self.playback.capture_snapshot()
        elif shared.game_state == 'online_setup':
            if self.active_player == 0:
                self.change_active_player()
                self.online_active = False
                online.send_game_state_to_client()
            else:
                self.change_active_player()
                shared.game_state = 'pvp_turn'
                self.is_shop_open = False
                self.shop_menu.disable()
                shared.pvp_menu.disable()
                shared.timer_menu.enable()
                self.pvp_main_menu.enable()

                # Dodajemy snapshot na początku pierwszej tury
                if self.playback.recording_enabled:
                    self.playback.capture_snapshot()


    def change_active_player(self):
        if self.active_player == 0:
            self.active_player = 1
        else:
            self.active_player = 0

    def place_cell_BASIC(self):
        self.placing_cell = 'BASIC'

    def activate_shop(self):
        self.is_shop_open = True
        shared.pvp_menu.disable()
        self.shop_menu.enable()

    def deactivate_shop(self):
        self.is_shop_open = False
        shared.pvp_menu.enable()
        self.shop_menu.disable()

    def set_level_2(self):
        shared.game_state = 'level_classic'
        shared.menu.disable()
        self.classic_mode_menu.enable()
        self.stage = 2

    def set_level_3(self):
        shared.game_state = 'level_classic'
        shared.menu.disable()
        self.classic_mode_menu.enable()
        self.stage = 3

    def set_level_1(self):
        shared.game_state = 'level_classic'
        shared.game_mode = 'single'
        shared.menu.disable()
        self.classic_mode_menu.enable()
        self.stage = 1

        # Set active player to blue (player 0)
        self.active_player = 0

        # Create evenly distributed cells across the map
        # Two blue cells and two red cells

        # Blue cell 1 (top left quadrant)
        blue_cell1 = Cell('BASIC', 10, 1, 'BLUE',
                          np.array([self.game_area_width / 4, self.game_area_height / 4]))
        self.addCell(blue_cell1)

        # Blue cell 2 (bottom right quadrant)
        blue_cell2 = Cell('BASIC', 10, 1, 'BLUE',
                          np.array([self.game_area_width * 3 / 4, self.game_area_height * 3 / 4]))
        self.addCell(blue_cell2)

        # Red cell 1 (top right quadrant)
        red_cell1 = Cell('BASIC', 10, 1, 'RED',
                         np.array([self.game_area_width * 3 / 4, self.game_area_height / 4]))
        self.addCell(red_cell1)

        # Red cell 2 (bottom left quadrant)
        red_cell2 = Cell('BASIC', 10, 1, 'RED',
                         np.array([self.game_area_width / 4, self.game_area_height * 3 / 4]))
        self.addCell(red_cell2)

    def pvp_check_for_win(self):
        # sprawdzanie timera
        for player in self.players:
            if player.timer <= 0:
                player.lost = True
                shared.game_state = 'pvp_end'
        # sprawdzanie czy każdy gracz ma żywą komórkę
        player1_cells = 0
        player2_cells = 0
        player1_color = self.players[0].color
        player2_color = self.players[1].color
        for cell in self.cells:
            if cell.color == player1_color:
                player1_cells += 1
            elif cell.color == player2_color:
                player2_cells += 1
        if player1_cells == 0:
            self.players[0].lost = True
            shared.game_state = 'pvp_end'
        elif player2_cells == 0:
            self.players[1].lost = True
            shared.game_state = 'pvp_end'
        if shared.game_state == 'pvp_end':
            self.end_menu.enable()

    def check_for_win_single_mode(self):
        # sprawdzanie czy każdy gracz ma żywą komórkę
        player1_cells = 0
        player2_cells = 0
        player1_color = self.players[0].color
        player2_color = self.players[1].color
        for cell in self.cells:
            if cell.color == player1_color:
                player1_cells += 1
            elif cell.color == player2_color:
                player2_cells += 1
        if player1_cells == 0:
            self.players[0].lost = True
            shared.game_state = 'pvp_end'
        elif player2_cells == 0:
            self.players[1].lost = True
            shared.game_state = 'pvp_end'
        if shared.game_state == 'pvp_end':
            self.classic_mode_menu.disable()
            self.end_menu.enable()

    def return_to_main_menu(self):
        # Sprawdź, czy nagrywanie jest aktywne i zatrzymaj je
        if hasattr(self, 'playback') and self.playback.recording_enabled:
            print("Kończenie nagrywania przed powrotem do menu głównego...")
            self.playback.stop_recording()

        # Dotychczasowy kod metody
        shared.game_state = 'main_menu'
        shared.menu.enable()
        self.end_menu.disable()
        self.reinit()

    def playback_loop(self):
        """Pętla obsługująca tryb odtwarzania nagrania"""

        window = shared.window

        self.playback.next_frame_cooldown += 1 * shared.mnoznik

        # Jeśli wszystkie animacje zostały zakończone, przechodzimy do następnej klatki
        if self.playback.next_frame_cooldown >= shared.frame_speed and not self.advance_to_next_frame:
            self.playback.next_frame_cooldown = 0
            self.advance_to_next_frame = True
            print("Animacje zakończone, gotowy do przejścia do następnej klatki")

        if self.advance_to_next_frame:
            if self.playback.current_snapshot_index < len(self.playback.snapshots) - 1:
                self.playback.current_snapshot_index += 1
                self.playback.apply_current_snapshot()  # Ta metoda już została zmodyfikowana, aby zachować game_state
                print(f"Odtwarzanie tury {self.playback.current_snapshot_index + 1} z {len(self.playback.snapshots)}")
                # Reset flagi
                self.advance_to_next_frame = False
            else:
                print("Osiągnięto koniec nagrania.")
                self.playback.stop_playback()
                return

        battle_texture = pygame.transform.scale(shared.purple_texture, (self.game_area_width, self.game_area_height))
        self.battle_area_surface.blit(battle_texture, (0, 0))

        window.blit(self.battle_area_surface, (0, 0))

        for cell in self.cells:
            for bridge in cell.bridges:
                bridge.draw_bridge(window)
            for ghost_bridge in cell.ghost_bridges:
                draw_dashed_line(window, ghost_bridge[0].color, ghost_bridge[0].position,
                                 ghost_bridge[1].position)
            cell.draw(window, shared.font)

        for cell in self.cells:
            for bridge in cell.bridges:
                for unit in bridge.units:
                    unit.draw_unit(window)

        font = pygame.font.Font(None, 30)
        current_turn = self.playback.current_snapshot_index + 1
        total_turns = len(self.playback.snapshots)

        turn_text = f"Tura: {current_turn}/{total_turns}"
        turn_surface = font.render(turn_text, True, shared.WHITE)
        window.blit(turn_surface, (20, 20))

        player_color = "Niebieski" if self.active_player == 0 else "Czerwony"
        player_text = f"Gracz: {player_color}"
        player_surface = font.render(player_text, True, shared.BLUE if self.active_player == 0 else shared.RED)
        window.blit(player_surface, (20, 50))

        self.playback_menu.draw(window)
        self.playback_menu.update(shared.events)

    def stop_playback(self):
        """Zatrzymuje odtwarzanie nagrania i wraca do menu głównego"""
        self.playback.stop_playback()
        self.playback_menu.disable()
        self.return_to_main_menu()

    # zresetowanie stanu poziomu
    def reinit(self):
        self.active = False
        self.cells = []
        self.activated_cell_connection = False
        self.clicked_cell_id = -1
        self.connections = []
        self.lock = False
        self.cutting_line = False
        #   mówi o tym czy w danym momencie aktywne jest przecinanie
        self.cutting = False
        self.cutting_start_pos = (0, 0)
        #   ZMIENNE DO TRYBU PVP
        self.active_player = 0
        self.side_menu_width = int(shared.width_px / 5)
        self.side_menu_height = shared.height_px
        # określa rozmiar mapy walki
        self.game_area_width = shared.width_px - self.side_menu_width
        self.game_area_height = shared.height_px
        self.start_zones_height = self.game_area_height
        self.start_zones_width = self.game_area_width / 3
        # sklep pygame z kom
        self.shop_menu = pygame_menu.Menu('', shared.pvp_menu_width, 0.7 * shared.pvp_menu_height,
                                          theme=pygame_menu.themes.THEME_DARK)
        self.shop_menu.disable()
        self.shop_menu.set_relative_position(100, 0)
        self.shop_menu.add.button("Zwykła", self.place_cell_BASIC)
        self.shop_menu.add.button("Powrót", self.deactivate_shop)
        # true jeżeli otwarte jest menu sklepu
        self.is_shop_open = False
        # działa podczas stawiania komórki w fazie przygotowania, zawiera nazwę stawianej komórki
        self.placing_cell = None
        self.battle_area_surface = pygame.Surface((self.game_area_width, self.game_area_height))
        battle_texture = pygame.transform.scale(shared.purple_texture, (
        self.game_area_width, self.game_area_height))  # Skalowanie tekstury do rozmiaru powierzchni
        self.battle_area_surface.blit(battle_texture, (0, 0))
        # przechowuje zmienne związane z graczami w pvp
        player1 = Player('BLUE')
        player2 = Player('RED')
        self.players = [player1, player2]

        # menu końca gry
        self.end_menu = pygame_menu.Menu('', 400, 150, theme=pygame_menu.themes.THEME_DARK)
        self.end_menu.disable()
        self.end_menu.set_relative_position(50, 70)
        self.end_menu.add.button("Powrót do menu", self.return_to_main_menu)

        # menu boczne główne
        self.pvp_main_menu = pygame_menu.Menu('', shared.pvp_menu_width, 0.7 * shared.pvp_menu_height,
                                              theme=pygame_menu.themes.THEME_DARK)
        self.pvp_main_menu.disable()
        self.pvp_main_menu.set_relative_position(100, 0)
        self.pvp_main_menu.add.button('Sterowanie gestem', self.start_gesture_system)
        self.pvp_main_menu.add.button("Zapisz (XML)", self.save_game_xml)
        self.pvp_main_menu.add.button("Załaduj grę (XML)", self.load_game_xml)
        self.pvp_main_menu.add.button("Zapisz (Firebase)", self.save_game_firebase)
        self.pvp_main_menu.add.button("Załaduj grę (Firebase)", self.load_game_firebase)
        self.pvp_main_menu.add.button("Zapisz (JSON)", self.save_game_json)
        self.pvp_main_menu.add.button("Załaduj grę (JSON)", self.load_game_json)
        self.pvp_main_menu.add.button("Powrót do menu", self.return_to_main_menu)

        # zmienna poziomu mówiąca czy włączone jest menu kontekstowe
        self.context_on = False

        self.classic_mode_menu = pygame_menu.Menu('', shared.pvp_menu_width, shared.pvp_menu_height,
                                                  theme=pygame_menu.themes.THEME_DARK)
        self.classic_mode_menu.disable()
        self.classic_mode_menu.set_relative_position(100, 0)
        self.classic_mode_menu.add.button('Zapisz grę (XML)', self.save_game_xml)
        self.classic_mode_menu.add.button('Załaduj zapis (XML)', self.load_game_xml)
        self.classic_mode_menu.add.button('Zapisz grę (Firebase)', self.save_game_firebase)
        self.classic_mode_menu.add.button('Załaduj zapis (Firebase)', self.load_game_firebase)
        self.classic_mode_menu.add.button('Zapisz grę (JSON)', self.save_game_json)
        self.classic_mode_menu.add.button('Załaduj zapis (JSON)', self.load_game_json)
        self.classic_mode_menu.add.button("Powrót do menu", self.return_to_main_menu)
        # żeby nie nazywać tego level.level
        self.stage = 0

        # system gestow reki
        # Tworzenie obiektu do gestów dłoni
        # self.gest_sys = HandGestureSystem()
        # self.gest_sys.start()
        self.gest_sys_on = False
        self.x_cam = 0
        self.y_cam = 0
        self.fist = False
        # komórka zaznaczona przez kursor kamery
        self.cam_curs_cell = None

        self.game_mode = "None"

        # obiekt klasy AI
        self.AI = SimpleAI(self, 'RED')

    def online_loop_setup(self):
        """
        Funkcja analogiczna do pvp_loop_setup dla trybu online
        Obsługuje fazę stawiania komórek w trybie online
        """
        click = shared.click
        LMB = shared.LMB
        RMB = shared.RMB
        mouse_pos = shared.mouse_pos
        window = shared.window
        if self.online_active:
            # DZIAŁANIE GRY - analogiczne do pvp_loop_setup
            if self.placing_cell is not None:
                # Dla gracza niebieskiego
                if click and self.active_player == 0 and self.players[self.active_player].coins >= 20:
                    # Sprawdzanie czy punkt jest w dozwolonej strefie
                    if is_point_inside_area(mouse_pos, (shared.cell_radius, shared.cell_radius),
                                            (self.game_area_width / 3 - shared.cell_radius,
                                             self.game_area_height - shared.cell_radius)):
                        cell = Cell("BASIC", 10, 1, self.players[self.active_player].color,
                                    np.array([mouse_pos[0], mouse_pos[1]]))
                        self.addCell(cell)
                        self.players[0].coins -= 20
                # Dla gracza czerwonego
                elif click and self.active_player == 1 and self.players[self.active_player].coins >= 20:
                    # Sprawdzanie czy punkt jest w dozwolonej strefie
                    if is_point_inside_area(mouse_pos,
                                            (shared.cell_radius + 2 / 3 * self.game_area_width, shared.cell_radius),
                                            (self.game_area_width - shared.cell_radius,
                                             self.game_area_height - shared.cell_radius)):
                        cell = Cell("BASIC", 10, 1, self.players[self.active_player].color,
                                    np.array([mouse_pos[0], mouse_pos[1]]))
                        self.addCell(cell)
                        self.players[1].coins -= 20
                # Anulowanie wyboru komórki
                if RMB:
                    self.placing_cell = None

        # RYSOWANIE - analogiczne do pvp_loop_setup
        # Tworzenie powierzchni dla pola walki
        battle_texture = pygame.transform.scale(shared.purple_texture, (self.game_area_width, self.game_area_height))
        self.battle_area_surface.blit(battle_texture, (0, 0))

        # Rysowanie menu timera
        if shared.timer_menu.is_enabled():
            shared.timer_menu.draw(window)
            shared.timer_menu.update(shared.events)

        # Rysowanie odpowiedniego menu
        if self.is_shop_open:
            self.shop_menu.draw(window)
            self.shop_menu.update(shared.events)
        elif shared.game_state == 'online_setup' and shared.pvp_menu.is_enabled():
            shared.pvp_menu.draw(window)
            shared.pvp_menu.update(shared.events)

        # Rysowanie stref stawiania komórek
        # STREFA NIEBIESKA
        transparent_surface = pygame.Surface((self.start_zones_width, self.start_zones_height), pygame.SRCALPHA)
        pygame.draw.rect(transparent_surface, (0, 0, 255, 128), (0, 0, self.start_zones_width, self.start_zones_height))
        self.battle_area_surface.blit(transparent_surface, (0, 0))

        # STREFA CZERWONA
        transparent_surface_red = pygame.Surface((self.start_zones_width, self.start_zones_height), pygame.SRCALPHA)
        pygame.draw.rect(transparent_surface_red, (255, 0, 0, 128),
                         (0, 0, self.start_zones_width, self.start_zones_height))
        self.battle_area_surface.blit(transparent_surface_red, (2 / 3 * self.game_area_width, 0))

        # Rysowanie cienia komórki przy stawianiu
        if self.placing_cell is not None:
            pygame.draw.circle(self.battle_area_surface, shared.GRAY_TRANSPARENT, mouse_pos, shared.cell_radius)

        # Rysowanie timerów
        self.draw_timers()

        # Rysowanie informacji o graczu i monetach
        font = pygame.font.Font(None, 40)
        if self.active_player == 0:
            label = f"Niebieski: {self.players[0].coins}"
            text_surface = font.render(label, True, shared.BLUE)
        else:
            label = f"Czerwony: {self.players[1].coins}"
            text_surface = font.render(label, True, shared.RED)

        text_x = self.game_area_width + (self.side_menu_width // 2 - text_surface.get_width() // 2)
        text_y = 0.65 * self.game_area_height
        shared.window.blit(text_surface, (text_x, text_y))

        # Rysowanie ikony monety
        coin_size = shared.coin_size
        coin_texture = pygame.transform.scale(shared.coin_texture, (coin_size, coin_size))
        coin_x = self.game_area_width + (
                    self.side_menu_width // 2 - text_surface.get_width() // 2) + text_surface.get_width() + 10
        coin_y = 0.65 * self.game_area_height - shared.coin_y_offset
        shared.window.blit(coin_texture, (coin_x, coin_y))

        # Rysowanie pola walki
        shared.window.blit(self.battle_area_surface, (0, 0))

        # Rysowanie komórek
        for cell in self.cells:
            cell.draw(shared.window, shared.font)

    def pvp_side_menu_setup(self):
        global menu
        shared.menu.disable()
        shared.pvp_menu = pygame_menu.Menu('WYBÓR KOMÓREK STARTOWYCH', shared.pvp_menu_width,
                                           0.7 * shared.pvp_menu_height,
                                           theme=pygame_menu.themes.THEME_DARK)
        shared.pvp_menu.widget_alignment = 'align_top'
        shared.pvp_menu.set_relative_position(100, 0)
        shared.pvp_menu.add.button('Sklep', self.activate_shop)
        shared.pvp_menu.add.button('Powrót', self.return_to_main_menu)
        if shared.game_state == 'online_setup' and shared.is_host:
            shared.timer_menu.enable()
            shared.pvp_menu.enable()
        elif shared.game_state == 'online_setup' and not shared.is_host:
            shared.timer_menu.disable()
            shared.pvp_menu.disable()

def draw_dashed_line(screen, color, start_pos, end_pos, dash_length=12, width=line_width):
    x1, y1 = start_pos
    x2, y2 = end_pos
    dx = x2 - x1
    dy = y2 - y1
    distance = math.sqrt(dx ** 2 + dy ** 2)
    dashes = int(distance // dash_length)

    for i in range(dashes):
        if i % 2 == 0:
            start_x = x1 + (dx / distance) * dash_length * i
            start_y = y1 + (dy / distance) * dash_length * i
            end_x = x1 + (dx / distance) * dash_length * (i + 1)
            end_y = y1 + (dy / distance) * dash_length * (i + 1)
            pygame.draw.line(screen, color, (start_x, start_y), (end_x, end_y), width)

def line_intersection(A1, A2, B1, B2):
    """
    Sprawdza, czy dwie linie przecinają się, i zwraca punkt przecięcia, jeśli istnieje.

    :param A1: Początek linii A (x, y)
    :param A2: Koniec linii A (x, y)
    :param B1: Początek linii B (x, y)
    :param B2: Koniec linii B (x, y)
    :return: Tuple (True, (px, py)) jeśli linie się przecinają, inaczej (False, None)
    """
    def det(a, b, c, d):
        """Wyznacznik macierzy 2x2."""
        return a * d - b * c

    x1, y1 = A1
    x2, y2 = A2
    x3, y3 = B1
    x4, y4 = B2

    # Obliczenia wyznaczników
    denominator = det(x1 - x2, y1 - y2, x3 - x4, y3 - y4)
    if denominator == 0:  # Linie są równoległe
        return False, None

    # Obliczenie punktu przecięcia
    px = det(det(x1, y1, x2, y2), x1 - x2, det(x3, y3, x4, y4), x3 - x4) / denominator
    py = det(det(x1, y1, x2, y2), y1 - y2, det(x3, y3, x4, y4), y3 - y4) / denominator

    # Sprawdzenie, czy punkt przecięcia leży w zakresie obu odcinków
    if (min(x1, x2) <= px <= max(x1, x2) and min(y1, y2) <= py <= max(y1, y2) and
        min(x3, x4) <= px <= max(x3, x4) and min(y3, y4) <= py <= max(y3, y4)):
        return True, (px, py)

    return False, None

def is_point_inside_area(point, corner1, corner2):
    """
    Sprawdza, czy punkt znajduje się wewnątrz obszaru wyznaczonego przez dwa rogi prostokąta.

    Args:
        point (tuple): Współrzędne punktu (x, y) sprawdzanego.
        corner1 (tuple): Współrzędne pierwszego rogu prostokąta (x, y).
        corner2 (tuple): Współrzędne drugiego rogu prostokąta (x, y).

    Returns:
        bool: True, jeśli punkt znajduje się wewnątrz obszaru, False w przeciwnym razie.
    """
    x, y = point
    x1, y1 = corner1
    x2, y2 = corner2

    # Wyznacz minimalne i maksymalne współrzędne prostokąta
    min_x = min(x1, x2)
    max_x = max(x1, x2)
    min_y = min(y1, y2)
    max_y = max(y1, y2)

    # Sprawdzenie, czy punkt mieści się w zakresie
    return min_x <= x <= max_x and min_y <= y <= max_y

def draw_game_over_message(screen, winner_name, color):
    """
    Funkcja rysuje komunikat na środku ekranu: "Koniec gry, wygrał gracz [winner_name]"
    """
    font = pygame.font.Font(None, 60)  # Ustawienie czcionki (domyślna, rozmiar 60)
    message = f"Koniec gry, wygrał gracz {winner_name}"  # Treść komunikatu

    # Renderowanie tekstu
    text_surface = font.render(message, True, color)  # Biały kolor tekstu
    text_rect = text_surface.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2))  # Środek ekranu

    # Rysowanie tła za tekstem (opcjonalnie, np. czarny prostokąt)
    pygame.draw.rect(screen, (0, 0, 0), text_rect.inflate(20, 20))  # Tło powiększone o 20 pikseli z każdej strony
    screen.blit(text_surface, text_rect)  # Rysowanie tekstu na ekranie




