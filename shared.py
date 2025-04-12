import pygame

# Ustawienia okna
width_px = None
height_px = None
window_size = None
window = None
game_state = 'main_menu'
game_mode = 'None'

# obiekt klasy poziom
level = None

# Boczne menu trybu pvp
pvp_menu = None
pvp_menu_width = None
pvp_menu_height = height_px
timer_menu = None
turn_button = None
menu = None
level_menu = None
ip_menu = None
saves_menu = None
load_menu = None
online_menu = None
online_status_label = None

# zmienne myszki
LMB = False
RMB = False
mouse_pos = None
events = None

# używana czcionka
font = None
# używane tekstury
purple_texture = None
coin_texture = None

# Definicja kolorów
BLUE = (0, 0, 255)
RED = (255, 0, 0)
BLACK = (0, 0, 0)
DARK_BLUE = (0, 0, 80)
DARK_RED = (139, 0, 0)
WHITE = (255, 255, 255)
DARK_GRAY = (69, 69, 69)
GRAY = (100, 100, 100)
GRAY_TRANSPARENT = (128, 128, 128, 128)
LIGHT_RED = (128, 0, 0)
LIGHT_BLUE = (0, 0, 128)
GREEN = (0, 255, 0)

# Inicjalizacja zegara
clock = None
fps = 60

# do obsługi myszki
# jeżeli nastąpiło clicknięcie to True
click = False

# promień komórki na 1 tierze i o ile się zwiększa na następnych
cell_radius = 35
cell_radius_tier = 5

attack_speed = 1
# ilość regenerowanej siły na sekunde * tier
regen_speed = 0.5
mnoznik = 1 / fps
# ilość segmentów na sekunde
bridge_build_speed = 3
# szybkość komórek na sekundę w pixelach
cell_speed = 200
# cooldown spawnowania komórek w sekundach (tier 1)
spawn_cooldown_s = 2
# szerokość linii rysowanej do cięcia i rysowania mostów
line_width = 5
# początkowy czas na timerach graczy w sekundach
timer_time = 1200
# skala określająca wielkość komórek w pvp, w stosunku do oryginalnych rozmiarów
pvp_scale = 1
# okresla po jakim czasie w sekundach spawnuje sie jednostka w fazie pvp_wait
pvp_spawn_cooldown = 1
# mnożnik szybkości jednostek w pvp
pvp_unit_mul = 3
# mnożnik szybkości budowania mostu w pvp
pvp_bridge_mul = 3
# stała tierów
tier_constant = 10
# ta wartosc pomnożona przez promień komórki daje znać o odległości na jaką może ruszyć się komórka
move_const = 4
# mnoznik mówiący ile px na sekunde będzie się przemieszczać komórka
cell_move_speed = 150
# koszt ilości pixeli za 1 power ruchu komórki
cell_move_cost = cell_radius/2
# długość przerwy między segmentami w pikselach
gap_length = 2
# szerokość mostu
br_thickness = 10
# długość segmentu w moście
segm_len = 40
# wymiary menu końcowego
end_menu_width = 400
end_menu_height = 150
# timers offsets
offset1 = 150
offset2 = 220
# coin size
coin_size = 40
coin_y_offset = 10



# ZMIENNE ZWIĄZANE Z ZARZĄDZANIEM KAMERĄ
gest_cursor_radius = 10
# kamera
cap = None

# ZAPISYWANIE KONFIGURACJI
ip_address = "127.0.0.1"
port = 8080
subnet_mask = "255.255.255.0"
active_connection = False
received_client_message = False
is_host = False
client_ip = None
client_port = None
host_address = None

# przycisk do nagrywania
recording_button = None
recordings_menu = None
# sekundy między klatkami nagrania
frame_speed = 1

# Domyślny adres IP hosta, do którego klient będzie się łączył
host_ip = "192.168.0.191"
host_subnet_mask = "255.255.255.0"
message_to_send = "Cześć!"
client_socket = None

# szerokość / wysokość
ASPECT_RATIO = 1.77777
# Stałe względem wysokości ekranu
CELL_RADIUS_RATIO = 0.0374  # 35/936
CELL_RADIUS_TIER_RATIO = 0.0053  # 5/936
MAX_CELL_RADIUS_RATIO = 0.0588  # 55/936
LINE_WIDTH_RATIO = 0.0053  # 5/936
GEST_CURSOR_RADIUS_RATIO = 0.0107  # 10/936
MAX_MOVE_AREA_RATIO = 0.1496  # 140/936
CELL_MOVE_SPEED_RATIO = 0.1603  # 150/936
CELL_MOVE_COST_RATIO = 0.0187  # 17.5/936

# Stałe interfejsu
SIDE_MENU_WIDTH_RATIO = 0.2  # width_px/5 / width_px
PVP_MENU_HEIGHT_RATIO = 1.0  # height_px / height_px
PVP_MENU_WIDTH_RATIO = 0.2  # width_px/5 / width_px

# Stałe czasowe
TIMER_TIME = 120  # sekundy
SPAWN_COOLDOWN = 2  # sekundy
FRAME_SPEED = 1  # sekundy

# Stałe mnożnikowe
PVP_UNIT_MULTIPLIER = 3
PVP_BRIDGE_MULTIPLIER = 3
BRIDGE_BUILD_SPEED = 3  # segmenty/sekundę
REGEN_SPEED = 0.5  # moc/sekundę/tier

# Stałe gry
TIER_CONSTANT = 10
ATTACK_SPEED = 1


def set_all_variables():
    global width_px, height_px, window_size, pvp_menu_width, pvp_menu_height
    global cell_radius, cell_radius_tier, line_width, cell_move_speed, gest_cursor_radius
    global br_thickness, gap_length, segm_len, cell_move_cost, mnoznik, window
    global end_menu_width, end_menu_height, offset1, offset2, coin_size, coin_y_offset


    # Podstawowe wymiary ekranu
    width_px = int(height_px * ASPECT_RATIO)
    window_size = (width_px, height_px)
    window = pygame.display.set_mode(window_size, pygame.RESIZABLE)

    pvp_menu_width = width_px / 5

    # Elementy komórek
    cell_radius = int(height_px * CELL_RADIUS_RATIO)
    cell_radius_tier = int(height_px * CELL_RADIUS_TIER_RATIO)

    # Elementy interfejsu
    pvp_menu_width = width_px * PVP_MENU_WIDTH_RATIO
    pvp_menu_height = height_px * PVP_MENU_HEIGHT_RATIO

    # Elementy graficzne
    line_width = max(1, int(height_px * LINE_WIDTH_RATIO))
    gest_cursor_radius = int(height_px * GEST_CURSOR_RADIUS_RATIO)

    # Parametry mostu
    br_thickness = int(height_px * LINE_WIDTH_RATIO * 2)
    gap_length = max(1, int(height_px * 0.0021))  # 2/936
    segm_len = int(height_px * 0.0427)  # 40/936

    # Parametry ruchu
    cell_move_speed = int(height_px * CELL_MOVE_SPEED_RATIO)
    cell_move_cost = cell_radius / 2
    mnoznik = 1 / fps

    # Elementy UI
    end_menu_width = int(height_px * 0.4273)  # 400/936
    end_menu_height = int(height_px * 0.1603)  # 150/936
    offset1 = int(height_px * 0.1603)  # 150/936
    offset2 = int(height_px * 0.2350)  # 220/936
    coin_size = int(height_px * 0.0427)  # 40/936
    coin_y_offset = int(height_px * 0.0107)  # 10/936
