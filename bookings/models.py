from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class Restaurant(models.Model):
    """Restauracja dostępna do rezerwacji na uroczystości."""

    name = models.CharField("Nazwa", max_length=200)
    description = models.TextField("Opis", blank=True)
    address = models.CharField("Adres", max_length=300)
    city = models.CharField("Miasto", max_length=100)
    phone = models.CharField("Telefon", max_length=20)
    email = models.EmailField("E-mail", blank=True)
    website = models.URLField("Strona WWW", blank=True)
    image = models.ImageField("Zdjęcie", upload_to="restaurants/", blank=True, null=True)
    image_url = models.URLField("Link do zdjęcia", blank=True, help_text="Alternatywa dla przesłanego pliku")
    max_guests = models.PositiveIntegerField("Maks. liczba gości", default=100)
    price_per_person = models.DecimalField(
        "Cena za osobę (PLN)", max_digits=8, decimal_places=2, default=0
    )
    has_parking = models.BooleanField("Parking", default=False)
    has_garden = models.BooleanField("Ogród / teren zewnętrzny", default=False)
    has_dance_floor = models.BooleanField("Parkiet taneczny", default=False)
    has_accommodation = models.BooleanField("Noclegi", default=False)
    latitude = models.DecimalField(
        "Szerokość geogr.", max_digits=9, decimal_places=6, null=True, blank=True
    )
    longitude = models.DecimalField(
        "Długość geogr.", max_digits=9, decimal_places=6, null=True, blank=True
    )
    is_active = models.BooleanField("Aktywna", default=True)
    created_at = models.DateTimeField("Data utworzenia", auto_now_add=True)
    updated_at = models.DateTimeField("Data aktualizacji", auto_now=True)

    class Meta:
        verbose_name = "Restauracja"
        verbose_name_plural = "Restauracje"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} — {self.city}"

    def average_rating(self):
        reviews = self.reviews.all()
        if reviews.exists():
            return round(reviews.aggregate(models.Avg("rating"))["rating__avg"], 1)
        return None

    def get_image_url(self):
        """Return image URL - either uploaded file or external URL."""
        if self.image:
            return self.image.url
        return self.image_url


class EventType(models.TextChoices):
    """Typy uroczystości."""

    WEDDING = "wedding", "Wesele"
    BAPTISM = "baptism", "Chrzciny"
    COMMUNION = "communion", "Komunia Święta"


