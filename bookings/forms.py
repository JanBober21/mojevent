from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.utils import timezone

from .models import Booking, Review


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
    """Formularz wyszukiwania restauracji."""

    EVENT_CHOICES = [("", "Wszystkie")] + [
        ("wedding", "Wesele"),
        ("christening", "Chrzciny"),
        ("communion", "Komunia Święta"),
    ]

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
