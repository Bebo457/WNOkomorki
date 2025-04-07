--------------PUNKTACJA ZA PROJEKT---------------
1. Implementacja sceny gry (1pkt)
2. Komórki jako osobne obiekty (1pkt)
3. Interaktywność komórek – klikalność, przeciąganie, menu kontekstowe (3pkt)
4. Sterowanie jednostkami – wybór z menu i ruch na siatce planszy (2 pkt)
5. System walki uwzględniający poziomy komórek, specjalne efekty bitewne (3 pkt?) - nie zaimplementowałem mnożenia jednostek, więc nie wiem ile Pan policzy mi punktów
6. Mechanizm tur i licznik czasu na wykonanie ruchu (zegar rundowy) (2 pkt)
7. Sterowanie jednostkami za pomocą gestów z kamery (kliknięcie ruchem dłoni) (2 pkt)

Sumarycznie (celowane): 14 pkt


--------PROJEKT WOJNA EKSPANSJI----------

Przy odpaleniu gry, powinnno pojawić się okno z menu głównym gry, z trzema opcjami:
1. Tryb klasyczny
2. Tryb turowy
3. Wyjście

Cały sens i działanie gry znajduje się w punkcie "Tryb turowy". Tryb klasyczny miał odwzorować oryginalne działanie gry,
jendak ten tryb aktualnie nie działa.

Po kliknięciu w tryb turowy pokazuje nam się okno gry w fazie wstępnej.

FAZA WSTĘPNA:

W tej fazie gracze najpierw niebieski, potem czerwony rozstawiają swoje komórki. Aktualnie można postawić jeden typ komórki (maksymalnie 5).
Należy kliknąć po prawej w guzik "sklep". Kliknięcie na "Zwykła" sprawi że wokół kursora na mapie walki pojawi się kółko oznaczające położenie komórki.
Każdy gracz ma swoją własną strefę do stawiania komórek (oznaczone odpowiednio kolorami). Anulować stawianie można klikając prawy przycisk myszy.

Po tym jak pierwszy gracz rozstawił swoje komórki, naciska przycisk "ODDAJ TURE", co spowoduje przekazanie kolejki graczowi czerwonemu, którego teraz jest kolej na 
rozstawienie swoich komórek. Po tym jak gracz czerwony odda turę graczowi niebieskiemu zacznie się faktyczna gra z aktywnym zegarem.

FAZA TURY:

W tej fazie, menu ze sklepem zniknie i gracze grają z komórkami jakimi mają. Gracze podczas swoich tur mogą:
1. Oznaczać budowanie połączeń między innymi komórkami, zarówno wrogimi jak i nie. W tym celu klikammy najpierw na komórkę z której ma wychodzić połączenie, a następnie na komórkę do której połączenie ma prowadzić. Połączenie anulujemy klikając prawy przycisk myszki.
2. Usuwać połączenia, zrówno istniejące jak i zaplanowane. W tym celu należy kliknąć lewym przyciskiem myszki w dowolnym miejscu, niezajmowanym przez komórkę. Spowoduje to 
 pokazanie się białej linii, która po przecięciu z połączeniem istniejącym lub zaplanowanym, spowoduje jego usunięcie lub oznaczanie do usunięcia (w przypadku istniejących mostów). W celu domknięcie linii, należy drugi raz kliknąć w inne miejsce wolne od komórki.
3. Otworzyć menu kontekstowe danej komórki. W tym celu należy na komórce kliknąć prawym przyciskiem myszki. Menu kontekstowe pojawi się po prawej stronie. W menu tym widzimy infomację o danej komórce oraz przycisk "Ruch". Anulujemy menu kontestowe klikając prawym przyciskiem myszki w obszar wolny od komórek.
4. Zaplanować ruch jednostki. Należy w tym celu kliknąć "Ruch" z menu kontekstowego. Wówczas wokół komórki pojawi się szary obszar. Kliknięcie lewym przyciskiem myszki w ten obszar utworzy plan ruchu tej komórki w postaci czarnej kreski. Szary obszar znika przy otworzeniu menu kontekstowego innej komórki. UWAGA! ABY RUSZYĆ KOMÓRKĄ, 
 NIE MOŻE ONA MIEĆ ŻADNYCH POŁĄCZEŃ, ANI AKTYWNYCH ANI ZAPLANOWANYCH.
5. Ruch jednostek można wykonać poprzez gesty z kamery. W tym celu należy w panelu bocznym kliknąć "Sterowanie gestem". Funkcja ta włączy kamerę (jeżeli taką posiadamy i jest dostępna). Wówczas na ekranie walki pojawi się specjalny kursor. Ruszając ręką możemy sterować kursorem.
Aby ruszyć zaplanować ruch komórki należy najechać na nią kursorem a następnie zamknąć rękę (w pięść albo jakbyśmy coś łapali) a następnie przeciągnąć ją. Wówczas powinna pokazać się kreska zaplanowania ruchu komórki.

Po rozplanowaniu swoich zamiarów gracz, powinien oddać turę, wówczas gra przejdzie do następnej fazy:

FAZA PRZEJŚCIOWA:

W tej fazie gra wykonuje wszystkie zaplanowane akcje:
1. Wszystkie komórki zwiększają swoją siłę w zależności od swojego poziomu.
2. Wszystkie komórki z zaplanowanym ruchem wykonują ruch.
3. Na wszystkich połączeniach generują się podróżujące do innych komórek jednostki, które zwiększają lub zmniejszają siłę innych komórek.
4. Wszystkie zaplanowane do zbudowania połączenia budują się.
5. Wszystkie zaplanowane do zburzenia połączenia burzą się.

ZAKOŃCZENIE GRY

Gra się kończy kiedy:
1. Któryś z graczy przejmie wszystkie komórki przeciwnika.
2. Któremuś z graczy skończy się czas na zegarze, co oznacza automatyczną porażkę.

------------------------

ZADANIE NUMER 6

Zadanie zrealizowałem na 5 punktów:
1. W menu głównym widać przyciski odpowiedzialne za różne tryby gry.
2. Są też miejsca do wprowadzania i zapisywania adresu IP, maski podsieci oraz portu, wraz z walidacją poprawności wprowadzanych danych.
3. Zaimplementowałem, zapis i odczyt danych do plików XML, do bazy danych FireBase oraz plików JSON. Można zapisywać lub wczytywać grę z poziomu menu głównego bądź samej gry.
4. Zaimplementowałem możliwość odtwarzania historii rozgrywki. Nagrywana może być gra dla dwóch graczy, aby umożliwić nagrywanie, należy włączyć tą opcję w menu głównym.



