from django.urls import path
from django.contrib.auth import views as auth_views

from . import views

urlpatterns = [
    # Strona główna
    path("", views.home, name="home"),

    # Restauracje
    path("restauracje/", views.restaurant_list, name="restaurant_list"),
    path("restauracje/<int:pk>/", views.restaurant_detail, name="restaurant_detail"),

    # Rezerwacje
    path(
        "restauracje/<int:restaurant_pk>/rezerwuj/",
        views.booking_create,
        name="booking_create",
    ),
    path("rezerwacje/", views.booking_list, name="booking_list"),
    path("rezerwacje/<int:pk>/", views.booking_detail, name="booking_detail"),
    path("rezerwacje/<int:pk>/anuluj/", views.booking_cancel, name="booking_cancel"),

    # Opinie
    path(
        "restauracje/<int:restaurant_pk>/opinia/",
        views.review_create,
        name="review_create",
    ),

    # Panel właścicieli restauracji
    path("owner/", views.owner_dashboard, name="owner_dashboard"),
    path("owner/bookings/", views.owner_bookings, name="owner_bookings"),
    path("owner/booking/<int:booking_id>/", views.owner_booking_detail, name="owner_booking_detail"),
    path("owner/booking/<int:booking_id>/umowa/", views.owner_booking_agreement, name="owner_booking_agreement"),
    path("owner/calendar/", views.owner_calendar, name="owner_calendar"),
    path("owner/restauracja/dodaj/", views.owner_restaurant_create, name="owner_restaurant_create"),
    path("owner/restauracja/edytuj/", views.owner_restaurant_edit, name="owner_restaurant_edit"),
    path("owner/menu/", views.owner_menu, name="owner_menu"),
    path("owner/atrakcje/", views.owner_attractions, name="owner_attractions"),
    path("owner/firmy/", views.owner_firms, name="owner_firms"),
    path("owner/firmy/przelacz/<int:restaurant_id>/", views.owner_switch_firm, name="owner_switch_firm"),

    # Menu dla klienta
    path("rezerwacje/<int:pk>/menu/", views.booking_menu_select, name="booking_menu_select"),

    # Autoryzacja
    path("rejestracja/", views.register, name="register"),
    path("rejestracja/restauracja/", views.owner_register, name="owner_register"),
    path(
        "logowanie/",
        auth_views.LoginView.as_view(template_name="bookings/login.html"),
        name="login",
    ),
    path("wyloguj/", auth_views.LogoutView.as_view(), name="logout"),
]
