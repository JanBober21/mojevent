"""
URL routing REST API dla aplikacji MojEvent.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

from .api_views import (
    RestaurantViewSet,
    BookingViewSet,
    MenuItemViewSet,
    BookingMenuItemViewSet,
    AttractionItemViewSet,
    ReviewViewSet,
    BookingMessageViewSet,
    BookingNoteViewSet,
    api_login,
    api_logout,
    api_me,
)

router = DefaultRouter()
router.register(r"firmy", RestaurantViewSet, basename="api-restaurant")
router.register(r"rezerwacje", BookingViewSet, basename="api-booking")

urlpatterns = [
    # OpenAPI schema + Swagger UI + ReDoc
    path("schema/", SpectacularAPIView.as_view(), name="api-schema"),
    path("docs/", SpectacularSwaggerView.as_view(url_name="api-schema"), name="api-docs"),
    path("redoc/", SpectacularRedocView.as_view(url_name="api-schema"), name="api-redoc"),

    # Auth
    path("auth/login/", api_login, name="api-login"),
    path("auth/logout/", api_logout, name="api-logout"),
    path("auth/me/", api_me, name="api-me"),

    # Router (firmy, rezerwacje)
    path("", include(router.urls)),

    # Nested: menu firmy — /api/firmy/{id}/menu/
    path(
        "firmy/<int:restaurant_pk>/menu/",
        MenuItemViewSet.as_view({"get": "list", "post": "create"}),
        name="api-menu-list",
    ),
    path(
        "firmy/<int:restaurant_pk>/menu/<int:pk>/",
        MenuItemViewSet.as_view({"get": "retrieve", "patch": "partial_update", "delete": "destroy"}),
        name="api-menu-detail",
    ),

    # Nested: atrakcje firmy — /api/firmy/{id}/atrakcje/
    path(
        "firmy/<int:restaurant_pk>/atrakcje/",
        AttractionItemViewSet.as_view({"get": "list"}),
        name="api-attraction-list",
    ),
    path(
        "firmy/<int:restaurant_pk>/atrakcje/<int:pk>/",
        AttractionItemViewSet.as_view({"get": "retrieve"}),
        name="api-attraction-detail",
    ),

    # Nested: opinie firmy — /api/firmy/{id}/opinie/
    path(
        "firmy/<int:restaurant_pk>/opinie/",
        ReviewViewSet.as_view({"get": "list", "post": "create"}),
        name="api-review-list",
    ),

    # Nested: czat rezerwacji — /api/rezerwacje/{id}/czat/
    path(
        "rezerwacje/<int:booking_pk>/czat/",
        BookingMessageViewSet.as_view({"get": "list", "post": "create"}),
        name="api-chat-list",
    ),

    # Nested: wybory menu rezerwacji — /api/rezerwacje/{id}/menu/
    path(
        "rezerwacje/<int:booking_pk>/menu/",
        BookingMenuItemViewSet.as_view({"get": "list", "post": "create"}),
        name="api-booking-menu-list",
    ),
    path(
        "rezerwacje/<int:booking_pk>/menu/<int:pk>/",
        BookingMenuItemViewSet.as_view({"delete": "destroy"}),
        name="api-booking-menu-detail",
    ),

    # Nested: notatki CRM rezerwacji — /api/rezerwacje/{id}/notatki/
    path(
        "rezerwacje/<int:booking_pk>/notatki/",
        BookingNoteViewSet.as_view({"get": "list", "post": "create"}),
        name="api-note-list",
    ),
    path(
        "rezerwacje/<int:booking_pk>/notatki/<int:pk>/",
        BookingNoteViewSet.as_view({"patch": "partial_update", "delete": "destroy"}),
        name="api-note-detail",
    ),
]
