import pygame

# Ustawienia okna
width_px = 1664#1280
height_px = 936#720
window_size = (width_px, height_px)
window = pygame.display.set_mode(window_size, pygame.RESIZABLE)
game_state = 'main_menu'
game_mode = 'None'

# Boczne menu trybu pvp
pvp_menu = None
pvp_menu_width = width_px/5
pvp_menu_height = height_px
timer_menu = None
turn_button = None
menu = None
level_menu = None
ip_menu = None
saves_menu = None
load_menu = None
online_menu = None

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
DARK_BLUE = (0, 0, 139)
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
timer_time = 120
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

# ZMIENNE ZWIĄZANE Z ZARZĄDZANIEM KAMERĄ
gest_cursor_radius = 10
# kamera
cap = None

# ZAPISYWANIE KONFIGURACJI
ip_address = "127.0.0.1"
port = 8080
subnet_mask = "255.255.255.0"

# przycisk do nagrywania
recording_button = None
recordings_menu = None
# sekundy między klatkami nagrania
frame_speed = 1

# Domyślny adres IP hosta, do którego klient będzie się łączył
host_ip = "127.0.0.1"
host_mask = "255.255.255.0"

