# MojEvent — Dokumentacja

## Opis projektu

**MojEvent** to aplikacja webowa do rezerwacji firm eventowych na polskim rynku.  
Obsługuje trzy kategorie: **Imprezy w lokalu**, **Catering z dowozem** i **Atrakcje** (fotograf, fotobudka, ścianki, animacje).

Właściciele firm mogą zarządzać rezerwacjami, klientami, menu, ofertą atrakcji, prowadzić czat z klientem i zamykać deale z generowaniem umowy do druku.

### Stack technologiczny

| Warstwa       | Technologia                                |
|---------------|--------------------------------------------|
| Backend       | Django 5.2, Python 3.14                    |
| Frontend      | Bootstrap 5, Bootstrap Icons, Leaflet.js   |
| Baza danych   | PostgreSQL (prod) / SQLite (dev)           |
| Autoryzacja   | django-allauth (Google OAuth)              |
| Hosting       | Heroku (Gunicorn + WhiteNoise)             |
| Repo          | github.com/JanBober21/mojevent             |

---

## Główne funkcjonalności

- **Wyszukiwanie firm** — po kategorii, mieście, filtrach; catering z filtrem po GPS (Haversine)
- **Mapa** — Leaflet + OpenStreetMap z pinami firm, Nominatim geocoding
- **Rezerwacja** — formularz dla klienta, wybór menu, czat z firmą
- **Panel właściciela** — dashboard ze statystykami, kalendarz, lista rezerwacji, CRM, menu, atrakcje
- **Zamykanie dealu** — ustalenie kwoty i warunków, generowanie drukowanej umowy
- **Google Calendar** — link do dodania wydarzenia
- **Opinie** — oceny 1–5 z komentarzem
- **Admin** — panel Django z CSV export

---

## Schemat bazy danych

```
┌─────────────────────────────────┐
│           Restaurant            │
├─────────────────────────────────┤
│ id              PK              │
│ firm_type       varchar(20)     │  venue / catering / attraction
│ attraction_type varchar(20)     │  photographer / photobooth / photo_wall / animations
│ delivery_radius_km  int         │
│ name            varchar(200)    │
│ description     text            │
│ address         varchar(300)    │
│ city            varchar(100)    │
│ phone           varchar(20)     │
│ email           email           │
│ website         url             │
│ image           file            │
│ image_url       url             │
│ max_guests      int             │
│ price_per_person decimal(8,2)   │
│ has_parking      bool           │
│ has_garden       bool           │
│ has_dance_floor  bool           │
│ has_accommodation bool          │
│ latitude        decimal(9,6)    │
│ longitude       decimal(9,6)    │
│ is_active       bool            │
│ created_at      datetime        │
│ updated_at      datetime        │
└─────────────────────────────────┘
         │ 1
         │
         ├──────< RestaurantOwner (user FK → User, restaurant FK)
         │
         ├──────< MenuItem
         │        │ id, category, name, description, price, is_visible, order
         │        │
         │        └──────< BookingMenuItem (menu_item FK, booking FK, quantity)
         │
         ├──────< AttractionItem
         │        │ id, name, description, image_url, price, tag, is_active, order
         │
         ├──────< Booking
         │        │ id, user FK → User, restaurant FK
         │        │ event_type, event_date, guest_count
         │        │ status (pending / confirmed / cancelled / completed)
         │        │ first_name, last_name, phone, email, notes
         │        │ deal_closed_at, deal_agreed_price decimal(10,2), deal_terms
         │        │ created_at, updated_at
         │        │ UNIQUE(restaurant, event_date)
         │        │
         │        ├──────< BookingNote (CRM)
         │        │        │ id, booking FK, author FK → User
         │        │        │ date, title, content
         │        │
         │        ├──────< BookingMessage (czat)
         │        │        │ id, booking FK, sender FK → User
         │        │        │ content, created_at
         │        │
         │        └──────< BookingMenuItem
         │                 │ booking FK, menu_item FK, quantity
         │                 │ UNIQUE(booking, menu_item)
         │
         └──────< Review
                  │ id, user FK → User, restaurant FK
                  │ rating (1-5), comment
                  │ UNIQUE(user, restaurant)


┌──────────────────┐
│   User (auth)    │
├──────────────────┤
│ id, username,    │
│ email, password  │
│ first_name,      │
│ last_name        │
└──────────────────┘
  │ 1
  ├──< RestaurantOwner
  ├──< Booking
  ├──< Review
  ├──< BookingNote (author)
  └──< BookingMessage (sender)
```

