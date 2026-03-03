"""
Serializery REST API dla aplikacji MojEvent.
"""

from __future__ import annotations

from rest_framework import serializers
from django.contrib.auth.models import User
from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes

from .models import (
    Restaurant,
    Booking,
    Review,
    MenuItem,
    BookingMenuItem,
    AttractionItem,
    BookingMessage,
    BookingNote,
)


# ──────────────────────────────────────────────
# Auth / User
# ──────────────────────────────────────────────

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name", "email"]
        read_only_fields = fields


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


# ──────────────────────────────────────────────
# Restaurant (Firma)
# ──────────────────────────────────────────────

class RestaurantListSerializer(serializers.ModelSerializer):
    """Skrócony widok firmy dla listy."""

    average_rating = serializers.SerializerMethodField()
    firm_type_display = serializers.CharField(
        source="get_firm_type_display", read_only=True
    )

    class Meta:
        model = Restaurant
        fields = [
            "id", "name", "firm_type", "firm_type_display",
            "city", "address", "price_per_person", "max_guests",
            "image_url", "latitude", "longitude",
            "average_rating", "is_active",
        ]

    @extend_schema_field(OpenApiTypes.FLOAT)
    def get_average_rating(self, obj):
        return obj.average_rating()


# ──────────────────────────────────────────────
# Menu
# ──────────────────────────────────────────────

class MenuItemSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(
        source="get_category_display", read_only=True
    )

    class Meta:
        model = MenuItem
        fields = [
            "id", "category", "category_display",
            "name", "description", "price", "is_visible", "order",
        ]


# ──────────────────────────────────────────────
# Attraction
# ──────────────────────────────────────────────

class AttractionItemSerializer(serializers.ModelSerializer):
    tag_display = serializers.CharField(
        source="get_tag_display", read_only=True
    )

    class Meta:
        model = AttractionItem
        fields = [
            "id", "name", "description", "image_url",
            "price", "tag", "tag_display", "is_active", "order",
        ]


# ──────────────────────────────────────────────
# Restaurant Detail (po Menu i Attraction)
# ──────────────────────────────────────────────

class RestaurantDetailSerializer(serializers.ModelSerializer):
    """Pełny widok firmy z udogodnieniami."""

    average_rating = serializers.SerializerMethodField()
    firm_type_display = serializers.CharField(
        source="get_firm_type_display", read_only=True
    )
    attraction_type_display = serializers.CharField(
        source="get_attraction_type_display", read_only=True
    )
    menu_items = serializers.SerializerMethodField()
    attraction_items = serializers.SerializerMethodField()

    class Meta:
        model = Restaurant
        fields = [
            "id", "name", "firm_type", "firm_type_display",
            "attraction_type", "attraction_type_display",
            "delivery_radius_km",
            "description", "address", "city", "phone", "email", "website",
            "image", "image_url",
            "max_guests", "price_per_person",
            "has_parking", "has_garden", "has_dance_floor", "has_accommodation",
            "latitude", "longitude",
            "is_active", "average_rating",
            "menu_items", "attraction_items",
            "created_at", "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    @extend_schema_field(OpenApiTypes.FLOAT)
    def get_average_rating(self, obj):
        return obj.average_rating()

    @extend_schema_field(MenuItemSerializer(many=True))
    def get_menu_items(self, obj):
        qs = obj.menu_items.filter(is_visible=True)
        return MenuItemSerializer(qs, many=True).data

    @extend_schema_field(AttractionItemSerializer(many=True))
    def get_attraction_items(self, obj):
        qs = obj.attraction_items.filter(is_active=True)
        return AttractionItemSerializer(qs, many=True).data


class BookingMenuItemSerializer(serializers.ModelSerializer):
    menu_item = MenuItemSerializer(read_only=True)
    menu_item_id = serializers.PrimaryKeyRelatedField(
        queryset=MenuItem.objects.all(), source="menu_item", write_only=True
    )
    subtotal = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )

    class Meta:
        model = BookingMenuItem
        fields = ["id", "menu_item", "menu_item_id", "quantity", "subtotal"]


