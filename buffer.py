def level_loop(self):
    click = shared.click
    LMB = shared.LMB
    RMB = shared.RMB
    mouse_pos = shared.mouse_pos
    window = shared.window

    # Ustawienie aktywnego gracza zawsze na niebieskiego (indeks 0)
    self.active_player = 0

    # Rysowanie paska bocznego (menu)
    battle_texture = pygame.transform.scale(shared.purple_texture, (self.game_area_width, self.game_area_height))
    self.battle_area_surface.blit(battle_texture, (0, 0))

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
    # oddzielna pętla dla dobrej kolejności rysowania
    for cell in self.cells:
        for bridge in cell.bridges:
            bridge.draw_bridge(shared.window)
    for cell in self.cells:
        for bridge in cell.bridges:
            for unit in bridge.units:
                unit.draw_unit(shared.window)
    # zmienna potrzebna do wykrywania przecinania
    any_cell_hovered = False
    # obsługa kliknięć myszką
    for cell in self.cells:
        cell.cell_state_update()
        if cell.is_hovered(mouse_pos):
            any_cell_hovered = True
        if cell.activated_connection:
            draw_dashed_line(window, cell.color, (cell.position[0], cell.position[1]), mouse_pos, 10, 3)
        cell.draw(shared.window, shared.font)

        # Dodana walidacja koloru komórki - możemy operować tylko na niebieskich komórkach
        if cell.is_clicked_lmb(LMB) and not self.activated_cell_connection and not self.lock and cell.color == \
                self.players[self.active_player].color:
            cell.activated_connection = True
            self.activated_cell_connection = True
            self.clicked_cell_id = cell.id
        if self.activated_cell_connection and cell.is_hovered(
                mouse_pos) and LMB and not self.clicked_cell_id == cell.id:
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
            # Dodana walidacja koloru komórki - tylko niebieski gracz może przecinać
            if cell.color == self.players[self.active_player].color:
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
                                # do wykrycia błędu
                                if cut_bridge_ratio >= 1:
                                    print('cut_bridge_ratio wieksze od 1')
                                bridge.create_cut(cut_bridge_ratio)
                            else:
                                bridge.collapse = True
                                print('przeciecie')
                        else:
                            bridge.collapse = True

    elif not any_cell_hovered and not self.activated_cell_connection and click:
        self.cutting = True
        self.cutting_start_pos = mouse_pos
    if self.cutting:
        pygame.draw.line(shared.window, shared.WHITE, self.cutting_start_pos, mouse_pos, shared.line_width)
    if self.cutting and RMB:
        self.cutting = False
    if self.classic_mode_menu.is_enabled():
        self.classic_mode_menu.update(shared.events)
        self.classic_mode_menu.draw(shared.window)
    shared.window.blit(self.battle_area_surface, (0, 0))

    # Wyświetlanie informacji o aktywnym graczu (podobnie jak w pvp_loop)
    font = pygame.font.Font(None, 40)
    label = "Niebieski"
    text_surface = font.render(label, True, shared.BLUE)
    text_x = self.game_area_width + (self.side_menu_width // 2 - text_surface.get_width() // 2)
    text_y = 0.65 * self.game_area_height
    shared.window.blit(text_surface, (text_x, text_y))