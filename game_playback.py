import json
import os
import datetime
import shared


class GamePlayback:
    def __init__(self, level):
        self.level = level
        self.recording_enabled = False
        self.playback_directory = "playback_recordings"
        self.current_recording_file = None
        self.snapshots = []
        self.current_snapshot_index = 0
        self.is_playing = False
        self.playback_speed = 1.0  # Mnożnik szybkości odtwarzania
        self.next_frame_cooldown = 0

        # Tworzenie katalogu dla nagrań, jeśli nie istnieje
        if not os.path.exists(self.playback_directory):
            os.makedirs(self.playback_directory)

    def apply_current_snapshot(self):
        if not self.snapshots or self.current_snapshot_index >= len(self.snapshots):
            return

        current_data = self.snapshots[self.current_snapshot_index]
        try:
            # Zapisz aktualny stan gry
            current_game_state = shared.game_state
            if "shared_variables" in current_data:
                current_data["shared_variables"]["game_state"] = current_game_state

            self.level.save_system_json.load_game_from_data2(current_data)

            # Przywróć stan gry
            shared.game_state = current_game_state

            # Wyświetl informacje o aktualnej turze
            metadata = current_data.get("metadata", {})
            turn_number = metadata.get("turn_number", self.current_snapshot_index + 1)
            active_player = metadata.get("active_player", self.level.active_player)
            player_color = "Niebieski" if active_player == 0 else "Czerwony"

            print(f"Załadowano turę {turn_number}, aktywny gracz: {player_color}")
        except Exception as e:
            print(f"Błąd podczas ładowania snapshotu: {e}")

    def toggle_recording(self):
        """Włącza lub wyłącza nagrywanie"""
        if self.recording_enabled:
            self.stop_recording()
        else:
            self.start_recording()

        return self.recording_enabled

    def start_recording(self):
        """Rozpoczyna nagrywanie nowej sesji"""
        self.recording_enabled = True
        self.snapshots = []

        # Generowanie unikalnej nazwy pliku z datą i czasem
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_recording_file = f"game_recording_{timestamp}.json"

        print(f"Rozpoczęto nagrywanie rozgrywki do pliku: {self.current_recording_file}")

    def stop_recording(self):
        """Zatrzymuje nagrywanie i zapisuje sesję"""
        if not self.recording_enabled:
            return
        self.recording_enabled = False
        if self.snapshots:
            self.save_snapshots_to_file()
            print(f"Zakończono nagrywanie rozgrywki. Zapisano {len(self.snapshots)} tur.")
        else:
            print("Zakończono nagrywanie rozgrywki. Brak zapisanych tur.")

    def capture_snapshot(self):
        """Zapisuje aktualny stan gry jako snapshot"""
        if not self.recording_enabled:
            return

        game_data = {}

        # Tworzenie metadanych dla snapshotu
        metadata = {
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "turn_number": len(self.snapshots) + 1,
            "active_player": self.level.active_player,
            "game_state": shared.game_state,
            "game_mode": shared.game_mode
        }

        try:
            game_data = self._create_game_data_structure()
            game_data["metadata"] = metadata
            self.snapshots.append(game_data)
            print(f"Zapisano snapshot dla tury {metadata['turn_number']}")
        except Exception as e:
            print(f"Błąd podczas tworzenia snapshotu: {e}")

    def _create_game_data_structure(self):
        """Tworzy strukturę danych gry na podstawie istniejącego systemu zapisu JSON"""
        return self.level.save_system_json._convert_to_serializable(
            self.level.save_system_json.save_game(return_data=True)
        )

    def save_snapshots_to_file(self):
        """Zapisuje wszystkie snapshoty do pliku"""
        if not self.snapshots:
            print("Brak snapshotów do zapisania.")
            return False

        file_path = os.path.join(self.playback_directory, self.current_recording_file)

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.snapshots, f, ensure_ascii=False, indent=2)
            print(f"Zapisano nagranie do pliku: {file_path}")
            return True
        except Exception as e:
            print(f"Błąd podczas zapisywania nagrania: {e}")
            return False

    def load_recording(self, filename):
        """Ładuje nagranie z pliku"""
        file_path = os.path.join(self.playback_directory, filename)

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.snapshots = json.load(f)

            self.current_snapshot_index = 0
            print(f"Wczytano nagranie z pliku: {file_path} ({len(self.snapshots)} tur)")
            return True
        except Exception as e:
            print(f"Błąd podczas wczytywania nagrania: {e}")
            return False

    def start_playback(self, filename=None):
        """Rozpoczyna odtwarzanie nagrania z wybranego pliku"""
        if filename:
            success = self.load_recording(filename)
            if not success:
                print(f"Nie udało się załadować nagrania: {filename}")
                return False

        if not self.snapshots:
            print("Brak nagrania do odtworzenia.")
            return False

        shared.game_state = 'playback'
        self.current_snapshot_index = 0
        self.apply_current_snapshot()
        self.is_playing = True
        self.level.playback_active = True
        self.level.advance_to_next_frame = False
        self.level.playback_menu.enable()

        print(f"Rozpoczęto odtwarzanie nagrania. Liczba tur: {len(self.snapshots)}")
        return True

    def stop_playback(self):
        """Zatrzymuje odtwarzanie i wraca do menu głównego"""
        self.is_playing = False
        self.level.playback_active = False
        self.level.advance_to_next_frame = False
        self.level.return_to_main_menu()
        print("Zakończono odtwarzanie nagrania.")

    def get_available_recordings(self):
        """Zwraca listę dostępnych plików z nagraniami"""
        recordings = []

        try:
            if not os.path.exists(self.playback_directory):
                return recordings

            for filename in os.listdir(self.playback_directory):
                if filename.endswith('.json') and filename.startswith('game_recording_'):
                    # Wyciągnij datę z nazwy pliku
                    date_str = filename.replace('game_recording_', '').replace('.json', '')
                    try:
                        # Sformatuj datę na bardziej czytelną
                        date_obj = datetime.datetime.strptime(date_str, "%Y%m%d_%H%M%S")
                        readable_date = date_obj.strftime("%d.%m.%Y %H:%M:%S")

                        recordings.append((filename, readable_date))
                    except:
                        # Jeśli format daty jest nieprawidłowy, użyj oryginalnej nazwy
                        recordings.append((filename, filename))

            # Sortuj nagrania od najnowszych do najstarszych
            recordings.sort(reverse=True)

        except Exception as e:
            print(f"Błąd podczas odczytywania dostępnych nagrań: {e}")

        return recordings