from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.utils import timezone

from .models import Booking, Review, Restaurant, BookingNote, EventType, UserProfile


class BookingForm(forms.ModelForm):
    """Formularz tworzenia rezerwacji."""

    event_date = forms.DateField(
        label="Data uroczystości",
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
    )

    class Meta:
        model = Booking
        fields = [
            "event_type",
            "event_date",
            "event_start_time",
            "event_end_time",
            "guest_count",
            "first_name",
            "last_name",
            "phone",
            "email",
            "notes",
        ]
        widgets = {
            "event_type": forms.Select(attrs={"class": "form-select"}),
            "event_start_time": forms.TimeInput(attrs={"class": "form-control", "type": "time"}),
            "event_end_time": forms.TimeInput(attrs={"class": "form-control", "type": "time"}),
            "guest_count": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }

    def __init__(self, *args, firm_type=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.firm_type = firm_type
        if firm_type == "attraction":
            del self.fields["event_type"]
            del self.fields["guest_count"]
        # Domyślne godziny dla nowej rezerwacji
        if not self.instance.pk:
            if not self.initial.get("event_start_time"):
                self.initial["event_start_time"] = "17:00"
            if not self.initial.get("event_end_time"):
                self.initial["event_end_time"] = "20:00"

    def clean_event_date(self):
        date = self.cleaned_data["event_date"]
        if date <= timezone.now().date():
            raise forms.ValidationError("Data uroczystości musi być w przyszłości.")
        return date

    def clean_guest_count(self):
        count = self.cleaned_data.get("guest_count")
        if count is not None and count < 1:
            raise forms.ValidationError("Liczba gości musi wynosić co najmniej 1.")
        return count


class ReviewForm(forms.ModelForm):
    """Formularz dodawania opinii."""

    class Meta:
        model = Review
        fields = ["rating", "comment"]
        widgets = {
            "rating": forms.Select(
                choices=[(i, f"{i} ★") for i in range(1, 6)],
                attrs={"class": "form-select"},
            ),
            "comment": forms.Textarea(
                attrs={"class": "form-control", "rows": 3, "placeholder": "Twoja opinia..."}
            ),
        }


class UserRegisterForm(UserCreationForm):
    """Formularz rejestracji użytkownika."""

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={"class": "form-control"}),
    )
    first_name = forms.CharField(
        label="Imię",
        max_length=100,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    last_name = forms.CharField(
        label="Nazwisko",
        max_length=100,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    phone = forms.CharField(
        label="Telefon",
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "np. +48 123 456 789"}),
    )
    client_type = forms.ChoiceField(
        label="Typ klienta",
        choices=UserProfile.ClientType.choices,
        widget=forms.RadioSelect(attrs={"class": "form-check-input"}),
        initial="private",
    )
    company_name = forms.CharField(
        label="Nazwa firmy",
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "np. ABC Sp. z o.o."}),
    )
    company_address = forms.CharField(
        label="Adres firmy",
        max_length=300,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "ul. Przykładowa 1, 00-000 Warszawa"}),
    )
    company_nip = forms.CharField(
        label="NIP",
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "np. 1234567890"}),
    )

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "password1", "password2"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update({"class": "form-control"})
        self.fields["password1"].widget.attrs.update({"class": "form-control"})
        self.fields["password2"].widget.attrs.update({"class": "form-control"})

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("client_type") == "company":
            if not cleaned.get("company_name"):
                self.add_error("company_name", "Podaj nazwę firmy.")
            if not cleaned.get("company_nip"):
                self.add_error("company_nip", "Podaj NIP firmy.")
        return cleaned


