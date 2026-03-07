from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class Restaurant(models.Model):
    """Firma — lokal na imprezy, catering lub atrakcje."""

    class FirmType(models.TextChoices):
        VENUE = "venue", "Imprezy w lokalu"
        CATERING = "catering", "Catering z dowozem"
        ATTRACTION = "attraction", "Atrakcje"

    class AttractionType(models.TextChoices):
        PHOTOGRAPHER = "photographer", "Fotograf / Wideo"
        PHOTOBOOTH = "photobooth", "Fotobudka"
        PHOTO_WALL = "photo_wall", "Ścianki do zdjęć"
        ANIMATIONS = "animations", "Animacje"

    firm_type = models.CharField(
        "Typ firmy", max_length=20,
        choices=FirmType.choices, default=FirmType.VENUE,
    )
    attraction_type = models.CharField(
        "Rodzaj atrakcji", max_length=20,
        choices=AttractionType.choices, blank=True,
        help_text="Wypełnij tylko dla typu Atrakcje",
    )
    delivery_radius_km = models.PositiveIntegerField(
        "Promień dowozu (km)", default=10,
        help_text="Wypełnij tylko dla Cateringu",
    )
    name = models.CharField("Nazwa", max_length=200)
    description = models.TextField("Opis", blank=True)
    address = models.CharField("Adres", max_length=300)
    city = models.CharField("Miasto", max_length=100)
    phone = models.CharField("Telefon", max_length=20)
    email = models.EmailField("E-mail", blank=True)
    website = models.URLField("Strona WWW", blank=True)
    facebook_url = models.URLField("Facebook", blank=True)
    instagram_url = models.URLField("Instagram", blank=True)
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
    welcome_message = models.TextField(
        "Wiadomość powitalna",
        blank=True,
        default=(
            "Dziękujemy za złożenie rezerwacji! 🎉 "
            "Cieszymy się, że wybraliście Państwo naszą firmę. "
            "Twoje zgłoszenie zostało przyjęte — skontaktujemy się z Tobą "
            "w ciągu 24 godzin, aby potwierdzić szczegóły i odpowiedzieć na "
            "ewentualne pytania. W razie pilnych spraw zadzwoń do nas. "
            "Do zobaczenia!"
        ),
        help_text="Wiadomość automatycznie wysyłana do klienta po złożeniu rezerwacji.",
    )

    # ── Godziny pracy (pon–ndz) ───────────────────────────────────────────
    mon_open = models.TimeField("Poniedziałek od", null=True, blank=True)
    mon_close = models.TimeField("Poniedziałek do", null=True, blank=True)
    tue_open = models.TimeField("Wtorek od", null=True, blank=True)
    tue_close = models.TimeField("Wtorek do", null=True, blank=True)
    wed_open = models.TimeField("Środa od", null=True, blank=True)
    wed_close = models.TimeField("Środa do", null=True, blank=True)
    thu_open = models.TimeField("Czwartek od", null=True, blank=True)
    thu_close = models.TimeField("Czwartek do", null=True, blank=True)
    fri_open = models.TimeField("Piątek od", null=True, blank=True)
    fri_close = models.TimeField("Piątek do", null=True, blank=True)
    sat_open = models.TimeField("Sobota od", null=True, blank=True)
    sat_close = models.TimeField("Sobota do", null=True, blank=True)
    sun_open = models.TimeField("Niedziela od", null=True, blank=True)
    sun_close = models.TimeField("Niedziela do", null=True, blank=True)

    show_calendar = models.BooleanField(
        "Pokaż kalendarz dostępności",
        default=False,
        help_text="Wyświetla kalendarz z wolnymi/zajętymi terminami na stronie firmy.",
    )
    max_events_per_day = models.PositiveIntegerField(
        "Maks. wydarzeń dziennie", default=1,
        help_text="Ile rezerwacji może mieć jedno miejsce w jednym dniu.",
    )

    # ── Formularz rezerwacji na zewnętrzną stronę ──────────────────────────
    booking_slug = models.SlugField(
        "Slug formularza", max_length=120, unique=True, blank=True, null=True,
        help_text="Unikalny adres formularza, np. mojevent.pl/rezerwacja/hotel-bomba",
    )
    embed_enabled = models.BooleanField(
        "Formularz zewnętrzny aktywny", default=False,
    )
    scraped_css = models.TextField(
        "Pobrane style CSS", blank=True,
        help_text="Automatycznie pobrane CSS/czcionki ze strony www restauracji.",
    )

    # ── Typy menu dostępne dla klientów (tylko venue) ──────────────────────
    enabled_menu_types = models.JSONField(
        "Dostępne typy menu",
        default=list,
        blank=True,
        help_text="Lista włączonych typów menu: detailed, limited, buffet, custom_mix",
    )

    is_active = models.BooleanField("Aktywna", default=True)
    created_at = models.DateTimeField("Data utworzenia", auto_now_add=True)
    updated_at = models.DateTimeField("Data aktualizacji", auto_now=True)

    class Meta:
        verbose_name = "Firma"
        verbose_name_plural = "Firmy"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} — {self.city}"

    DAYS_OF_WEEK = [
        ("mon", "Poniedziałek"),
        ("tue", "Wtorek"),
        ("wed", "Środa"),
        ("thu", "Czwartek"),
        ("fri", "Piątek"),
        ("sat", "Sobota"),
        ("sun", "Niedziela"),
    ]

    def get_working_hours(self):
        """Return list of dicts: {day, label, open, close, closed}."""
        hours = []
        for code, label in self.DAYS_OF_WEEK:
            h_open = getattr(self, f"{code}_open")
            h_close = getattr(self, f"{code}_close")
            hours.append({
                "day": code,
                "label": label,
                "open": h_open,
                "close": h_close,
                "closed": h_open is None or h_close is None,
            })
        return hours

    def has_working_hours(self):
        """Return True if at least one day has hours set."""
        for code, _ in self.DAYS_OF_WEEK:
            if getattr(self, f"{code}_open") and getattr(self, f"{code}_close"):
                return True
        return False

    # Mapping: Python weekday (0=Mon) → field prefix
    _WEEKDAY_PREFIX = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]

    def is_day_closed(self, d):
        """Return True if the restaurant is closed on date *d*.

        A day is closed when working hours are configured AND the weekday
        has no opening time set.
        """
        if not self.has_working_hours():
            return False  # no hours set → assume always open
        prefix = self._WEEKDAY_PREFIX[d.weekday()]
        return getattr(self, f"{prefix}_open") is None

    def average_rating(self):
        reviews = self.reviews.all()
        if reviews.exists():
            return round(reviews.aggregate(models.Avg("rating"))["rating__avg"], 1)
        return None

    def get_image_url(self):
        """Return image URL - either uploaded file or external URL."""
        if self.image:
            return self.image.url
        if self.image_url:
            return self.image_url
        # Fallback: first gallery image
        first = self.gallery_images.first()
        if first:
            return first.get_url()
        return ""

    def get_all_image_urls(self):
        """Return list of all image URLs (legacy + gallery)."""
        urls = []
        legacy = self.get_image_url()
        if legacy:
            urls.append(legacy)
        for img in self.gallery_images.all():
            url = img.get_url()
            if url and url not in urls:
                urls.append(url)
        return urls


