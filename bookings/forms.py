from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.utils import timezone

from .models import Booking, Review, Restaurant, BookingNote, EventType


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
            "guest_count",
            "first_name",
            "last_name",
            "phone",
            "email",
            "notes",
        ]
        widgets = {
            "event_type": forms.Select(attrs={"class": "form-select"}),
            "guest_count": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }

    def clean_event_date(self):
        date = self.cleaned_data["event_date"]
        if date <= timezone.now().date():
            raise forms.ValidationError("Data uroczystości musi być w przyszłości.")
        return date

    def clean_guest_count(self):
        count = self.cleaned_data["guest_count"]
        if count < 1:
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

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "password1", "password2"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update({"class": "form-control"})
        self.fields["password1"].widget.attrs.update({"class": "form-control"})
        self.fields["password2"].widget.attrs.update({"class": "form-control"})


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
            "has_parking": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "has_garden": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "has_dance_floor": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "has_accommodation": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "latitude": forms.HiddenInput(attrs={"id": "id_latitude"}),
            "longitude": forms.HiddenInput(attrs={"id": "id_longitude"}),
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
        # Normalize: remove °, N/S/E/W suffixes, extra spaces
        import re
        raw = raw.replace("°", "").strip()
        # Try "lat, lng" or "lat lng" (decimal)
        m = re.match(r'^([+-]?\d+[.,]\d+)[,;\s]+([+-]?\d+[.,]\d+)$', raw)
        if m:
            return f"{m.group(1).replace(',', '.')}, {m.group(2).replace(',', '.')}"
        raise forms.ValidationError("Nieprawidłowy format. Wklej współrzędne np. 52.2297, 21.0122")

    def clean(self):
        cleaned = super().clean()
        coords = cleaned.get("coords", "")
        if coords:
            parts = coords.split(",")
            cleaned["latitude"] = round(float(parts[0].strip()), 6)
            cleaned["longitude"] = round(float(parts[1].strip()), 6)
        else:
            # Keep existing or clear
            if not cleaned.get("latitude"):
                cleaned["latitude"] = None
            if not cleaned.get("longitude"):
                cleaned["longitude"] = None
        return cleaned
