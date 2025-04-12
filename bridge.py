import numpy as np
import pygame

import shared
from unit import Unit
from shared import fps, bridge_build_speed, mnoznik, attack_speed, spawn_cooldown_s
import cell

class Bridge:
    def __init__(self, parent, destination):
        self.color = parent.color
        self.length = 0
        self.parent = parent
        self.destination = destination
        self.start_pos = parent.position
        self.end_pos = destination.position
        self.segm_len = shared.segm_len
        self.len_px = 0
        self.len = 0
        self.finished = False
        self.comp_len_px = np.linalg.norm(destination.position - parent.position) - parent.radius - destination.radius
        self.id = -1
        self.delete = False
        self.stored_power = 0
        # most się buduje z prędkością i power komórki na sekunde
        self.bridge_speed = bridge_build_speed
        # jeżeli most konkuruje z innym mostem
        self.is_half_bridge = False
        # flaga aktywowana, gdy most się zapada z powodu braku sił komórki albo przecięcia mostu
        self.collapse = False
        # lista jednostek które aktualnie są na moście
        self.units = []
        vector = self.end_pos - self.start_pos
        self.versor = vector / np.linalg.norm(vector)
        # wartości w pixelach
        self.thickness = shared.br_thickness
        self.gap_length = shared.gap_length
        # faktyczny początek i koniec rysowanego mostu
        self.real_start = self.start_pos + self.versor * self.parent.radius
        self.real_end = self.real_start
        # licznik do spawnowania jednostki
        self.spawn_cooldown = 0
        # wskaznik do mostu, komórki z którą jest half_bridge
        self.enemy_bridge = None
        self.can_spawn_this_turn = False
        # określa ile jednostek na turę może wypuścić dany most w pvp
        self.pvp_units = 0

    def building_bridge(self):
        global fps
        # sprawdzanie czy most ma się budować
        if not self.collapse:
            if not self.is_half_bridge:
                if self.len > self.comp_len_px - 1:
                    self.finished = True
            elif self.len > self.comp_len_px/2 - 1 and self.len + self.enemy_bridge.len > self.comp_len_px - 1:
                self.finished = True

        # samo budowanie
        pvp_mnoz = 1
        if shared.game_state == 'pvp_wait':
            pvp_mnoz = shared.pvp_bridge_mul
        if self.collapse:
            self.build_px(-1 * pvp_mnoz)
        elif not self.is_half_bridge:
            if self.len < self.comp_len_px:
                self.build_px(1 * pvp_mnoz)
        else:
            if self.len < self.comp_len_px / 2 - 1:
                self.build_px(1 * pvp_mnoz)
            elif self.len >= self.comp_len_px - self.enemy_bridge.len:
                self.build_px(-1 * pvp_mnoz)
            else:
                self.build_px(1 * pvp_mnoz)

    def draw_bridge(self, window, color = None):
        x1 = self.start_pos[0] + self.versor[0] * self.parent.radius
        y1 = self.start_pos[1] + self.versor[1] * self.parent.radius
        x2 = self.start_pos[0] + self.versor[0] * (self.parent.radius + self.len_px)
        y2 = self.start_pos[1] + self.versor[1] * (self.parent.radius + self.len_px)

        self.real_start = np.array([x1, y1])
        self.real_end = np.array([x2, y2])

        total_length = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
        dx = (x2 - x1) / total_length
        dy = (y2 - y1) / total_length

        current_length = 0
        while current_length < total_length:
            segment_end = min(self.segm_len, total_length - current_length)
            segment_start_x = x1 + dx * current_length
            segment_start_y = y1 + dy * current_length
            segment_end_x = segment_start_x + dx * segment_end
            segment_end_y = segment_start_y + dy * segment_end
            if color is not None:
                pygame.draw.line(window, color, (segment_start_x, segment_start_y), (segment_end_x, segment_end_y),self.thickness)
            else:
                pygame.draw.line(window, self.color, (segment_start_x, segment_start_y), (segment_end_x, segment_end_y),self.thickness)

            current_length += self.segm_len

            if current_length < total_length:
                gap_end = min(self.gap_length, total_length - current_length)
                current_length += gap_end

    def detect_half_bridge(self):
        self.is_half_bridge = False
        self.enemy_bridge = None
        for other_br in self.destination.bridges:
            if other_br.destination == self.parent and not other_br.collapse:
                self.is_half_bridge = True
                other_br.enemy_bridge = self
                self.enemy_bridge = other_br
                return

    def bridge_action(self):
        if self.parent.type == 'BASIC':
            if self.parent.power > 1:
                if self.spawn_cooldown >= spawn_cooldown_s/self.parent.tier:
                    self.spawn_unit()
                    self.spawn_cooldown = 0
                else:
                    self.spawn_cooldown += shared.mnoznik

    def action_pvp(self):
        if self.pvp_units > 0:
            if self.parent.power > 1:
                if self.spawn_cooldown >= shared.pvp_spawn_cooldown/self.parent.tier:
                    self.spawn_unit()
                    self.spawn_cooldown = 0
                    self.pvp_units -= 1
                else:
                    self.spawn_cooldown += shared.mnoznik



    def check_collapse(self):
        if self.parent.power <= 1:
            self.collapse = True
            self.finished = False
            self.can_spawn_this_turn = False

    def spawn_unit(self):
        self.stored_power += 1
        self.parent.power -= 1
        unit = Unit(self)
        self.units.append(unit)

    def filter_dead_units(self):
        for u in self.units:
            if u.dead:
                self.stored_power -= 1
        self.units = [unit for unit in self.units if not unit.dead]

    def build_px(self, x):
        # domyślnie x = -1 lub 1
        self.len += mnoznik * self.segm_len * self.bridge_speed * x
        self.stored_power += mnoznik * self.bridge_speed * x
        if self.parent.color == self.color:
            self.parent.power -= mnoznik * self.bridge_speed * x
        else:
            self.parent.power += mnoznik * self.bridge_speed * x
            self.parent.last_attacked_by = self.color
        self.len_px = int(self.len)

    def create_cut(self, ratio):
    #x to liczba od 0 do 1 mówiąca, ile procent przeciętego mostu wróci do swojej komórki
        new_len = ratio * self.len
        new_len2 = self.len - new_len
        self.len = new_len
        self.collapse = True
        new_bridge = Bridge(self.destination, self.parent)
        new_bridge.color = self.color
        new_bridge.collapse = True
        new_bridge.len = new_len2
        self.destination.bridges.append(new_bridge)

    def update_can_spawn_this_turn(self):
        if self.finished:
            self.can_spawn_this_turn = True