class RestaurantImage(models.Model):
    """Zdjęcie w galerii firmy."""

    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name="gallery_images",
        verbose_name="Firma",
    )
    image = models.ImageField(
        "Plik zdjęcia", upload_to="restaurants/gallery/", blank=True, null=True,
    )
    image_url = models.URLField(
        "Link do zdjęcia", blank=True,
        help_text="Alternatywa — URL zewnętrznego zdjęcia",
    )
    caption = models.CharField("Podpis", max_length=200, blank=True)
    order = models.PositiveIntegerField("Kolejność", default=0)
    created_at = models.DateTimeField("Dodano", auto_now_add=True)

    class Meta:
        verbose_name = "Zdjęcie firmy"
        verbose_name_plural = "Zdjęcia firmy"
        ordering = ["order", "created_at"]

    def __str__(self):
        label = self.caption or f"Zdjęcie #{self.pk}"
        return f"{self.restaurant.name} — {label}"

    def get_url(self):
        if self.image:
            return self.image.url
        return self.image_url


class EventType(models.TextChoices):
    """Typy uroczystości."""

    WEDDING = "wedding", "Wesele"
    BAPTISM = "baptism", "Chrzciny"
    COMMUNION = "communion", "Komunia Święta"
    BIRTHDAY = "birthday", "Urodziny"
    INTEGRATION = "integration", "Impreza integracyjna"
    CORPORATE_XMAS = "corporate_xmas", "Wigilia firmowa"
    CATERING = "catering", "Catering"
    OTHER = "other", "Inne"


