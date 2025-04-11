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
    connection_message = f"CONNECT:{shared.ip_address}:{shared.port}"
    client_socket = connect_to_server(shared.host_ip, shared.port, connection_message)

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
                # ------------------------------------TUTAJ DAWAĆ RZECZY PRZY INICJALICAJI KLIENTA ---------------------
                shared.active_connection = True
                shared.game_state = 'online_setup'  # Zmieniono na online_setup zamiast online_game
                shared.level.pvp_side_menu_setup()
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
            data = client_socket.recv(8192)  # Zwiększono bufor dla większych danych
            if not data:
                break

            message = data.decode('utf-8')

            # Sprawdź początek wiadomości, aby określić jej typ
            if message.startswith("GAME_STATE:"):
                # Wyodrębnij dane JSON ze stanu gry
                json_data = message[11:]  # Usuń prefix "GAME_STATE:"
                print("Otrzymano stan gry od hosta")
                process_game_state(json_data)
            else:
                print(f"Otrzymano: {message}")
                # Zapisz wiadomość i ustaw flagę
                shared.client_message = message
                shared.received_client_message = True
    except Exception as e:
        print(f"Błąd: {e}")
    finally:
        client_socket.close()


def process_game_state(json_data):
    """Przetwórz otrzymany stan gry i załaduj do lokalnej instancji gry"""
    try:
        # Konwertuj string JSON na słownik Pythona
        game_data = json.loads(json_data)

        # Załaduj stan gry używając istniejącego systemu z save_system_json
        if hasattr(shared, "level") and hasattr(shared.level, "save_system_json"):
            success = shared.level.save_system_json.load_game_from_data(game_data)
            if success:
                print("Stan gry załadowany pomyślnie")
                shared.game_state = 'online_setup'
            else:
                print("Nie udało się załadować stanu gry")
        else:
            print("Brak dostępu do obiektu poziomu lub systemu zapisu")
    except json.JSONDecodeError as e:
        print(f"Błąd podczas dekodowania danych JSON: {e}")
    except Exception as e:
        print(f"Błąd podczas przetwarzania stanu gry: {e}")


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
        # Odbierz pierwszą wiadomość od klienta
        data = client_socket.recv(1024)
        if not data:
            return

        message = data.decode('utf-8')
        print(f"Otrzymano pierwszą wiadomość: {message}")

        # Sprawdź, czy jest to wiadomość połączeniowa
        if message.startswith("CONNECT:"):
            parts = message[8:].split(':')
            if len(parts) == 2:
                client_ip = parts[0]
                client_port = parts[1]

                # Akceptuj połączenie
                response = "ACCEPTED:CONNECTION_ESTABLISHED"
                client_socket.send(response.encode('utf-8'))
                print(f"Zaakceptowano połączenie od {client_ip}:{client_port}")

                # ------------------------------------------ USTAWIANIE ZMIENNYCH DLA KLIENTA ------------------------
                shared.client_ip = client_ip
                shared.client_port = int(client_port)
                shared.active_connection = True
                shared.game_state = 'online_setup'  # Zmieniono na online_setup zamiast online_game
                shared.level.pvp_side_menu_setup()

                # Aktualizuj status
                if hasattr(shared, 'online_status_label'):
                    shared.online_status_label.set_title("połączono")

                # Wyślij stan gry do klienta
                send_game_state_to_client()

                # Kontynuuj odbieranie wiadomości
                while True:
                    data = client_socket.recv(4096)
                    if not data:
                        break

                    message = data.decode('utf-8')
                    print(f"Otrzymano: {message}")

                    # Zapisz wiadomość i ustaw flagę
                    shared.client_message = message
                    shared.received_client_message = True
                    shared.level.online_active = True
            elif message.startswith("GAME_STATE:"):
                json_data = message[11:]
                process_game_state(json_data)  # Dodaj funkcję jeśli chcesz
            elif message.startswith("JSON:"):
                typ, dane = parse_received_data(message)
                if typ == 'json':
                    print("Host otrzymał dane JSON:", dane)
            else:
                print(f"Zwykła wiadomość: {message}")
        else:
            print(f"Nieoczekiwany format pierwszej wiadomości: {message}")

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


def send_game_state_to_client():
    """Wysyła aktualny stan gry do klienta"""
    try:
        if not hasattr(shared, "level") or not hasattr(shared.level, "save_system_json"):
            print("Brak dostępu do obiektu poziomu lub systemu zapisu")
            return

        # Pobierz stan gry jako słownik
        game_data = shared.level.save_system_json.save_game(return_data=True)
        if not game_data:
            print("Nie udało się uzyskać danych gry")
            return

        # Konwertuj na JSON
        json_data = json.dumps(shared.level.save_system_json.convert_to_serializable(game_data))

        # Dodaj prefix do identyfikacji typu wiadomości
        full_message = f"GAME_STATE:{json_data}"

        if shared.client_socket:
            shared.client_socket.send(full_message.encode('utf-8'))
            print("Stan gry wysłany do klienta")
        else:
            print("Brak podłączonego klienta")
    except Exception as e:
        print(f"Błąd podczas wysyłania stanu gry: {e}")


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


# Ta funkcja została przeniesiona do klasy Level w pliku level.py
# i powinna być wywoływana jako level.online_loop_setup()


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
                            shared.game_state = 'online_setup'

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

# Ta funkcja już istnieje w level.py i powinna być używana stamtąd