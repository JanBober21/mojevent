# 🚀 INSTRUKCJE DEPLOYMENT NA HEROKU

## 1. Zaloguj się do Heroku
```bash
heroku login
```

## 2. Utwórz aplikację Heroku (jeśli jeszcze nie istnieje)
```bash
heroku create mojevent51  # lub inna nazwa jeśli zajęta
```

## 3. Skonfiguruj zmienne środowiskowe
```bash
heroku config:set DJANGO_SETTINGS_MODULE=config.settings.production
heroku config:set SECRET_KEY="8w(7tx4@fg47zj6w-&x)hg__l+z-uu63av7zdbyh#j=x!rsi+z"
heroku config:set DEBUG=False
```

## 4. Dodaj PostgreSQL addon
```bash
heroku addons:create heroku-postgresql:mini
```

## 5. Połącz z repozytorium
```bash
heroku git:remote -a mojevent51  # użyj nazwy swojej aplikacji
```

## 6. Deploy kod
```bash
git push heroku main
```

## 7. Uruchom migracje
```bash
heroku run python manage.py migrate
```

## 8. Załaduj przykładowe dane
```bash
heroku run python manage.py loaddata bookings/fixtures/sample_data.json
```

## 9. Utwórz superusera na Heroku
```bash
heroku run python manage.py createsuperuser
```

## 10. Sprawdź logi w przypadku problemów
```bash
heroku logs --tail
```

## 📱 Gotowe! 
Aplikacja będzie dostępna pod: https://mojevent51.herokuapp.com
Admin panel: https://mojevent51.herokuapp.com/admin/

---

## 🛠️ AKTUALNA SYTUACJA:
✅ Kod wysłany na GitHub (wszystkie poprawki kalendarza)
⏳ Oczekuje na instalację Heroku CLI i deployment

## 🐛 NAPRAWIONE PROBLEMY:
✅ Fix EventType: baptism zamiast christening  
✅ Uproszczona struktura JSON kalendarza
✅ Dodany HTML fallback dla listy rezerwacji
✅ Debug i error handling dla kalendarza
✅ Try-catch dla inicjalizacji JavaScript
✅ Przekazywanie danych bookings do template