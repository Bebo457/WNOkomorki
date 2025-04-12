import sys
from level import Level
import shared
import pygame
import pygame_menu
from config_manager import ConfigManager
import online

# Inicjalizacja Pygame
pygame.init()

# Ustawianie rozmiarów ekranu (najlepiej w stosunku 1280 x 720)
shared.height_px = 700
shared.set_all_variables()
window_size = (shared.width_px, shared.height_px)
shared.window = pygame.display.set_mode(window_size, pygame.RESIZABLE)

# inicjalizacja menażdżera konfiguracji
config_manager = ConfigManager()

# Do zapisywania IP, portu i maski podsieci
loaded_config = config_manager.load_config()
shared.ip_address = loaded_config["ip_address"]
shared.port = loaded_config["port"]
shared.subnet_mask = loaded_config["subnet_mask"]


def show_recordings_menu():
    """Wyświetla menu wyboru nagrania do odtworzenia"""
    shared.game_state = 'recordings_menu'
    shared.menu.disable()

    # Pobierz dostępne nagrania
    recordings = level.playback.get_available_recordings()

    # Odśwież menu nagrań
    shared.recordings_menu.clear()

    if not recordings:
        shared.recordings_menu.add.label("Brak dostępnych nagrań")
    else:
        for filename, date in recordings:
            shared.recordings_menu.add.button(f"Nagranie z {date}", lambda f=filename: start_playback(f))

    shared.recordings_menu.add.button("Powrót", return_to_main_menu)
    shared.recordings_menu.enable()


def start_playback(filename):
    """Rozpoczyna odtwarzanie wybranego nagrania"""
    success = level.playback.start_playback(filename)
    if success:
        shared.recordings_menu.disable()


def recordings_menu_loop():
    """Obsługuje menu wyboru nagrania"""
    shared.recordings_menu.draw(shared.window)
    shared.recordings_menu.update(shared.events)


def toggle_recording():
    """Obsługuje przycisk włączania/wyłączania nagrywania gry"""
    is_recording = level.toggle_recording()
    if is_recording:
        shared.recording_button.set_title('Wyłącz nagrywanie gry')
    else:
        shared.recording_button.set_title('Włącz nagrywanie gry')


def classic_mode_menu():
    global menu
    shared.game_state = 'level_menu'
    shared.game_mode = 'single'
    shared.menu.disable()
    shared.level_menu.enable()


def return_to_main_menu():
    global menu
    shared.level_menu.disable()
    shared.menu.enable()


def main_menu():
    global menu
    shared.menu.draw(shared.window)
    shared.menu.update(shared.events)


def level_menu_loop():
    shared.level_menu.draw(shared.window)
    shared.level_menu.update(shared.events)


def start_pvp_mode():
    global level
    shared.game_state = 'pvp_setup'
    shared.game_mode = 'local'
    shared.menu.disable()
    pvp_side_menu_setup()


def start_pvp_mode_online():
    global level
    shared.game_state = 'pvp_setup'
    shared.game_mode = 'Online'
    shared.menu.disable()
    pvp_side_menu_setup()


def pvp_side_menu_setup():
    global menu
    shared.menu.disable()
    shared.pvp_menu = pygame_menu.Menu('WYBÓR KOMÓREK STARTOWYCH', shared.pvp_menu_width, 0.7 * shared.pvp_menu_height,
                                       theme=pygame_menu.themes.THEME_DARK)
    shared.pvp_menu.widget_alignment = 'align_top'
    shared.pvp_menu.set_relative_position(100, 0)
    shared.pvp_menu.add.button('Sklep', level.activate_shop)
    shared.pvp_menu.add.button('Powrót', level.return_to_main_menu)
    shared.timer_menu.enable()


def start_ip_menu():
    global menu
    shared.game_state = 'ip_menu'
    shared.game_mode = 'None'
    shared.menu.disable()
    shared.ip_menu.enable()
    # Aktualizuj wartości w polach tekstowych
    ip_input.set_value(shared.ip_address if hasattr(shared, "ip_address") else "127.0.0.1")
    port_input.set_value(str(shared.port) if hasattr(shared, "port") else "8080")
    mask_input.set_value(shared.subnet_mask if hasattr(shared, "subnet_mask") else "255.255.255.0")


