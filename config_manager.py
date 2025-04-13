import json
import os


class ConfigManager:
    def __init__(self):
        self.config_directory = "config"
        self.config_filename = "network_config.json"
        self.config_path = os.path.join(self.config_directory, self.config_filename)

        # Domyślne wartości konfiguracyjne
        self.default_config = {
            "ip_address": "127.0.0.1",
            "port": 8080,
            "subnet_mask": "255.255.255.0"
        }

        # Upewnij się, że katalog konfiguracyjny istnieje
        if not os.path.exists(self.config_directory):
            os.makedirs(self.config_directory)

    def load_config(self):
        """Ładuje konfigurację z pliku JSON. Jeśli plik nie istnieje, zwraca domyślne wartości."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # Sprawdź, czy wszystkie potrzebne klucze są obecne
                    keys_to_check = ["ip_address", "port", "subnet_mask"]
                    if all(key in config for key in keys_to_check):
                        return config
                    else:
                        # Jeśli brakuje tylko subnet_mask, dodaj ją z domyślną wartością
                        if "ip_address" in config and "port" in config and "subnet_mask" not in config:
                            config["subnet_mask"] = self.default_config["subnet_mask"]
                            return config
                        else:
                            print("Plik konfiguracyjny ma niepoprawny format. Używam domyślnej konfiguracji.")
                            return self.default_config
            else:
                print(f"Plik konfiguracyjny nie istnieje. Używam domyślnej konfiguracji.")
                return self.default_config
        except Exception as e:
            print(f"Błąd podczas wczytywania konfiguracji: {e}")
            return self.default_config

    def save_config(self, ip_address, port, subnet_mask):
        """Zapisuje konfigurację do pliku JSON."""
        try:
            config = {
                "ip_address": ip_address,
                "port": port,
                "subnet_mask": subnet_mask
            }

            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=4)

            print(f"Konfiguracja zapisana pomyślnie do {self.config_path}")
            return True
        except Exception as e:
            print(f"Błąd podczas zapisywania konfiguracji: {e}")
            return False