---

## Endpointy (urls.py)

| URL                                     | Widok                      | Opis                              |
|-----------------------------------------|----------------------------|-----------------------------------|
| `/`                                     | `home`                     | Strona główna z mapą              |
| `/restauracje/`                         | `restaurant_list`          | Lista firm z filtrami             |
| `/restauracje/<id>/`                    | `restaurant_detail`        | Profil firmy, menu, opinie        |
| `/restauracje/<id>/rezerwuj/`           | `booking_create`           | Formularz rezerwacji              |
| `/restauracje/<id>/opinia/`             | `review_create`            | Dodaj opinię                      |
| `/rezerwacje/`                          | `booking_list`             | Moje rezerwacje (klient)          |
| `/rezerwacje/<id>/`                     | `booking_detail`           | Szczegóły rezerwacji + czat       |
| `/rezerwacje/<id>/anuluj/`              | `booking_cancel`           | Anuluj rezerwację                 |
| `/rezerwacje/<id>/menu/`                | `booking_menu_select`      | Wybór menu do rezerwacji          |
| `/owner/`                               | `owner_dashboard`          | Dashboard właściciela             |
| `/owner/bookings/`                      | `owner_bookings`           | Lista rezerwacji (właściciel)     |
| `/owner/booking/<id>/`                  | `owner_booking_detail`     | Szczegóły + czat + CRM + deal     |
| `/owner/booking/<id>/umowa/`            | `owner_booking_agreement`  | Drukowana umowa                   |
| `/owner/calendar/`                      | `owner_calendar`           | Kalendarz rezerwacji              |
| `/owner/restauracja/dodaj/`             | `owner_restaurant_create`  | Dodaj firmę                       |
| `/owner/restauracja/edytuj/`            | `owner_restaurant_edit`    | Edytuj firmę                      |
| `/owner/menu/`                          | `owner_menu`               | Zarządzanie menu                  |
| `/owner/atrakcje/`                      | `owner_attractions`        | Zarządzanie ofertą atrakcji       |
| `/rejestracja/`                         | `register`                 | Rejestracja klienta               |
| `/rejestracja/restauracja/`             | `owner_register`           | Rejestracja właściciela           |
| `/logowanie/`                           | `LoginView`                | Logowanie                         |
| `/wyloguj/`                             | `LogoutView`               | Wylogowanie                       |

---

## Typy uroczystości (EventType)

| Klucz           | Etykieta              |
|-----------------|-----------------------|
| wedding         | Wesele                |
| baptism         | Chrzciny              |
| communion       | Komunia Święta        |
| birthday        | Urodziny              |
| integration     | Impreza integracyjna  |
| corporate_xmas  | Wigilia firmowa       |
| catering        | Catering              |
| other           | Inne                  |

## Statusy rezerwacji

| Klucz      | Etykieta      | Opis                        |
|------------|---------------|-----------------------------|
| pending    | Oczekująca    | Nowa, czeka na potwierdzenie|
| confirmed  | Potwierdzona  | Zaakceptowana przez firmę   |
| cancelled  | Anulowana     | Odrzucona lub anulowana     |
| completed  | Zakończona    | Po wydarzeniu               |

---

## Uruchomienie lokalne

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Domyślnie działa na `http://127.0.0.1:8000/` z SQLite.