def ip_menu_loop():
    shared.ip_menu.draw(shared.window)
    shared.ip_menu.update(shared.events)


# Definicja funkcji walidującej i zapisującej dane przed inicjalizacją menu
def validate_and_save_ip_config():
    global ip_input, port_input, mask_input, ip_error, port_error, mask_error

    # Pobranie wartości z pól tekstowych
    ip_value = ip_input.get_value()
    port_value = port_input.get_value()
    mask_value = mask_input.get_value()

    # Walidacja adresu IP
    is_ip_valid = True
    parts = ip_value.split('.')
    if len(parts) != 4:
        is_ip_valid = False
    else:
        for part in parts:
            if not part.isdigit() or int(part) < 0 or int(part) > 255:
                is_ip_valid = False
                break

    # Walidacja portu
    is_port_valid = True
    if not port_value.isdigit():
        is_port_valid = False
    else:
        port_num = int(port_value)
        if port_num < 1024 or port_num > 65535:
            is_port_valid = False

    # Walidacja maski podsieci
    is_mask_valid = True
    parts = mask_value.split('.')
    if len(parts) != 4:
        is_mask_valid = False
    else:
        for part in parts:
            if not part.isdigit() or int(part) < 0 or int(part) > 255:
                is_mask_valid = False
                break

        # Dodatkowa walidacja - sprawdzenie czy maska jest poprawna
        # Prawidłowa maska powinna mieć ciągłe jedynki w reprezentacji binarnej,
        # a następnie same zera
        if is_mask_valid:
            bin_mask = ''.join([bin(int(part))[2:].zfill(8) for part in parts])
            if '01' in bin_mask:  # Sprawdza, czy po 0 występuje 1, co jest nieprawidłowe
                is_mask_valid = False

    # Aktualizacja komunikatów o błędach
    ip_error.set_title(' ' if is_ip_valid else 'Niepoprawny format adresu IP!')
    port_error.set_title(' ' if is_port_valid else 'Port musi być liczbą z zakresu 1024-65535!')
    mask_error.set_title(' ' if is_mask_valid else 'Niepoprawny format maski podsieci!')

    # Jeśli wszystko jest poprawne, zapisz dane
    if is_ip_valid and is_port_valid and is_mask_valid:
        shared.ip_address = ip_value
        shared.port = int(port_value)
        shared.subnet_mask = mask_value

        # Zapisz konfigurację do pliku
        config_manager.save_config(shared.ip_address, shared.port, shared.subnet_mask)

        print(f"Zapisano konfigurację: IP={shared.ip_address}, Port={shared.port}, Maska={shared.subnet_mask}")

        # Powrót do głównego menu
        level.return_to_main_menu()
        return True

    return False

def update_host_ip(value):
    """Aktualizuje adres IP hosta, do którego będziemy się łączyć"""
    shared.host_ip = value
    print(f"Zaktualizowano adres IP hosta na: {shared.host_ip}")

def update_host_subnet_mask(value):
    """Aktualizuje maskę podsieci dla połączenia online"""
    shared.host_subnet_mask = value
    print(f"Zaktualizowano maskę podsieci na: {shared.host_subnet_mask}")

def show_online_menu():
    """Wyświetla menu gry online"""
    shared.game_state = 'online_menu'
    shared.menu.disable()
    shared.online_menu.enable()

def return_from_online_menu():
    """Powrót z menu online do menu głównego"""
    shared.online_status_label.set_title(" ")
    shared.is_host = False
    shared.game_state = 'main_menu'
    shared.online_menu.disable()
    shared.menu.enable()

def online_menu_loop():
    """Obsługuje menu gry online"""
    if shared.online_menu.is_enabled():
        shared.online_menu.draw(shared.window)
        shared.online_menu.update(shared.events)
        online.handle_incoming_connection()


