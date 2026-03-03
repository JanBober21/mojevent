from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from django.http import HttpResponse
import csv
from .models import Restaurant, Booking, Review, RestaurantOwner, BookingNote, MenuItem, BookingMenuItem, AttractionItem, BookingMessage


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
            return format_html('<span style="color:#198754;font-weight:bold;">🏪 Firma</span>')
        return format_html('<span style="color:#0d6efd;">👤 Użytkownik</span>')


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = [
        "name", "firm_type", "city", "max_guests", "price_per_person",
        "has_parking", "has_garden", "has_dance_floor", "is_active",
    ]
    list_filter = ["firm_type", "city", "is_active", "has_parking", "has_garden", "has_dance_floor"]
    search_fields = ["name", "city", "address"]
    fieldsets = (
        (None, {"fields": ("firm_type", "attraction_type", "delivery_radius_km", "name", "description", "is_active")}),
        ("Adres i kontakt", {"fields": ("address", "city", "phone", "email", "website")}),
        ("Zdjęcia", {"fields": (("image", "image_url"),)}),
        ("Lokalizacja GPS", {"fields": (("latitude", "longitude"),)}),
        ("Parametry", {"fields": ("max_guests", "price_per_person")}),
        ("Udogodnienia", {"fields": ("has_parking", "has_garden", "has_dance_floor", "has_accommodation")}),
    )
    list_editable = ["is_active"]
    actions = ["export_csv"]

    @admin.action(description="Eksportuj zaznaczone do CSV")
    def export_csv(self, request, queryset):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="firmy.csv"'
        response.write("\ufeff")  # BOM for Excel UTF-8
        writer = csv.writer(response, delimiter=";")
        writer.writerow([
            "Typ firmy", "Nazwa", "Miasto", "Adres", "Telefon", "Email", "Strona www",
            "Maks. go\u015bci", "Cena/os.", "Parking", "Ogr\u00f3d", "Parkiet",
            "Noclegi", "Aktywna", "Szeroko\u015b\u0107 GPS", "D\u0142ugo\u015b\u0107 GPS",
        ])
        for r in queryset:
            writer.writerow([
                r.get_firm_type_display(), r.name, r.city, r.address, r.phone, r.email, r.website or "",
                r.max_guests, r.price_per_person,
                "Tak" if r.has_parking else "Nie",
                "Tak" if r.has_garden else "Nie",
                "Tak" if r.has_dance_floor else "Nie",
                "Tak" if r.has_accommodation else "Nie",
                "Tak" if r.is_active else "Nie",
                r.latitude or "", r.longitude or "",
            ])
        self.message_user(request, f"Wyeksportowano {queryset.count()} firm do CSV.")
        return response

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


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ["name", "restaurant", "category", "price", "is_visible", "order"]
    list_filter = ["category", "is_visible", "restaurant"]
    search_fields = ["name", "description", "restaurant__name"]
    list_editable = ["is_visible", "order"]


@admin.register(BookingMenuItem)
class BookingMenuItemAdmin(admin.ModelAdmin):
    list_display = ["booking", "menu_item", "quantity"]
    list_filter = ["menu_item__restaurant", "menu_item__category"]
    search_fields = ["booking__first_name", "booking__last_name", "menu_item__name"]


@admin.register(AttractionItem)
class AttractionItemAdmin(admin.ModelAdmin):
    list_display = ["name", "tag", "price", "restaurant", "is_active"]
    list_filter = ["tag", "is_active", "restaurant"]
    search_fields = ["name", "description"]
    list_editable = ["is_active"]


@admin.register(BookingMessage)
class BookingMessageAdmin(admin.ModelAdmin):
    list_display = ["booking", "sender", "short_content", "created_at"]
    list_filter = ["created_at"]
    search_fields = ["content", "sender__username", "sender__first_name"]
    readonly_fields = ["created_at"]

    @admin.display(description="Treść")
    def short_content(self, obj):
        return obj.content[:80] + "…" if len(obj.content) > 80 else obj.content
