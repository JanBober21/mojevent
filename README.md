# EventBook — Rezerwacja Restauracji na Uroczystości

Aplikacja Django do rezerwacji restauracji na **chrzciny**, **wesela** i **komunie święte**.

## Funkcjonalności

- **Przeglądanie restauracji** — lista z filtrami (miasto, cena, pojemność, udogodnienia)
- **Szczegóły restauracji** — opis, udogodnienia, opinie, oceny
- **Rezerwacja online** — formularz z wyborem typu uroczystości i daty
- **Panel użytkownika** — lista rezerwacji, anulowanie, statusy
- **System opinii** — ocena i komentarze do restauracji
- **Rejestracja i logowanie** — pełna autoryzacja użytkowników
- **Panel admina** — zarządzanie restauracjami, rezerwacjami i opiniami

## Wymagania

- Python 3.10+
- Django 5.0+

## Instalacja i uruchomienie

```bash
# 1. Sklonuj repozytorium lub przejdź do katalogu projektu
cd restaurant_booking

# 2. Utwórz i aktywuj wirtualne środowisko
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac

# 3. Zainstaluj zależności
pip install -r requirements.txt

# 4. Wykonaj migracje bazy danych
python manage.py makemigrations
python manage.py migrate

# 5. Utwórz konto administratora
python manage.py createsuperuser

# 6. (Opcjonalnie) Załaduj przykładowe dane
python manage.py loaddata sample_data.json

# 7. Uruchom serwer
python manage.py runserver
```

Aplikacja będzie dostępna pod adresem: http://127.0.0.1:8000/

Panel admina: http://127.0.0.1:8000/admin/

## Struktura projektu

```
restaurant_booking/
├── config/                  # Konfiguracja Django
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── bookings/                # Główna aplikacja
│   ├── models.py            # Modele: Restaurant, Booking, Review
│   ├── views.py             # Widoki
│   ├── forms.py             # Formularze
│   ├── admin.py             # Konfiguracja panelu admina
│   └── urls.py              # Routing URL
├── templates/               # Szablony HTML
│   ├── base.html
│   └── bookings/
├── static/css/              # Style CSS
├── manage.py
├── requirements.txt
└── README.md
```

## Modele danych

- **Restaurant** — restauracja (nazwa, adres, pojemność, cena, udogodnienia)
- **Booking** — rezerwacja (użytkownik, restauracja, typ uroczystości, data, goście, status)
- **Review** — opinia (użytkownik, restauracja, ocena 1-5, komentarz)

## Typy uroczystości

| Typ | Opis |
|-----|------|
| Wesele | Przyjęcie weselne z parkietem i noclegami |
| Chrzciny | Kameralne spotkanie rodzinne po chrzcie |
| Komunia Święta | Przyjęcie komunijne z ogrodem |