class BlockedDate(models.Model):
    """Dzień zablokowany ręcznie przez właściciela (np. remont, urlop)."""

    restaurant = models.ForeignKey(
        "Restaurant",
        on_delete=models.CASCADE,
        related_name="blocked_dates",
        verbose_name="Firma",
    )
    date = models.DateField("Data")
    reason = models.CharField("Powód", max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Zablokowany dzień"
        verbose_name_plural = "Zablokowane dni"
        ordering = ["date"]
        constraints = [
            models.UniqueConstraint(
                fields=["restaurant", "date"],
                name="unique_blocked_date",
            )
        ]

    def __str__(self):
        return f"{self.restaurant.name} — {self.date:%d.%m.%Y}"


class MenuTypeChoice(models.TextChoices):
    """Sposób kompletowania menu przy rezerwacji."""
    DETAILED = "detailed", "Szczegółowy plan"
    LIMITED = "limited", "Ograniczony Wybór"
    BUFFET = "buffet", "Szwedzki Stół"
    CUSTOM_MIX = "custom_mix", "Własny Mix"


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
        verbose_name="Firma",
    )
    event_type = models.CharField(
        "Typ uroczystości",
        max_length=20,
        choices=EventType.choices,
        blank=True,
    )
    menu_type = models.CharField(
        "Typ menu",
        max_length=20,
        choices=MenuTypeChoice.choices,
        default="",
        blank=True,
    )
    event_date = models.DateField("Data uroczystości")
    event_start_time = models.TimeField("Godzina rozpoczęcia", null=True, blank=True)
    event_end_time = models.TimeField("Godzina zakończenia", null=True, blank=True)
    guest_count = models.PositiveIntegerField(
        "Liczba gości", validators=[MinValueValidator(1)], null=True, blank=True,
    )
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
    deal_closed_at = models.DateTimeField("Data zamknięcia dealu", null=True, blank=True)
    deal_agreed_price = models.DecimalField(
        "Uzgodniona cena końcowa (zł)", max_digits=10, decimal_places=2,
        null=True, blank=True,
    )
    deal_terms = models.TextField("Warunki umowy / ustalenia", blank=True)
    created_at = models.DateTimeField("Data utworzenia", auto_now_add=True)
    updated_at = models.DateTimeField("Data aktualizacji", auto_now=True)

    class Meta:
        verbose_name = "Rezerwacja"
        verbose_name_plural = "Rezerwacje"
        ordering = ["-event_date"]
        constraints = [
            models.UniqueConstraint(
                fields=["restaurant", "event_date"],
                condition=models.Q(status__in=["pending", "confirmed"]),
                name="unique_active_restaurant_date",
            )
        ]

    def __str__(self):
        label = self.get_event_type_display() if self.event_type else "Rezerwacja"
        return f"{label} — {self.restaurant.name} ({self.event_date:%d.%m.%Y})"

    @property
    def total_cost(self):
        if self.guest_count:
            return self.guest_count * self.restaurant.price_per_person
        return 0


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
        verbose_name="Firma",
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
    """Powiązanie użytkownika z firmą — rola owner lub worker."""

    class Role(models.TextChoices):
        OWNER = "owner", "Właściciel"
        WORKER = "worker", "Pracownik"

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="restaurant_owners",
        verbose_name="Użytkownik",
    )
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name="owners",
        verbose_name="Firma",
        null=True,
        blank=True,
    )
    role = models.CharField(
        "Rola", max_length=10,
        choices=Role.choices, default=Role.OWNER,
    )
    created_at = models.DateTimeField("Data dodania", auto_now_add=True)

    class Meta:
        verbose_name = "Członek firmy"
        verbose_name_plural = "Członkowie firm"
        unique_together = ["user", "restaurant"]

    def __str__(self):
        name = self.restaurant.name if self.restaurant else "(brak firmy)"
        return f"{self.user.get_full_name() or self.user.username} → {name} ({self.get_role_display()})"


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


class BookingTodo(models.Model):
    """Zadanie do wykonania powiązane z rezerwacją."""

    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name="todos",
        verbose_name="Rezerwacja",
    )
    text = models.CharField("Zadanie", max_length=300)
    is_done = models.BooleanField("Wykonane", default=False)
    created_at = models.DateTimeField("Utworzono", auto_now_add=True)

    class Meta:
        verbose_name = "Zadanie"
        verbose_name_plural = "Zadania"
        ordering = ["is_done", "created_at"]

    def __str__(self):
        mark = "✓" if self.is_done else "○"
        return f"{mark} {self.text}"