# ──────────────────────────────────────────────
# Booking (Rezerwacja)
# ──────────────────────────────────────────────

class BookingListSerializer(serializers.ModelSerializer):
    """Skrócony widok rezerwacji dla listy."""

    restaurant_name = serializers.CharField(
        source="restaurant.name", read_only=True
    )
    event_type_display = serializers.CharField(
        source="get_event_type_display", read_only=True
    )
    status_display = serializers.CharField(
        source="get_status_display", read_only=True
    )

    class Meta:
        model = Booking
        fields = [
            "id", "restaurant", "restaurant_name",
            "event_type", "event_type_display",
            "event_date", "guest_count",
            "status", "status_display",
            "first_name", "last_name",
            "deal_closed_at", "deal_agreed_price",
            "created_at",
        ]


class BookingDetailSerializer(serializers.ModelSerializer):
    """Pełny widok rezerwacji z menu i czatem."""

    restaurant_name = serializers.CharField(
        source="restaurant.name", read_only=True
    )
    event_type_display = serializers.CharField(
        source="get_event_type_display", read_only=True
    )
    status_display = serializers.CharField(
        source="get_status_display", read_only=True
    )
    menu_selections = BookingMenuItemSerializer(many=True, read_only=True)
    total_cost = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )

    class Meta:
        model = Booking
        fields = [
            "id", "user", "restaurant", "restaurant_name",
            "event_type", "event_type_display",
            "event_date", "guest_count",
            "status", "status_display",
            "first_name", "last_name", "phone", "email", "notes",
            "deal_closed_at", "deal_agreed_price", "deal_terms",
            "menu_selections", "total_cost",
            "created_at", "updated_at",
        ]
        read_only_fields = [
            "user", "status", "deal_closed_at",
            "created_at", "updated_at",
        ]


class BookingCreateSerializer(serializers.ModelSerializer):
    """Tworzenie nowej rezerwacji."""

    class Meta:
        model = Booking
        fields = [
            "restaurant", "event_type", "event_date", "guest_count",
            "first_name", "last_name", "phone", "email", "notes",
        ]

    def validate_event_date(self, value):
        from django.utils import timezone
        if value < timezone.now().date():
            raise serializers.ValidationError("Data nie może być w przeszłości.")
        return value

    def validate(self, data):
        restaurant = data["restaurant"]
        if Booking.objects.filter(
            restaurant=restaurant,
            event_date=data["event_date"],
        ).exclude(status="cancelled").exists():
            raise serializers.ValidationError(
                {"event_date": "Ten termin jest już zajęty."}
            )
        return data


# ──────────────────────────────────────────────
# Review (Opinia)
# ──────────────────────────────────────────────

class ReviewSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Review
        fields = [
            "id", "user", "username", "restaurant",
            "rating", "comment", "created_at",
        ]
        read_only_fields = ["user", "created_at"]


# ──────────────────────────────────────────────
# Chat (BookingMessage)
# ──────────────────────────────────────────────

class BookingMessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.SerializerMethodField()

    class Meta:
        model = BookingMessage
        fields = [
            "id", "booking", "sender", "sender_name",
            "content", "created_at",
        ]
        read_only_fields = ["sender", "created_at"]

    @extend_schema_field(OpenApiTypes.STR)
    def get_sender_name(self, obj):
        return obj.sender.get_full_name() or obj.sender.username


# ──────────────────────────────────────────────
# CRM Note
# ──────────────────────────────────────────────

class BookingNoteSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()

    class Meta:
        model = BookingNote
        fields = [
            "id", "booking", "author", "author_name",
            "date", "title", "content", "created_at",
        ]
        read_only_fields = ["author", "created_at"]

    @extend_schema_field(OpenApiTypes.STR)
    def get_author_name(self, obj):
        if obj.author:
            return obj.author.get_full_name() or obj.author.username
        return None


# ──────────────────────────────────────────────
# Deal (zamknięcie dealu)
# ──────────────────────────────────────────────

class CloseDealSerializer(serializers.Serializer):
    """Dane do zamknięcia dealu."""

    deal_agreed_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    deal_terms = serializers.CharField(required=False, allow_blank=True, default="")