class UserSettingsForm(forms.Form):
    """Formularz ustawień konta użytkownika."""

    first_name = forms.CharField(
        label="Imię",
        max_length=100,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    last_name = forms.CharField(
        label="Nazwisko",
        max_length=100,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    email = forms.EmailField(
        label="E-mail",
        widget=forms.EmailInput(attrs={"class": "form-control"}),
    )
    phone = forms.CharField(
        label="Telefon",
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "np. +48 123 456 789"}),
    )
    city = forms.ChoiceField(
        label="Miasto",
        choices=UserProfile.CITY_CHOICES,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    client_type = forms.ChoiceField(
        label="Typ klienta",
        choices=UserProfile.ClientType.choices,
        widget=forms.RadioSelect(attrs={"class": "form-check-input"}),
    )
    company_name = forms.CharField(
        label="Nazwa firmy",
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    company_address = forms.CharField(
        label="Adres firmy",
        max_length=300,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    company_nip = forms.CharField(
        label="NIP",
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("client_type") == "company":
            if not cleaned.get("company_name"):
                self.add_error("company_name", "Podaj nazwę firmy.")
            if not cleaned.get("company_nip"):
                self.add_error("company_nip", "Podaj NIP firmy.")
        return cleaned


class RestaurantSearchForm(forms.Form):
    """Formularz wyszukiwania firm."""

    FIRM_TYPE_CHOICES = [("", "Wszystkie")] + list(Restaurant.FirmType.choices)

    firm_type = forms.ChoiceField(
        label="Typ firmy",
        choices=FIRM_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    city = forms.CharField(
        label="Miasto",
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Miasto..."}),
    )
    event_date = forms.DateField(
        label="Data",
        required=False,
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
    )
    min_guests = forms.IntegerField(
        label="Min. gości",
        required=False,
        widget=forms.NumberInput(attrs={"class": "form-control", "placeholder": "Min. gości"}),
    )
    max_price = forms.DecimalField(
        label="Maks. cena/os.",
        required=False,
        widget=forms.NumberInput(
            attrs={"class": "form-control", "placeholder": "Maks. cena za osobę"}
        ),
    )
    min_price = forms.DecimalField(
        label="Cena od",
        required=False,
        widget=forms.NumberInput(
            attrs={"class": "form-control", "placeholder": "od", "min": 0, "step": "1"}
        ),
    )
    max_guests_filter = forms.IntegerField(
        label="Maks. gości",
        required=False,
        widget=forms.NumberInput(attrs={"class": "form-control", "placeholder": "Maks. gości"}),
    )
    has_parking = forms.BooleanField(
        label="Parking",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )
    has_garden = forms.BooleanField(
        label="Ogród",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )
    has_dance_floor = forms.BooleanField(
        label="Parkiet",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )
    has_accommodation = forms.BooleanField(
        label="Noclegi",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )
    min_rating = forms.ChoiceField(
        label="Min. ocena",
        required=False,
        choices=[("" , "Wszystkie")] + [(str(i), f"{i}+ ★") for i in range(1, 6)],
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    has_online_menu = forms.BooleanField(
        label="Menu dostępne online",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )
    # Pola lokalizacji dla cateringu (filtrowanie po promieniu)
    user_lat = forms.DecimalField(
        required=False,
        widget=forms.HiddenInput(attrs={"id": "user_lat"}),
    )
    user_lng = forms.DecimalField(
        required=False,
        widget=forms.HiddenInput(attrs={"id": "user_lng"}),
    )


class OwnerRegisterForm(UserCreationForm):
    """Formularz rejestracji właściciela restauracji."""

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={"class": "form-control"}),
    )
    first_name = forms.CharField(
        label="Imię",
        max_length=100,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    last_name = forms.CharField(
        label="Nazwisko",
        max_length=100,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    phone = forms.CharField(
        label="Telefon",
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "np. +48 123 456 789"}),
    )

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "password1", "password2"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update({"class": "form-control"})
        self.fields["password1"].widget.attrs.update({"class": "form-control"})
        self.fields["password2"].widget.attrs.update({"class": "form-control"})


class RestaurantForm(forms.ModelForm):
    """Formularz dodawania/edycji firmy."""

    coords = forms.CharField(
        required=False,
        label="Współrzędna GPS",
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "id": "id_coords",
            "placeholder": "np. 52.2297, 21.0122  (wklej z Google Maps)",
        }),
    )

    class Meta:
        model = Restaurant
        fields = [
            "firm_type", "attraction_type", "delivery_radius_km",
            "name", "description", "address", "city",
            "phone", "email", "website", "image_url",
            "max_guests", "price_per_person",
            "has_parking", "has_garden", "has_dance_floor", "has_accommodation",
            "latitude", "longitude",
            "welcome_message",
            "mon_open", "mon_close",
            "tue_open", "tue_close",
            "wed_open", "wed_close",
            "thu_open", "thu_close",
            "fri_open", "fri_close",
            "sat_open", "sat_close",
            "sun_open", "sun_close",
        ]
        widgets = {
            "firm_type": forms.Select(attrs={"class": "form-select", "id": "id_firm_type"}),
            "attraction_type": forms.Select(attrs={"class": "form-select"}),
            "delivery_radius_km": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "address": forms.TextInput(attrs={"class": "form-control", "id": "id_address"}),
            "city": forms.TextInput(attrs={"class": "form-control", "id": "id_city"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "website": forms.URLInput(attrs={"class": "form-control", "placeholder": "https://..."}),
            "image_url": forms.URLInput(attrs={"class": "form-control", "placeholder": "https://...link do zdjęcia"}),
            "max_guests": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
            "price_per_person": forms.NumberInput(attrs={"class": "form-control", "min": 0, "step": "0.01"}),
            "welcome_message": forms.Textarea(attrs={"class": "form-control", "rows": 5}),
            "has_parking": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "has_garden": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "has_dance_floor": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "has_accommodation": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "latitude": forms.HiddenInput(attrs={"id": "id_latitude"}),
            "longitude": forms.HiddenInput(attrs={"id": "id_longitude"}),
            "mon_open": forms.TimeInput(attrs={"class": "form-control", "type": "time"}),
            "mon_close": forms.TimeInput(attrs={"class": "form-control", "type": "time"}),
            "tue_open": forms.TimeInput(attrs={"class": "form-control", "type": "time"}),
            "tue_close": forms.TimeInput(attrs={"class": "form-control", "type": "time"}),
            "wed_open": forms.TimeInput(attrs={"class": "form-control", "type": "time"}),
            "wed_close": forms.TimeInput(attrs={"class": "form-control", "type": "time"}),
            "thu_open": forms.TimeInput(attrs={"class": "form-control", "type": "time"}),
            "thu_close": forms.TimeInput(attrs={"class": "form-control", "type": "time"}),
            "fri_open": forms.TimeInput(attrs={"class": "form-control", "type": "time"}),
            "fri_close": forms.TimeInput(attrs={"class": "form-control", "type": "time"}),
            "sat_open": forms.TimeInput(attrs={"class": "form-control", "type": "time"}),
            "sat_close": forms.TimeInput(attrs={"class": "form-control", "type": "time"}),
            "sun_open": forms.TimeInput(attrs={"class": "form-control", "type": "time"}),
            "sun_close": forms.TimeInput(attrs={"class": "form-control", "type": "time"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pre-populate coords from existing lat/lng
        if self.instance and self.instance.pk:
            lat = self.instance.latitude
            lng = self.instance.longitude
            if lat and lng:
                self.fields["coords"].initial = f"{lat}, {lng}"

    def clean_coords(self):
        raw = self.cleaned_data.get("coords", "").strip()
        if not raw:
            return ""
        import re
        from decimal import Decimal, ROUND_HALF_UP
        raw = raw.replace("°", "").strip()
        # Match "lat, lng" or "lat lng" — with or without decimal part
        m = re.match(r'^([+-]?\d+(?:[.,]\d+)?)[,;\s]+([+-]?\d+(?:[.,]\d+)?)$', raw)
        if not m:
            raise forms.ValidationError("Nieprawidłowy format. Wklej współrzędne np. 52.2297, 21.0122")
        lat = Decimal(m.group(1).replace(",", ".")).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)
        lng = Decimal(m.group(2).replace(",", ".")).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)
        return f"{lat}, {lng}"

    def clean(self):
        cleaned = super().clean()
        coords = cleaned.get("coords", "")
        if coords:
            from decimal import Decimal
            parts = coords.split(",")
            cleaned["latitude"] = Decimal(parts[0].strip())
            cleaned["longitude"] = Decimal(parts[1].strip())
        else:
            if not cleaned.get("latitude"):
                cleaned["latitude"] = None
            if not cleaned.get("longitude"):
                cleaned["longitude"] = None
        return cleaned
