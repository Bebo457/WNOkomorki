import pygame
import numpy as np

import shared
from shared import mnoznik, cell_speed, DARK_BLUE, DARK_RED

class Unit:
    def __init__(self, bridge):
        # typ klasy bridge
        self.bridge = bridge
        # pozycja początkowa jednostki znajduje się na granicy koła
        self.position = self.bridge.real_start
        self.radius = self.bridge.thickness / 2
        self.dead = False
        if self.bridge.color == 'BLUE':
            self.color = DARK_BLUE
        elif self.bridge.color == 'RED':
            self.color = DARK_RED
        self.closest_enemy_unit = None

    def draw_unit(self, window):
        pygame.draw.circle(window, self.color, self.position, self.radius)

    def update_position(self):
        # sprawdzanie czy dotarł do komórki
        distance_form_dest = np.linalg.norm(self.position - self.bridge.destination.position)
        # jeżeli unit natknie się na unit przeciwnika nawzajem się zabiją
        if self.bridge.enemy_bridge is not None:
            dist_from_en_cells = 100000
            found_cell = False
            for enemy in self.bridge.enemy_bridge.units:
                buffer = np.linalg.norm(enemy.position - self.position)
                if buffer < dist_from_en_cells:
                    dist_from_en_cells = buffer
                    self.closest_enemy_unit = enemy
                    found_cell = True
            if found_cell and dist_from_en_cells < self.radius + self.closest_enemy_unit.radius:
                self.closest_enemy_unit.dead = True
                self.dead = True
        if distance_form_dest < self.radius + self.bridge.destination.radius:
            self.dead = True
            if self.bridge.destination.color != self.bridge.parent.color:
                self.bridge.destination.power -= 1
                self.bridge.destination.last_attacked_by = self.bridge.color
            else:
                self.bridge.destination.power += 1
        # aktualizacja położenia
        if not self.dead:
            pvp_mnoz = 1
            if shared.game_state == 'pvp_wait':
                pvp_mnoz = shared.pvp_unit_mul
            self.position += self.bridge.versor * mnoznik * cell_speed * pvp_mnoz

#   funkcja do przejmowania