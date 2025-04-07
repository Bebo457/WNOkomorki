import random
import numpy as np

import shared
from bridge import Bridge


class SimpleAI:
    def __init__(self, level, color='RED'):
        # Referencja do poziomu
        self.level = level
        # Kolor komórek AI (domyślnie czerwony)
        self.color = color
        # Czasomierz do podejmowania akcji
        self.action_timer = 0
        # Prawdopodobieństwo wykonania ruchu (40%)
        self.action_probability = 0.4
        # Interwał sprawdzania (w sekundach)
        self.check_interval = 2.0

    def update(self):
        """Aktualizuje stan AI i podejmuje decyzje"""
        # Aktualizacja timera
        self.action_timer += shared.mnoznik

        # Sprawdzenie, czy czas na akcję
        if self.action_timer >= self.check_interval:
            self.action_timer = 0

            # Losowanie czy wykonać ruch
            if random.random() < self.action_probability:
                # 80% szans na budowanie mostu, 20% szans na przecięcie własnego mostu
                if random.random() < 0.8:
                    self.make_move()
                else:
                    self.cut_own_bridge()

    def make_move(self):
        """Podejmuje losową akcję dla komórek AI"""
        # Zbieranie komórek należących do AI
        ai_cells = [cell for cell in self.level.cells if cell.color == self.color]

        # Jeśli nie ma komórek AI, nic nie rób
        if not ai_cells:
            return

        # Sortowanie komórek według ilości mostów (od najmniejszej)
        ai_cells.sort(key=lambda cell: len(cell.bridges))

        # Wybierz komórkę z najmniejszą liczbą mostów
        # Możemy dodać losowość wybierając z np. 3 pierwszych komórek
        if len(ai_cells) > 3:
            source_cell = random.choice(ai_cells[:3])
        else:
            source_cell = random.choice(ai_cells)

        # Próba znalezienia celu dla mostu
        target_cell = self.find_target_for_bridge(source_cell)

        # Jeśli znaleziono cel, zbuduj most
        if target_cell:
            self.build_bridge(source_cell, target_cell)

    def find_target_for_bridge(self, source_cell):
        """Znajduje odpowiednią komórkę do zbudowania mostu"""
        # Lista wszystkich komórek z wyjątkiem źródłowej
        potential_targets = [cell for cell in self.level.cells if cell != source_cell]

        # Jeśli nie ma potencjalnych celów, zwróć None
        if not potential_targets:
            return None

        # Lista komórek, do których już istnieje most z komórki źródłowej
        connected_cells = []
        for bridge in source_cell.bridges:
            if bridge.parent == source_cell:
                connected_cells.append(bridge.destination)
            elif bridge.destination == source_cell:
                connected_cells.append(bridge.parent)

        # Odfiltruj komórki, do których już istnieje połączenie
        unconnected_cells = [cell for cell in potential_targets if cell not in connected_cells]

        # Sprawdź komórki wroga połączone z naszymi (potencjalne half_bridge)
        enemy_connected_to_us = []
        for cell in self.level.cells:
            if cell.color != self.color:  # Komórka wroga
                for bridge in cell.bridges:
                    # Sprawdź czy wrogi most łączy się z dowolną naszą komórką
                    if ((bridge.parent == cell and bridge.destination.color == self.color) or
                            (bridge.destination == cell and bridge.parent.color == self.color)):
                        # Sprawdź czy nie mamy już half_bridge do tej komórki
                        is_already_half_bridge = False
                        for our_bridge in source_cell.bridges:
                            if ((our_bridge.parent == source_cell and our_bridge.destination == cell) or
                                    (our_bridge.destination == source_cell and our_bridge.parent == cell)):
                                is_already_half_bridge = True
                                break

                        if not is_already_half_bridge and cell not in connected_cells:
                            enemy_connected_to_us.append(cell)

        # Jeśli nie ma niepołączonych komórek i żadnych potencjalnych half_bridge, zwróć None
        if not unconnected_cells and not enemy_connected_to_us:
            return None

        # Znajdź wrogie komórki, do których nie ma mostu
        enemy_cells = [cell for cell in unconnected_cells if cell.color != self.color]

        # Znajdź przyjazne komórki, do których nie ma mostu
        friendly_cells = [cell for cell in unconnected_cells if cell.color == self.color]

        # Strategia budowania mostów:
        # 1. 30% szansy na budowanie half_bridge dla ochrony (jeśli są dostępne)
        # 2. 50% szansy na atak na wroga
        # 3. Budowanie połączeń między własnymi komórkami

        if enemy_connected_to_us and random.random() < 0.3:  # 30% szans na half_bridge
            return random.choice(enemy_connected_to_us)
        elif enemy_cells and random.random() < 0.5:  # 50% szans na atak wroga
            return random.choice(enemy_cells)
        elif friendly_cells:
            return random.choice(friendly_cells)
        elif enemy_cells:  # Jeśli nie ma przyjaznych, próbuj wroga
            return random.choice(enemy_cells)
        elif enemy_connected_to_us:  # Ostatnia opcja: half_bridge jeśli nic innego nie jest dostępne
            return random.choice(enemy_connected_to_us)

        # Jeśli nic nie zostało wybrane, zwróć None
        return None

    def build_bridge(self, source_cell, target_cell):
        """Tworzy most między dwoma komórkami"""
        # Sprawdź czy komórka źródłowa ma wystarczającą moc na budowę mostu
        if source_cell.power < 5:  # Minimalny próg mocy do budowania
            return False

        # Tworzenie nowego mostu
        bridge = Bridge(source_cell, target_cell)
        bridge.id = len(source_cell.bridges)
        source_cell.bridges.append(bridge)

        return True

    def cut_own_bridge(self):
        """Próbuje przeciąć własny most"""
        # Zbieranie własnych mostów
        own_bridges = []

        for cell in self.level.cells:
            if cell.color == self.color:
                for bridge in cell.bridges:
                    if bridge.color == self.color and bridge.finished and not bridge.collapse:
                        own_bridges.append(bridge)

        # Jeśli nie ma własnych mostów, nic nie rób
        if not own_bridges:
            return False

        # Wybierz losowy most do przecięcia
        bridge_to_cut = random.choice(own_bridges)

        # Oblicz punkt przecięcia (gdzieś w środku mostu)
        start_pos = bridge_to_cut.real_start
        end_pos = bridge_to_cut.real_end

        # Losowy punkt pomiędzy 25% a 75% długości mostu
        ratio = random.uniform(0.25, 0.75)

        # Oblicz rzeczywiste współrzędne punktu przecięcia
        cut_point = start_pos + (end_pos - start_pos) * ratio

        # Przecięcie mostu
        if not bridge_to_cut.is_half_bridge:
            bridge_to_cut.create_cut(ratio)
        else:
            bridge_to_cut.collapse = True

        return True