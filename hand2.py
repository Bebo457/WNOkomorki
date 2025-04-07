import cv2
import mediapipe as mp
import math

class HandGestureSystem:
    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils
        self.hands = None
        self.active = False
        self.reading_enabled = False  # Flaga do kontrolowania odczytu danych
        self.palm_center = (0, 0)
        self.avg_distance = 0
        self.is_fist = False

    def start(self):
        """
        Uruchamia system rozpoznawania dłoni.
        """
        self.hands = self.mp_hands.Hands(min_detection_confidence=0.5, min_tracking_confidence=0.5)
        self.active = True
        self.reading_enabled = True  # Automatyczne włączenie odczytu przy starcie

    def stop(self):
        """
        Wyłącza system rozpoznawania dłoni.
        """
        if self.hands:
            self.hands.close()
        self.active = False
        self.reading_enabled = False  # Wyłączenie odczytu po zatrzymaniu systemu

    def enable_reading(self):
        """
        Włącza odczyt danych z kamery.
        """
        if self.active:
            self.reading_enabled = True

    def disable_reading(self):
        """
        Wyłącza odczyt danych z kamery.
        """
        self.reading_enabled = False

    def get_palm_center(self, landmarks):
        """
        Oblicza środek dłoni.
        """
        key_points = [landmarks[0], landmarks[5], landmarks[9], landmarks[13], landmarks[17]]
        center_x = sum(point.x for point in key_points) / len(key_points)
        center_y = sum(point.y for point in key_points) / len(key_points)
        return center_x, center_y

    def calculate_average_distance(self, landmarks, palm_center):
        """
        Oblicza średnią odległość palców od środka dłoni.
        """
        distances = []
        center_x, center_y = palm_center

        # Landmarky końcówek palców: 4, 8, 12, 16, 20
        finger_tips = [landmarks[4], landmarks[8], landmarks[12], landmarks[16], landmarks[20]]

        for tip in finger_tips:
            distance = math.sqrt((tip.x - center_x) ** 2 + (tip.y - center_y) ** 2)
            distances.append(distance)

        return sum(distances) / len(distances)

    def is_fist_based_on_distance(self, avg_distance, threshold=0.1):
        """
        Sprawdza, czy średnia odległość wskazuje na zaciśniętą pięść.
        """
        return avg_distance < threshold

    def process_frame(self, frame):
        """
        Przetwarza pojedynczą klatkę obrazu i aktualizuje dane gestów.
        """
        if not self.active or not self.reading_enabled or not self.hands:
            return

        # Konwersja obrazu na RGB
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image.flags.writeable = False

        # Wykrywanie dłoni
        results = self.hands.process(image)
        image.flags.writeable = True

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Obliczanie środka dłoni
                self.palm_center = self.get_palm_center(hand_landmarks.landmark)

                # Obliczanie średniej odległości
                self.avg_distance = self.calculate_average_distance(hand_landmarks.landmark, self.palm_center)

                # Sprawdzenie, czy dłoń to pięść
                self.is_fist = self.is_fist_based_on_distance(self.avg_distance)

    def get_palm_coordinates_percentage(self, frame_width, frame_height):
        """
        Zwraca współrzędne środka dłoni w procentach (szerokość, wysokość).
        """
        center_x, center_y = self.palm_center
        return center_x * 100, center_y * 100

    def get_fist_status(self):
        """
        Zwraca informację, czy dłoń jest zaciśnięta w pięść.
        """
        return self.is_fist
