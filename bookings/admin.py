from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from .models import Restaurant, Booking, Review, RestaurantOwner, BookingNote


# ── Rozszerzony panel użytkowników z kolumną Rola ─────────────────────────────

admin.site.unregister(User)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ["username", "first_name", "last_name", "email", "rola", "is_active", "date_joined"]
    list_filter = ["is_superuser", "is_staff", "is_active"]

    @admin.display(description="Rola", ordering="is_superuser")
    def rola(self, obj):
        if obj.is_superuser:
            return format_html('<span style="color:#dc3545;font-weight:bold;">⛑ Administracja</span>')
        if hasattr(obj, "restaurant_owner"):
            return format_html('<span style="color:#198754;font-weight:bold;">🏪 Restauracja</span>')
        return format_html('<span style="color:#0d6efd;">👤 Użytkownik</span>')


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = [
        "name", "city", "max_guests", "price_per_person",
        "has_parking", "has_garden", "has_dance_floor", "is_active",
    ]
    list_filter = ["city", "is_active", "has_parking", "has_garden", "has_dance_floor"]
    search_fields = ["name", "city", "address"]
    fieldsets = (
        (None, {"fields": ("name", "description", "is_active")}),
        ("Adres i kontakt", {"fields": ("address", "city", "phone", "email", "website")}),
        ("Zdjęcia", {"fields": (("image", "image_url"),)}),
        ("Lokalizacja GPS", {"fields": (("latitude", "longitude"),)}),
        ("Parametry", {"fields": ("max_guests", "price_per_person")}),
        ("Udogodnienia", {"fields": ("has_parking", "has_garden", "has_dance_floor", "has_accommodation")}),
    )
    list_editable = ["is_active"]


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = [
        "pk", "user", "restaurant", "event_type", "event_date",
        "guest_count", "status", "created_at",
    ]
    list_filter = ["status", "event_type", "event_date"]
    search_fields = ["first_name", "last_name", "email", "restaurant__name"]
    list_editable = ["status"]
    readonly_fields = ["created_at", "updated_at"]
    date_hierarchy = "event_date"


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ["user", "restaurant", "rating", "created_at"]
    list_filter = ["rating", "created_at"]
    search_fields = ["user__username", "restaurant__name", "comment"]
    readonly_fields = ["created_at"]


@admin.register(RestaurantOwner)
class RestaurantOwnerAdmin(admin.ModelAdmin):
    list_display = ["user", "restaurant", "is_main_owner", "created_at"]
    list_filter = ["is_main_owner", "created_at", "restaurant__city"]
    search_fields = ["user__username", "user__first_name", "user__last_name", "restaurant__name"]
    autocomplete_fields = ["user", "restaurant"]
    readonly_fields = ["created_at"]


@admin.register(BookingNote)
class BookingNoteAdmin(admin.ModelAdmin):
    list_display = ["booking", "date", "title", "author", "created_at"]
    list_filter = ["date", "created_at"]
    search_fields = ["title", "content", "booking__first_name", "booking__last_name"]
    readonly_fields = ["created_at"]
