## Zadania

- [x] **1. Nowy model `Czytelnik`** *(2 pkt)*
  - imię, nazwisko, e-mail (unikalny), numer karty bibliotecznej (unikalny)
  - pełny CRUD na stronie oraz rejestracja w panelu admina

- [x] **2. Nowy model `Wypozyczenie`** *(1 pkt)*
  - książka (`ForeignKey` do `Ksiazka`), czytelnik (`ForeignKey` do `Czytelnik`)
  - data wypożyczenia, termin zwrotu (domyślnie 30 dni)
  - data zwrotu (pusta, dopóki książka nie wróci)

- [x] **3. Kolumna „Dostępne” na liście książek** *(1 pkt)*
  - liczba egzemplarzy minus liczba aktywnych wypożyczeń
  - przycisk „Wypożycz” jest nieaktywny, gdy dostępnych jest 0

- [x] **4. Walidacja formularza wypożyczenia** *(1 pkt)*
  - odrzuca wypożyczenie książki bez wolnych egzemplarzy i pokazuje czytelny błąd

- [x] **5. Strona „Wypożyczenia”** *(1 pkt)*
  - tabela aktywnych wypożyczeń z przyciskiem „Zwróć” (metodą `POST`)
  - wiersze po terminie zwrotu są podświetlone na czerwono (`table-danger`)

## Wymagania dodatkowe

- [x] **6. Paginacja listy książek** *(1 pkt)*
  - po 10 pozycji na stronę, z komponentem `pagination` z Bootstrapa

- [x] **7. Sortowanie tabeli** *(1 pkt)*
  - sortowanie po kliknięciu nagłówka kolumny (tytuł, autor, rok)

- [x] **8. Strona szczegółów czytelnika** *(1 pkt)*
  - historia wypożyczeń danego czytelnika

- [x] **9. Wypożyczenia inline w panelu admina** *(1 pkt)*
  - wypożyczenia widoczne na stronie książki jako `TabularInline`
