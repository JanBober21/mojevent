# Deployment na Heroku 🚀

## Wymagania
- Konto na [Heroku](https://signup.heroku.com/)
- [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli) zainstalowane

## 1. Logowanie do Heroku
```bash
heroku login
```

## 2. Tworzenie aplikacji
```bash
heroku create your-app-name
# Lub bez nazwy dla losowej:
heroku create
```

## 3. Ustawianie zmiennych środowiskowych
```bash
# Generuj SECRET_KEY w Pythonie:
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Ustaw zmienne:
heroku config:set SECRET_KEY="your-generated-secret-key"
heroku config:set DJANGO_SETTINGS_MODULE="config.settings.production"
```

## 4. Dodanie PostgreSQL (baza danych)
```bash
heroku addons:create heroku-postgresql:essential-0
```

## 5. Deploy
```bash
git push heroku main
```

## 6. Migracje i superuser
```bash
heroku run python manage.py migrate
heroku run python manage.py createsuperuser
heroku run python manage.py loaddata sample_data
```

## 7. Otwieranie aplikacji
```bash
heroku open
```

## Monitoring
- Logi: `heroku logs --tail`
- Status: `heroku ps`
- Konfiguracja: `heroku config`

## URL aplikacji
Twoja aplikacja będzie dostępna pod: `https://your-app-name.herokuapp.com`

Admin panel: `https://your-app-name.herokuapp.com/admin/