def update_message(value):
    """Aktualizuje wiadomość do wysłania"""
    shared.message_to_send = value
    print(f"Zaktualizowano wiadomość do wysłania: {shared.message_to_send}")

pygame.display.set_caption('WOJNA KOMOREK')

# Ustawienia gry
tile_texture_path = "textures/background.jpg"
coin_texture_path = "textures/coin.png"

# Ładowanie obrazu
shared.purple_texture = pygame.image.load(tile_texture_path)
texture = pygame.transform.scale(shared.purple_texture, window_size)

shared.coin_texture = pygame.image.load(coin_texture_path).convert_alpha()

# Inicjalizacja klasy poziomu
level = Level()
shared.level = level
shared.game_state = 'main_menu'
previous_LMB_state = False
# Konfigurowanie menu
shared.menu = pygame_menu.Menu('Menu', shared.width_px, shared.height_px, theme=pygame_menu.themes.THEME_DARK)
shared.menu.add.button('1 gracz', classic_mode_menu)
shared.menu.add.button('2 graczy lokalnie', start_pvp_mode)
shared.menu.add.button('Gra sieciowa', show_online_menu)
shared.menu.add.button('Adres IP i port', start_ip_menu)
shared.menu.add.button('Zapisz stan gry (XML)', level.save_game_xml)
shared.menu.add.button('Ładuj zapis gry (XML)', level.load_game_xml)
shared.menu.add.button('Zapisz stan gry (Firebase)', level.save_game_firebase)
shared.menu.add.button('Ładuj zapis gry (Firebase)', level.load_game_firebase)
shared.menu.add.button('Zapisz stan gry (JSON)', level.save_game_json)
shared.menu.add.button('Ładuj zapis gry (JSON)', level.load_game_json)
shared.recording_button = shared.menu.add.button('Włącz nagrywanie gry', toggle_recording)
shared.menu.add.button('Odtwórz nagranie', show_recordings_menu)
shared.menu.add.button('Wyjście', pygame_menu.events.EXIT)

shared.level_menu = pygame_menu.Menu('Wybierz Poziom', shared.width_px, shared.height_px, theme=pygame_menu.themes.THEME_DARK)
shared.level_menu.add.button('Poziom 1', level.set_level_1)
shared.level_menu.add.button('Poziom 2', level.set_level_2)
shared.level_menu.add.button('Poziom 3', level.set_level_3)
shared.level_menu.add.button('Powrót', level.return_to_main_menu)

# Inicjalizacji IP_menu
shared.ip_menu = pygame_menu.Menu('Konfiguracja połączenia', shared.width_px, shared.height_px, theme=pygame_menu.themes.THEME_DARK)

# Dodanie pola z adresem IP z walidacją
ip_default = shared.ip_address if hasattr(shared, "ip_address") else "127.0.0.1"
ip_input = shared.ip_menu.add.text_input(
    'Adres IP: ',
    default=ip_default,
    maxchar=15,
    input_underline='_',
    textinput_id='ip_textinput'
)

# Dodanie etykiety z podpowiedzią dla IP
ip_help = shared.ip_menu.add.label('Format: xxx.xxx.xxx.xxx (np. 192.168.1.1)')
ip_error = shared.ip_menu.add.label(' ')  # Miejsce na komunikat o błędzie

# Dodanie pola z maską podsieci
mask_default = shared.subnet_mask if hasattr(shared, "subnet_mask") else "255.255.255.0"
mask_input = shared.ip_menu.add.text_input(
    'Maska podsieci: ',
    default=mask_default,
    maxchar=15,
    input_underline='_',
    textinput_id='mask_textinput'
)

# Dodanie etykiety z podpowiedzią dla maski
mask_help = shared.ip_menu.add.label('Format: xxx.xxx.xxx.xxx (np. 255.255.255.0)')
mask_error = shared.ip_menu.add.label(' ')  # Miejsce na komunikat o błędzie

# Dodanie pola z portem z walidacją
port_default = str(shared.port) if hasattr(shared, "port") else "8080"
port_input = shared.ip_menu.add.text_input(
    'Port: ',
    default=port_default,
    maxchar=5,
    input_underline='_',
    textinput_id='port_textinput'
)