class SavedMenu(models.Model):
    """Menu restauracji zapisane przez klienta."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="saved_menus",
        verbose_name="Użytkownik",
    )
    restaurant = models.ForeignKey(
        "Restaurant",
        on_delete=models.CASCADE,
        related_name="saved_by",
        verbose_name="Firma",
    )
    created_at = models.DateTimeField("Zapisano", auto_now_add=True)

    class Meta:
        verbose_name = "Zapisane menu"
        verbose_name_plural = "Zapisane menu"
        unique_together = ["user", "restaurant"]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} → {self.restaurant.name}"


class Menu(models.Model):
    """Nazwane menu restauracji. Jedno menu jest aktywne (wyświetlane klientom)."""

    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name="menus",
        verbose_name="Firma",
    )
    name = models.CharField("Nazwa menu", max_length=200)
    description = models.TextField("Opis", blank=True, default="")
    is_active = models.BooleanField("Aktualne", default=False)
    created_at = models.DateTimeField("Utworzono", auto_now_add=True)
    last_edited_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        verbose_name="Ostatnio edytowane przez",
    )
    last_edited_at = models.DateTimeField("Ostatnia edycja", auto_now=True)

    class Meta:
        verbose_name = "Menu"
        verbose_name_plural = "Menu"
        ordering = ["-is_active", "-created_at"]

    def __str__(self):
        active = " (aktualne)" if self.is_active else ""
        return f"{self.name}{active}"


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
        verbose_name="Firma",
    )
    menu = models.ForeignKey(
        Menu,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="items",
        verbose_name="Menu",
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


class MenuItemTemplate(models.Model):
    """Globalny katalog znanych pozycji menu z ostatnia cena.

    Uzupelniany automatycznie przy kazdym dodaniu / edycji MenuItem.
    Sluzy jako baza podpowiedzi przy tworzeniu nowego menu.
    """

    category = models.CharField(
        "Kategoria", max_length=20, choices=MenuItem.Category.choices,
    )
    name = models.CharField("Nazwa", max_length=200)
    last_price = models.DecimalField(
        "Ostatnia cena (zl)", max_digits=8, decimal_places=2, default=0,
    )
    usage_count = models.PositiveIntegerField("Ile razy uzyta", default=1)
    updated_at = models.DateTimeField("Ostatnia aktualizacja", auto_now=True)

    class Meta:
        verbose_name = "Szablon pozycji menu"
        verbose_name_plural = "Szablony pozycji menu"
        unique_together = ["category", "name"]
        ordering = ["-usage_count", "name"]

    def __str__(self):
        return f"{self.get_category_display()}: {self.name} ({self.last_price} zl)"


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
    serving_order = models.PositiveIntegerField(
        "Kolejność serwowania", default=0,
        help_text="Używane w trybie Szwedzki stół i Własny mix.",
    )
    course = models.ForeignKey(
        "BookingCourse",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="items",
        verbose_name="Danie / etap",
    )
    guest_group = models.CharField(
        "Grupa gości", max_length=50, blank=True, default="",
        help_text="Np. Dorośli, Dzieci, Vege — używane w Własny mix.",
    )

    class Meta:
        verbose_name = "Wybór menu"
        verbose_name_plural = "Wybory menu"
        unique_together = ["booking", "menu_item"]

    def __str__(self):
        return f"{self.menu_item.name} x{self.quantity}"

    @property
    def subtotal(self):
        return self.menu_item.price * self.quantity


class BookingCourse(models.Model):
    """Etap / danie serwowane w trybie Własny Mix."""

    class ServingStyle(models.TextChoices):
        FOR_ALL = "for_all", "Dla wszystkich (jedno danie)"
        CHOICE = "choice", "Do wyboru (goście wybierają)"
        BUFFET = "buffet_style", "Na stół (goście nakładają)"
        CONTINUOUS = "continuous", "Ciągłe serwowanie"

    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name="courses",
        verbose_name="Rezerwacja",
    )
    name = models.CharField("Nazwa etapu", max_length=100)
    order = models.PositiveIntegerField("Kolejność", default=0)
    serving_style = models.CharField(
        "Sposób serwowania",
        max_length=20,
        choices=ServingStyle.choices,
        default=ServingStyle.FOR_ALL,
    )

    class Meta:
        verbose_name = "Etap menu (Mix)"
        verbose_name_plural = "Etapy menu (Mix)"
        ordering = ["order"]

    def __str__(self):
        return f"{self.name} ({self.get_serving_style_display()})"


class Dish(models.Model):
    """Baza potraw restauracji — Moja Baza Potraw.

    Per-restaurant dish library used as quick-add source when building menus.
    Imported from Excel, Word, text paste, external catalog, or added manually.
    """

    class Source(models.TextChoices):
        MANUAL = "manual", "Ręcznie"
        EXCEL = "excel", "Import z Excel"
        WORD = "word", "Import z Word"
        TEXT = "text", "Import z tekstu"
        EXTERNAL = "external", "Zewnętrzna baza"
        MENU = "menu", "Z istniejącego menu"

    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name="dishes",
        verbose_name="Firma",
    )
    category = models.CharField(
        "Kategoria", max_length=20, choices=MenuItem.Category.choices,
    )
    name = models.CharField("Nazwa", max_length=200)
    description = models.TextField("Opis", blank=True)
    price = models.DecimalField(
        "Cena (zł)", max_digits=8, decimal_places=2, default=0,
    )
    source = models.CharField(
        "Źródło", max_length=20,
        choices=Source.choices, default=Source.MANUAL,
    )
    created_at = models.DateTimeField("Dodano", auto_now_add=True)

    class Meta:
        verbose_name = "Potrawa"
        verbose_name_plural = "Baza potraw"
        ordering = ["category", "name"]
        unique_together = ["restaurant", "category", "name"]

    def __str__(self):
        return f"{self.get_category_display()}: {self.name} ({self.price} zł)"


class AttractionItem(models.Model):
    """Pozycja oferty firmy typu Atrakcje."""

    class Tag(models.TextChoices):
        SCIANKA = "scianka", "Ścianka"
        TORT = "tort", "Tort"
        FOTOGRAF = "fotograf", "Fotograf"
        WIDEO = "wideo", "Wideofilmowanie"
        FOTOBUDKA = "fotobudka", "Fotobudka"
        FONTANNA = "fontanna", "Fontanna czekoladowa"

    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name="attraction_items",
        verbose_name="Firma",
    )
    name = models.CharField("Nazwa", max_length=200)
    description = models.TextField("Opis", blank=True)
    image_url = models.URLField("Link do zdjęcia", blank=True)
    price = models.DecimalField(
        "Cena (zł)", max_digits=8, decimal_places=2, default=0
    )
    tag = models.CharField(
        "Tag", max_length=20, choices=Tag.choices
    )
    is_active = models.BooleanField("Aktywna", default=True)
    order = models.PositiveIntegerField("Kolejność", default=0)
    created_at = models.DateTimeField("Utworzono", auto_now_add=True)

    class Meta:
        verbose_name = "Pozycja atrakcji"
        verbose_name_plural = "Pozycje atrakcji"
        ordering = ["tag", "order", "name"]

    def __str__(self):
        return f"{self.get_tag_display()}: {self.name} ({self.price} zł)"


class BookingMessage(models.Model):
    """Wiadomość w chacie rezerwacji — komunikacja klient ↔ firma."""

    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name="chat_messages",
        verbose_name="Rezerwacja",
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="booking_messages",
        verbose_name="Nadawca",
    )
    content = models.TextField("Treść wiadomości")
    created_at = models.DateTimeField("Data wysłania", auto_now_add=True)

    class Meta:
        verbose_name = "Wiadomość czatu"
        verbose_name_plural = "Wiadomości czatu"
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.sender.get_full_name() or self.sender.username}: {self.content[:50]}"


class UserProfile(models.Model):
    """Profil użytkownika z dodatkowymi danymi."""

    class ClientType(models.TextChoices):
        PRIVATE = "private", "Osoba prywatna"
        COMPANY = "company", "Firma"

    CITY_CHOICES = [
        ("Poznań", "Poznań"),
        ("Warszawa", "Warszawa"),
        ("Kraków", "Kraków"),
        ("Wrocław", "Wrocław"),
        ("Gdańsk", "Gdańsk"),
        ("Łódź", "Łódź"),
        ("Katowice", "Katowice"),
        ("Szczecin", "Szczecin"),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile",
        verbose_name="Użytkownik",
    )
    phone = models.CharField("Telefon", max_length=20, blank=True)
    city = models.CharField("Miasto", max_length=100, blank=True, default="Poznań")
    client_type = models.CharField(
        "Typ klienta", max_length=10,
        choices=ClientType.choices, default=ClientType.PRIVATE,
    )
    company_name = models.CharField("Nazwa firmy", max_length=200, blank=True)
    company_address = models.CharField("Adres firmy", max_length=300, blank=True)
    company_nip = models.CharField("NIP", max_length=20, blank=True)

    class Meta:
        verbose_name = "Profil użytkownika"
        verbose_name_plural = "Profile użytkowników"

    @property
    def is_company(self):
        return self.client_type == self.ClientType.COMPANY

    def __str__(self):
        return f"Profil: {self.user.get_full_name() or self.user.username}"
