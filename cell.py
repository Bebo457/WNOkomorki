import numpy as np
import pygame
import pygame_menu

from shared import regen_speed, mnoznik, window_size
import shared

class Cell:
    def __init__(self, type="BASIC", power=10, tier=1, color="BLUE", position=np.array([0.0, 0.0]), id=-1):
        self.id = id
        self.position = position  # Pozycja komórki (środek kółka)
        self.type = type
        self.power = power
        self.tier = tier
        self.color = color
        self.activated_connection = False
        self.bridges = []
        self.enemy_connections = 0
        self.last_attacked_by = None
        # przerywane kreski w pvp pokazujące że zaraz będzie tam most
        self.ghost_bridges = []

        # własne menu kontekstowe dla każdej komórki
        self.context_menu = pygame_menu.Menu('', shared.pvp_menu_width, 0.7 * shared.pvp_menu_height, theme=pygame_menu.themes.THEME_DARK)
        self.context_menu.disable()
        self.context_menu.set_relative_position(100, 0)
        self.power_label = self.context_menu.add.label(f"Aktualna moc: {self.power}")
        self.tier_label = self.context_menu.add.label(f"Tier: {self.tier}")
        self.context_menu.add.button("Ruch", self.begin_move)
        # label do informowania o błędach
        self.info_label = self.context_menu.add.label(' ')

        # zmienne potrzebne do przesuwania
        # aktywuje rysowanie drugiego kółka
        self.will_move = False
        self.new_pos = self.position    # koordynaty nowego położenia
        self.has_any_bridge = False

        # Ładowanie tekstury
        texture_path = 'textures/bubble.png'
        try:
            self.texture = pygame.image.load(texture_path)
        except pygame.error as e:
            print(f"Nie udało się załadować tekstury: {e}")
            pygame.quit()
            sys.exit()

        # Parametry kółka
        self.radius = shared.cell_radius + shared.cell_radius_tier * (self.tier - 1)
        self.previous_LMB_state = False

    def draw(self, window, font):
        # Wybór koloru kółka
        color_1 = shared.RED if self.color == 'RED' else shared.BLUE if self.color == 'BLUE' else shared.BLACK

        # Rysowanie kółka
        pygame.draw.circle(window, color_1, (int(self.position[0]), int(self.position[1])), self.radius)

        # Skalowanie tekstury
        bubble_size = 1.3
        texture_scaled = pygame.transform.scale(self.texture, (bubble_size*self.radius * 2, bubble_size*self.radius * 2))
        texture_rect = texture_scaled.get_rect(center=(int(self.position[0]), int(self.position[1])))
        window.blit(texture_scaled, texture_rect)

        # Tworzenie tekstu wewnątrz kółka
        text1 = font.render(str(int(self.power)), True, shared.BLACK)
        text2 = font.render(str(self.tier), True, shared.BLACK)
        text1_rect = text1.get_rect(center=(self.position[0], self.position[1] - 10))
        text2_rect = text2.get_rect(center=(self.position[0], self.position[1] + 20))
        window.blit(text1, text1_rect)
        window.blit(text2, text2_rect)

        if self.is_hovered(shared.mouse_pos):
            circle_surface = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(circle_surface, (255, 255, 255, 100), (self.radius, self.radius), self.radius)
            window.blit(circle_surface, (int(self.position[0] - self.radius), int(self.position[1] - self.radius)))

    def is_hovered(self, mouse_pos):
        distance = np.linalg.norm(self.position - np.array(mouse_pos))
        return distance <= self.radius

    def is_clicked_lmb(self, LMB):
        if LMB and self.is_hovered(pygame.mouse.get_pos()):
            self.previous_LMB_state = True
        elif not LMB and self.previous_LMB_state:
            self.previous_LMB_state = False
            if self.is_hovered(pygame.mouse.get_pos()):
                return True
        return False

    def check_bridges_to_delete(self):
        # kasowanie mostow upadłych z zerową długością
        for bridge in self.bridges:
            if bridge.collapse and bridge.len <= 0:
                bridge.delete = True
        self.bridges = [bridge for bridge in self.bridges if not bridge.delete]

    def cell_state_update(self):
        self.power += self.tier * mnoznik * regen_speed
        self.check_capture()

    def check_capture(self):
        if self.power < 0 and self.last_attacked_by is not None:
            if self.last_attacked_by == 'BLUE':
                self.color = 'BLUE'
            elif self.last_attacked_by == 'RED':
                self.color = 'RED'
            self.power = 10
            self.tier = 1

        # po oddaniu tury, aby komórki mogły atakować
    def action_pvp(self):
        if self.type == 'BASIC':
            # per bridge
            for bridge in self.bridges:
                if bridge.can_spawn_this_turn:
                    bridge.pvp_units = 1 + self.tier
            self.power += 2 * self.tier

    def update_tier(self):
        # system tierów zrobiony na histerezie
        # awans
        if self.power >= (self.tier + 1) * shared.tier_constant + shared.tier_constant/2 and self.tier < 5:
            self.tier += 1
        # degradacja
        elif self.tier != 1 and self.power <= self.tier * shared.tier_constant - shared.tier_constant/2:
            self.tier -= 1
        # aktualizacja wielkości komórki w zależności od tieru
        self.radius = shared.cell_radius + shared.cell_radius_tier * (self.tier - 1)


    def update_context_menu(self):
        self.power_label.set_title(f"Aktualna moc: {int(self.power)}")
        self.tier_label.set_title(f"Tier: {self.tier}")

    def begin_move(self):
        if not self.will_move:
            if not self.has_any_bridge:
                self.will_move = True
            else:
                self.info_label.set_title("Komórka ma połączneia!")
        else:
            self.will_move = False
            self.new_pos = self.position

    def change_position(self):
        if np.linalg.norm(self.new_pos - self.position) > 5 and self.power > 1:
            versor = (self.new_pos - self.position) / np.linalg.norm(self.new_pos - self.position)
            self.position = self.position + versor * (shared.cell_move_speed * shared.mnoznik)
            self.power -= shared.cell_move_speed/shared.cell_move_cost * mnoznik
        else:
            self.new_pos = self.position
            self.will_move = False