class Booking(models.Model):
    """Rezerwacja restauracji na uroczystość."""

    class Status(models.TextChoices):
        PENDING = "pending", "Oczekująca"
        CONFIRMED = "confirmed", "Potwierdzona"
        CANCELLED = "cancelled", "Anulowana"
        COMPLETED = "completed", "Zakończona"

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="bookings",
        verbose_name="Użytkownik",
    )
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name="bookings",
        verbose_name="Restauracja",
    )
    event_type = models.CharField(
        "Typ uroczystości",
        max_length=20,
        choices=EventType.choices,
    )
    event_date = models.DateField("Data uroczystości")
    guest_count = models.PositiveIntegerField("Liczba gości", validators=[MinValueValidator(1)])
    status = models.CharField(
        "Status",
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    first_name = models.CharField("Imię", max_length=100)
    last_name = models.CharField("Nazwisko", max_length=100)
    phone = models.CharField("Telefon kontaktowy", max_length=20)
    email = models.EmailField("E-mail kontaktowy")
    notes = models.TextField("Dodatkowe uwagi", blank=True)
    created_at = models.DateTimeField("Data utworzenia", auto_now_add=True)
    updated_at = models.DateTimeField("Data aktualizacji", auto_now=True)

    class Meta:
        verbose_name = "Rezerwacja"
        verbose_name_plural = "Rezerwacje"
        ordering = ["-event_date"]
        constraints = [
            models.UniqueConstraint(
                fields=["restaurant", "event_date"],
                name="unique_restaurant_date",
            )
        ]

    def __str__(self):
        return (
            f"{self.get_event_type_display()} — {self.restaurant.name} "
            f"({self.event_date:%d.%m.%Y})"
        )

    @property
    def total_cost(self):
        return self.guest_count * self.restaurant.price_per_person


class Review(models.Model):
    """Opinia o restauracji."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="reviews",
        verbose_name="Użytkownik",
    )
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name="reviews",
        verbose_name="Restauracja",
    )
    rating = models.PositiveIntegerField(
        "Ocena",
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    comment = models.TextField("Komentarz", blank=True)
    created_at = models.DateTimeField("Data dodania", auto_now_add=True)

    class Meta:
        verbose_name = "Opinia"
        verbose_name_plural = "Opinie"
        ordering = ["-created_at"]
        unique_together = ["user", "restaurant"]

    def __str__(self):
        return f"{self.user.username} → {self.restaurant.name} ({self.rating}/5)"


class RestaurantOwner(models.Model):
    """Właściciel restauracji."""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="restaurant_owner",
        verbose_name="Użytkownik",
    )
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name="owners",
        verbose_name="Restauracja",
        null=True,
        blank=True,
    )
    is_main_owner = models.BooleanField("Główny właściciel", default=True)
    created_at = models.DateTimeField("Data dodania", auto_now_add=True)

    class Meta:
        verbose_name = "Właściciel restauracji"
        verbose_name_plural = "Właściciele restauracji"
        unique_together = ["user", "restaurant"]

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} → {self.restaurant.name}"


class BookingNote(models.Model):
    """Notatka CRM do rezerwacji — historia kontaktów z klientem."""

    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name="crm_notes",
        verbose_name="Rezerwacja",
    )
    author = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Autor",
    )
    date = models.DateField("Data kontaktu")
    title = models.CharField("Temat / nazwa", max_length=200)
    content = models.TextField("Treść notatki")
    created_at = models.DateTimeField("Utworzono", auto_now_add=True)

    class Meta:
        verbose_name = "Notatka CRM"
        verbose_name_plural = "Notatki CRM"
        ordering = ["-date", "-created_at"]

    def __str__(self):
        return f"{self.date} — {self.title}"


class MenuItem(models.Model):
    """Pozycja menu restauracji."""

    class Category(models.TextChoices):
        APPETIZER = "appetizer", "Przystawki"
        SOUP = "soup", "Zupy"
        MAIN = "main", "Główne danie"
        DESSERT = "dessert", "Deser"
        BUFFET = "buffet", "Bufet"
        DRINK = "drink", "Napoje"

    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name="menu_items",
        verbose_name="Restauracja",
    )
    category = models.CharField(
        "Kategoria", max_length=20, choices=Category.choices
    )
    name = models.CharField("Nazwa", max_length=200)
    description = models.TextField("Opis", blank=True)
    price = models.DecimalField(
        "Cena (zł)", max_digits=8, decimal_places=2, default=0
    )
    is_visible = models.BooleanField("Pokaż na głównej stronie", default=True)
    order = models.PositiveIntegerField("Kolejność", default=0)
    created_at = models.DateTimeField("Utworzono", auto_now_add=True)

    class Meta:
        verbose_name = "Pozycja menu"
        verbose_name_plural = "Pozycje menu"
        ordering = ["category", "order", "name"]

    def __str__(self):
        return f"{self.get_category_display()}: {self.name} ({self.price} zł)"


class BookingMenuItem(models.Model):
    """Wybór pozycji menu przez klienta przy rezerwacji."""

    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name="menu_selections",
        verbose_name="Rezerwacja",
    )
    menu_item = models.ForeignKey(
        MenuItem,
        on_delete=models.CASCADE,
        related_name="booking_selections",
        verbose_name="Pozycja menu",
    )
    quantity = models.PositiveIntegerField("Ilość", default=1)

    class Meta:
        verbose_name = "Wybór menu"
        verbose_name_plural = "Wybory menu"
        unique_together = ["booking", "menu_item"]

    def __str__(self):
        return f"{self.menu_item.name} x{self.quantity}"

    @property
    def subtotal(self):
        return self.menu_item.price * self.quantity
