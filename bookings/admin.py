from django.contrib import admin
from .models import Restaurant, Booking, Review


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = [
        "name", "city", "max_guests", "price_per_person",
        "has_parking", "has_garden", "has_dance_floor", "is_active",
    ]
    list_filter = ["city", "is_active", "has_parking", "has_garden", "has_dance_floor"]
    search_fields = ["name", "city", "address"]
    fieldsets = (
        (None, {"fields": ("name", "description", "image", "is_active")}),
        ("Adres i kontakt", {"fields": ("address", "city", "phone", "email", "website")}),
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
