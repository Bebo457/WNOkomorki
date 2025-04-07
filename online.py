import socket
import threading

import shared

def host_game():
    print("Hostowanie gry...")
    server_thread = threading.Thread(target=start_server, args=(shared.ip_address, shared.port))
    server_thread.daemon = True
    server_thread.start()

def connect_to_game():
    print(f"Łączenie z hostem: {shared.host_ip}")
    client_socket = connect_to_server(shared.host_ip, shared.port, shared.message_to_send)
    if client_socket:
        shared.client_socket = client_socket

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
    print(f"Połączenie od {address}")
    try:
        while True:
            data = client_socket.recv(1024)
            if not data:
                break
            message = data.decode('utf-8')
            print(f"Otrzymano: {message}")
            # Tu możesz dodać przetwarzanie otrzymanej wiadomości

            # Przykładowa odpowiedź
            response = "Wiadomość otrzymana"
            client_socket.send(response.encode('utf-8'))
    except Exception as e:
        print(f"Błąd: {e}")
    finally:
        client_socket.close()
        print(f"Połączenie z {address} zamknięte")


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

