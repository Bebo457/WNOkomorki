import socket
import threading
import json

import shared

def host_game():
    print("Hostowanie gry...")
    shared.online_status_label.set_title("oczekiwanie na drugiego gracza...")
    shared.is_host = True
    server_thread = threading.Thread(target=start_server, args=(shared.ip_address, shared.port))
    server_thread.daemon = True
    server_thread.start()


def connect_to_game():
    print(f"Łączenie z hostem: {shared.host_ip}")
    # connection_message = f"CONNECT:{shared.ip_address}:{shared.port}"
    client_socket = connect_to_server(shared.host_ip, shared.port)

    if client_socket:
        # Zapisz referencję do socketu
        shared.client_socket = client_socket

        # Przygotuj wiadomość z adresem IP i portem klienta
        connection_message = f"CONNECT:{shared.ip_address}:{shared.port}"

        try:
            # Wyślij wiadomość do hosta
            client_socket.send(connection_message.encode('utf-8'))
            print(f"Wysłano wiadomość: {connection_message}")

            # Czekaj na odpowiedź od hosta
            response = client_socket.recv(1024).decode('utf-8')
            print(f"Otrzymano odpowiedź: {response}")

            # Sprawdź czy połączenie zostało zaakceptowane
            if response.startswith("ACCEPTED:"):
                print("Połączenie zostało zaakceptowane przez hosta")
                shared.active_connection = True
                shared.game_state = 'online_game'

                if hasattr(shared, 'online_status_label'):
                    shared.online_status_label.set_title("połączono")
            else:
                print("Połączenie zostało odrzucone przez hosta")
                if hasattr(shared, 'online_status_label'):
                    shared.online_status_label.set_title("połączenie odrzucone")

                # Zamknij socket w przypadku odrzucenia
                client_socket.close()
                shared.client_socket = None

        except Exception as e:
            print(f"Błąd podczas wysyłania danych do hosta: {e}")
            client_socket.close()
            shared.client_socket = None

def send_message(message):
    if hasattr(shared, 'client_socket') and shared.client_socket:
        try:
            shared.client_socket.send(message.encode('utf-8'))
        except Exception as e:
            print(f"Błąd podczas wysyłania: {e}")


def receive_messages(client_socket):
    try:
        while True:
            data = client_socket.recv(1024)
            if not data:
                break
            message = data.decode('utf-8')
            print(f"Otrzymano: {message}")
            # Tu możesz dodać obsługę otrzymanej wiadomości w grze
    except Exception as e:
        print(f"Błąd: {e}")
    finally:
        client_socket.close()


def connect_to_server(host, port, message):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect((host, port))
        print(f"Połączono z {host}:{port}")

        # Utwórz wątek do odbierania wiadomości
        receive_thread = threading.Thread(target=receive_messages, args=(client,))
        receive_thread.daemon = True
        receive_thread.start()

        # Wyślij wiadomość
        client.send(message.encode('utf-8'))

        return client  # Zwróć socket, aby można było go używać później
    except Exception as e:
        print(f"Błąd podczas łączenia: {e}")
        client.close()
        return None


def handle_client(client_socket, address):
    """Obsługuje połączenie od klienta"""
    print(f"Połączenie od {address}")
    shared.client_socket = client_socket  # Zapisz socket klienta do późniejszego użycia

    try:
        while True:
            data = client_socket.recv(1024)
            if not data:
                break

            message = data.decode('utf-8')
            print(f"Otrzymano: {message}")

            # Zapisz wiadomość i ustaw flagę
            shared.client_message = message
            shared.received_client_message = True

            # Tutaj możesz dodać obsługę różnych typów wiadomości

    except Exception as e:
        print(f"Błąd podczas obsługi klienta: {e}")
    finally:
        client_socket.close()
        print(f"Połączenie z {address} zamknięte")
        # Resetowanie zmiennych po rozłączeniu
        shared.active_connection = False
        shared.client_socket = None
        if hasattr(shared, 'online_status_label'):
            shared.online_status_label.set_title("rozłączono")


def start_server(host, port):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen(5)
    print(f"Serwer nasłuchuje na {host}:{port}")

    try:
        while True:
            client, address = server.accept()
            client_thread = threading.Thread(target=handle_client, args=(client, address))
            client_thread.daemon = True
            client_thread.start()
    except KeyboardInterrupt:
        print("Serwer zatrzymany")
    finally:
        server.close()


def send_variables(variables_dict):
    """
    Wysyła słownik zmiennych jako JSON do połączonego klienta/hosta.

    Args:
        variables_dict (dict): Słownik zawierający zmienne do wysłania

    Returns:
        bool: True jeśli wysłano pomyślnie, False w przypadku błędu
    """
    if hasattr(shared, 'client_socket') and shared.client_socket:
        try:
            # Konwertuj słownik na string JSON
            json_data = json.dumps(variables_dict)

            # Dodaj prefix "JSON:" aby odbiorca mógł rozpoznać typ danych
            message = f"JSON:{json_data}"

            # Wyślij dane
            shared.client_socket.send(message.encode('utf-8'))
            print(f"Wysłano zmienne: {variables_dict}")
            return True
        except Exception as e:
            print(f"Błąd podczas wysyłania zmiennych: {e}")
    else:
        print("Brak aktywnego połączenia socket")
    return False