# Dodanie etykiety z podpowiedzią dla portu
port_help = shared.ip_menu.add.label('Zakres portów: 1024-65535')
port_error = shared.ip_menu.add.label(' ')  # Miejsce na komunikat o błędzie

shared.ip_menu.add.button('Zapisz konfigurację', validate_and_save_ip_config)
shared.ip_menu.add.button('Powrót', level.return_to_main_menu)

# inicjalizacja timer menu
shared.timer_menu = pygame_menu.Menu('', shared.pvp_menu_width, 0.3 * shared.height_px, theme=pygame_menu.themes.THEME_DARK)
shared.timer_menu.set_relative_position(100, 100)
shared.turn_button = shared.timer_menu.add.button('ODDAJ TURĘ', level.give_turn)
shared.turn_button.set_position(70, 70)
shared.timer_menu.disable()

# Inicjalizacja menu online
shared.online_menu = pygame_menu.Menu('Gra Online', shared.width_px, shared.height_px, theme=pygame_menu.themes.THEME_DARK)
shared.online_menu.add.button('Hostuj grę', online.host_game)
host_ip_input = shared.online_menu.add.text_input('Adres IP: ', default=shared.host_ip, onchange=update_host_ip)
subnet_mask_input = shared.online_menu.add.text_input('Maska podsieci: ', default=shared.host_subnet_mask, onchange=update_host_subnet_mask)
message_input = shared.online_menu.add.text_input('Wiadomość: ', default=shared.message_to_send, onchange=update_message, maxchar=100)
shared.online_menu.add.button('Połącz', online.connect_to_game)
shared.online_status_label = shared.online_menu.add.label(' ')
shared.online_menu.add.button('Powrót', return_from_online_menu)

# Inicjalizacja menu nagrania
shared.recordings_menu = pygame_menu.Menu('Wybierz nagranie', shared.width_px, shared.height_px, theme=pygame_menu.themes.THEME_DARK)

# inicjalizacja czcionki
pygamefont = pygame.font.Font(None, 30)
shared.font = pygamefont
shared.clock = pygame.time.Clock()

# Główna pętla
while True:
    shared.window.fill(shared.DARK_GRAY)
    # Obliczanie FPS
    global fps
    shared.fps = shared.clock.get_fps()
    events = pygame.event.get()
    shared.events = events
    shared.mouse_pos = pygame.mouse.get_pos()
    shared.LMB = False
    shared.RMB = False
    shared.click = False
    # zbieranie informacji o myszce
    for event in shared.events:
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                shared.LMB = True
                previous_LMB_state = True
            elif event.button == 0 and previous_LMB_state:
                previous_LMB_state = False
            if event.button == 3:
                shared.RMB = True
    if previous_LMB_state and not shared.LMB:
        previous_LMB_state = False
        shared.click = True
    if shared.game_state == 'main_menu':
        main_menu()
    elif shared.game_state == 'level_menu':
        level_menu_loop()
    elif shared.game_state == 'online_menu':
        online_menu_loop()
    elif shared.game_state == 'level_classic':
        level.level_loop()
    elif shared.game_state == 'pvp_setup':
        level.pvp_loop_setup()
    elif shared.game_state == 'pvp_turn' or shared.game_state == 'pvp_wait' or shared.game_state == 'pvp_end':
        level.pvp_loop()
    elif shared.game_state == 'ip_menu':
        ip_menu_loop()
    elif shared.game_state == 'online_setup':
        level.online_loop_setup()
    elif shared.game_state == 'online_pvp_turn':
        level.pvp_loop()
    elif shared.game_state == 'online_pvp_wait':
        level.pvp_loop()
    elif shared.game_state == 'recordings_menu':
        recordings_menu_loop()
    elif shared.game_state == 'playback':
        if level.playback_active:
            level.playback_loop()
        else:
            shared.game_state = 'main_menu'


    pygame.display.flip()
    shared.clock.tick(60)

level.gest_sys.stop()