# Funkcja pomocnicza do odczytywania zmiennych z odebranej wiadomości
def parse_received_data(data):
    """
    Parsuje odebrane dane, sprawdzając czy to zwykła wiadomość czy dane JSON.

    Args:
        data (str): Odebrane dane jako string

    Returns:
        tuple: (typ_danych, zawartość) gdzie typ_danych to 'message' lub 'json'
    """
    if data.startswith("JSON:"):
        try:
            # Usuń prefix "JSON:" i sparsuj pozostałą część jako JSON
            json_str = data[5:]  # Usuń pierwsze 5 znaków ("JSON:")
            variables = json.loads(json_str)
            return ('json', variables)
        except json.JSONDecodeError as e:
            print(f"Błąd dekodowania JSON: {e}")
            return ('message', data)
    else:
        return ('message', data)


def handle_received_variables(variables):
    """
    Obsługuje odebrane zmienne - możesz dostosować tę funkcję
    do potrzeb swojej gry.

    Args:
        variables (dict): Słownik z odebranymi zmiennymi
    """
    # Przykład: jeśli otrzymano informacje o pozycji gracza, zaktualizuj ją
    if 'player_position' in variables:
        print(f"Aktualizacja pozycji gracza: {variables['player_position']}")
        # shared.remote_player_position = variables['player_position']

    # Przykład: jeśli otrzymano informacje o komórkach
    if 'cells' in variables:
        print(f"Otrzymano dane o {len(variables['cells'])} komórkach")
        # Tu możesz dodać kod do aktualizacji stanu komórek w grze

    # Możesz dodać więcej warunków dla różnych typów danych


def validate_ip_address(ip):
    """
    Sprawdza czy podany ciąg znaków jest poprawnym adresem IPv4.

    Args:
        ip (str): Adres IP do sprawdzenia

    Returns:
        bool: True jeśli adres jest poprawny, False w przeciwnym razie
    """
    try:
        # Sprawdź czy adres IP ma 4 części
        parts = ip.split('.')
        if len(parts) != 4:
            return False

        # Sprawdź czy każda część jest liczbą z zakresu 0-255
        for part in parts:
            if not part.isdigit():
                return False
            num = int(part)
            if num < 0 or num > 255:
                return False

        return True
    except:
        return False


def handle_incoming_connection():
    """
    Sprawdza czy jest nowe połączenie od klienta i przetwarza je.
    Tę funkcję należy wywołać cyklicznie w online_menu_loop.
    """
    # Sprawdź czy jesteśmy hostem i czy mamy nowe połączenie
    if shared.is_host and shared.received_client_message:
        client_message = shared.client_message
        try:
            # Sprawdź czy wiadomość zawiera poprawny format połączenia
            if client_message.startswith("CONNECT:"):
                parts = client_message[8:].split(':')
                if len(parts) == 2:
                    client_ip = parts[0]
                    client_port_str = parts[1]

                    # Walidacja portu
                    if client_port_str.isdigit():
                        client_port = int(client_port_str)

                        # Walidacja adresu IP i zakresu portu
                        if validate_ip_address(client_ip) and 1024 <= client_port <= 65535:
                            print(f"Poprawne połączenie od klienta {client_ip}:{client_port}")

                            # Zapisz dane klienta
                            shared.client_ip = client_ip
                            shared.client_port = client_port

                            # Ustaw flagę aktywnego połączenia
                            shared.active_connection = True

                            # Zmień stan gry
                            shared.game_state = 'online_game'

                            # Wyślij potwierdzenie do klienta
                            if hasattr(shared, 'client_socket') and shared.client_socket:
                                try:
                                    response = "ACCEPTED:CONNECTION_ESTABLISHED"
                                    shared.client_socket.send(response.encode('utf-8'))
                                except Exception as e:
                                    print(f"Błąd podczas wysyłania potwierdzenia: {e}")

                            # Aktualizuj etykietę statusu
                            if hasattr(shared, 'online_status_label'):
                                shared.online_status_label.set_title("połączono")
                        else:
                            print(f"Niepoprawny adres IP lub port: {client_ip}:{client_port}")
                            # Możesz wysłać odpowiedź odmowną
                            if hasattr(shared, 'client_socket') and shared.client_socket:
                                try:
                                    response = "REJECTED:INVALID_ADDRESS"
                                    shared.client_socket.send(response.encode('utf-8'))
                                except Exception as e:
                                    print(f"Błąd podczas wysyłania odrzucenia: {e}")
                    else:
                        print(f"Niepoprawny format portu: {client_port_str}")
                else:
                    print("Niepoprawny format wiadomości połączeniowej")
            else:
                print(f"Nierozpoznany format wiadomości: {client_message}")
        except Exception as e:
            print(f"Błąd podczas przetwarzania wiadomości od klienta: {e}")

        # Zresetuj flagę otrzymanej wiadomości
        shared.received_client_message = False