"""
REST API viewsets i widoki dla aplikacji MojEvent.
"""

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework import viewsets, status, permissions, filters, serializers as drf_serializers
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, inline_serializer

from .models import (
    Restaurant,
    Booking,
    Review,
    Menu,
    MenuItem,
    BookingMenuItem,
    AttractionItem,
    BookingMessage,
    BookingNote,
)
from .serializers import (
    RestaurantListSerializer,
    RestaurantDetailSerializer,
    BookingListSerializer,
    BookingDetailSerializer,
    BookingCreateSerializer,
    ReviewSerializer,
    MenuItemSerializer,
    BookingMenuItemSerializer,
    AttractionItemSerializer,
    BookingMessageSerializer,
    BookingNoteSerializer,
    CloseDealSerializer,
    UserSerializer,
    LoginSerializer,
)


# ──────────────────────────────────────────────
# Permissions
# ──────────────────────────────────────────────

class IsOwnerOfRestaurant(permissions.BasePermission):
    """Pozwala tylko właścicielowi danej firmy."""

    def has_permission(self, request, view):
        return hasattr(request.user, "restaurant_owner")


class IsBookingParticipant(permissions.BasePermission):
    """Pozwala klientowi lub właścicielowi firmy powiązanej z rezerwacją."""

    def has_object_permission(self, request, view, obj):
        if obj.user == request.user:
            return True
        if hasattr(request.user, "restaurant_owner"):
            return request.user.restaurant_owner.restaurant == obj.restaurant
        return False


# ──────────────────────────────────────────────
# Auth
# ──────────────────────────────────────────────

@extend_schema(tags=["Auth"], request=LoginSerializer, responses={200: UserSerializer})
@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def api_login(request):
    """Logowanie — tworzy sesję."""
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = authenticate(
        request,
        username=serializer.validated_data["username"],
        password=serializer.validated_data["password"],
    )
    if user is None:
        return Response(
            {"detail": "Nieprawidłowe dane logowania."},
            status=status.HTTP_401_UNAUTHORIZED,
        )
    login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    return Response(UserSerializer(user).data)


@extend_schema(tags=["Auth"], request=None, responses={200: inline_serializer("LogoutResponse", {"detail": drf_serializers.CharField()})})
@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def api_logout(request):
    """Wylogowanie — usuwa sesję."""
    logout(request)
    return Response({"detail": "Wylogowano."})


@extend_schema(tags=["Auth"], responses={200: UserSerializer})
@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def api_me(request):
    """Dane zalogowanego użytkownika."""
    data = UserSerializer(request.user).data
    data["is_owner"] = hasattr(request.user, "restaurant_owner")
    if data["is_owner"]:
        owner = request.user.restaurant_owner
        data["restaurant_id"] = owner.restaurant_id
    return Response(data)


# ──────────────────────────────────────────────
# Restaurant (Firma)
# ──────────────────────────────────────────────

@extend_schema_view(
    list=extend_schema(tags=["Firmy"], summary="Lista firm"),
    retrieve=extend_schema(tags=["Firmy"], summary="Szczegóły firmy"),
)
class RestaurantViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Lista i szczegóły firm (tylko odczyt).
    Obsługuje filtrowanie po `firm_type`, `city` oraz wyszukiwanie po nazwie.
    """

    queryset = Restaurant.objects.filter(is_active=True)
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["firm_type", "city", "attraction_type"]
    search_fields = ["name", "description", "city"]
    ordering_fields = ["name", "price_per_person", "created_at"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return RestaurantDetailSerializer
        return RestaurantListSerializer


# ──────────────────────────────────────────────
# Booking (Rezerwacja)
# ──────────────────────────────────────────────

@extend_schema_view(
    list=extend_schema(tags=["Rezerwacje"], summary="Moje rezerwacje"),
    retrieve=extend_schema(tags=["Rezerwacje"], summary="Szczegóły rezerwacji"),
    create=extend_schema(tags=["Rezerwacje"], summary="Nowa rezerwacja"),
)
class BookingViewSet(viewsets.ModelViewSet):
    """
    CRUD rezerwacji.
    - Klient widzi swoje rezerwacje.
    - Właściciel widzi rezerwacje swojej firmy.
    """

    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["status", "event_type"]
    ordering_fields = ["event_date", "created_at"]
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Booking.objects.none()
        user = self.request.user
        if hasattr(user, "restaurant_owner") and user.restaurant_owner.restaurant:
            return Booking.objects.filter(
                restaurant=user.restaurant_owner.restaurant
            )
        return Booking.objects.filter(user=user)

    def get_serializer_class(self):
        if self.action == "create":
            return BookingCreateSerializer
        if self.action in ("retrieve",):
            return BookingDetailSerializer
        return BookingListSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    # ── akcje statusu ──

    @extend_schema(tags=["Rezerwacje"], request=None, responses={200: BookingDetailSerializer})
    @action(detail=True, methods=["post"], url_path="potwierdz")
    def confirm(self, request, pk=None):
        """Zatwierdź rezerwację (właściciel)."""
        booking = self.get_object()
        if not self._is_owner_of(booking, request.user):
            return Response({"detail": "Brak uprawnień."}, status=403)
        booking.status = Booking.Status.CONFIRMED
        booking.save(update_fields=["status", "updated_at"])
        return Response(BookingDetailSerializer(booking).data)

    @extend_schema(tags=["Rezerwacje"], request=None, responses={200: BookingDetailSerializer})
    @action(detail=True, methods=["post"], url_path="anuluj")
    def cancel(self, request, pk=None):
        """Anuluj rezerwację (klient lub właściciel)."""
        booking = self.get_object()
        booking.status = Booking.Status.CANCELLED
        booking.save(update_fields=["status", "updated_at"])
        return Response(BookingDetailSerializer(booking).data)

    # ── deal ──

    @extend_schema(tags=["Rezerwacje"], request=CloseDealSerializer, responses={200: BookingDetailSerializer})
    @action(detail=True, methods=["post"], url_path="zamknij-deal")
    def close_deal(self, request, pk=None):
        """Zamknij deal — ustaw cenę i warunki, wygeneruj umowę."""
        booking = self.get_object()
        if not self._is_owner_of(booking, request.user):
            return Response({"detail": "Brak uprawnień."}, status=403)
        ser = CloseDealSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        booking.deal_agreed_price = ser.validated_data["deal_agreed_price"]
        booking.deal_terms = ser.validated_data.get("deal_terms", "")
        booking.deal_closed_at = timezone.now()
        if booking.status == Booking.Status.PENDING:
            booking.status = Booking.Status.CONFIRMED
        booking.save()
        return Response(BookingDetailSerializer(booking).data)

    @extend_schema(tags=["Rezerwacje"], request=None, responses={200: BookingDetailSerializer})
    @action(detail=True, methods=["post"], url_path="otworz-deal")
    def reopen_deal(self, request, pk=None):
        """Otwórz deal ponownie — wyczyść dane dealu."""
        booking = self.get_object()
        if not self._is_owner_of(booking, request.user):
            return Response({"detail": "Brak uprawnień."}, status=403)
        booking.deal_closed_at = None
        booking.deal_agreed_price = None
        booking.deal_terms = ""
        booking.save()
        return Response(BookingDetailSerializer(booking).data)

    @staticmethod
    def _is_owner_of(booking, user):
        return (
            hasattr(user, "restaurant_owner")
            and user.restaurant_owner.restaurant == booking.restaurant
        )


# ──────────────────────────────────────────────
# Menu
# ──────────────────────────────────────────────

@extend_schema_view(
    list=extend_schema(tags=["Menu"], summary="Menu firmy"),
    retrieve=extend_schema(tags=["Menu"], summary="Pozycja menu"),
    create=extend_schema(tags=["Menu"], summary="Dodaj pozycję menu"),
    partial_update=extend_schema(tags=["Menu"], summary="Edytuj pozycję menu"),
    destroy=extend_schema(tags=["Menu"], summary="Usuń pozycję menu"),
)
class MenuItemViewSet(viewsets.ModelViewSet):
    """
    CRUD pozycji menu.
    GET — publiczny (is_visible=True); POST/PATCH/DELETE — właściciel.
    """

    serializer_class = MenuItemSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["category"]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        restaurant_id = self.kwargs.get("restaurant_pk")
        if getattr(self, "swagger_fake_view", False):
            return MenuItem.objects.none()
        qs = MenuItem.objects.filter(restaurant_id=restaurant_id)
        if self.request.method == "GET" and not self._is_owner(restaurant_id):
            # Publiczny dostęp — tylko pozycje z aktywnego menu
            active_menu = Menu.objects.filter(
                restaurant_id=restaurant_id, is_active=True,
            ).first()
            qs = qs.filter(is_visible=True, menu=active_menu) if active_menu else qs.none()
        return qs

    def get_permissions(self):
        if self.action in ("create", "partial_update", "destroy"):
            return [permissions.IsAuthenticated(), IsOwnerOfRestaurant()]
        return [permissions.AllowAny()]

    def perform_create(self, serializer):
        restaurant_id = self.kwargs["restaurant_pk"]
        serializer.save(restaurant_id=restaurant_id)

    def _is_owner(self, restaurant_id):
        user = self.request.user
        return (
            user.is_authenticated
            and hasattr(user, "restaurant_owner")
            and str(user.restaurant_owner.restaurant_id) == str(restaurant_id)
        )


# ──────────────────────────────────────────────
# Booking Menu Selections
# ──────────────────────────────────────────────

@extend_schema_view(
    list=extend_schema(tags=["Menu"], summary="Wybory menu rezerwacji"),
    create=extend_schema(tags=["Menu"], summary="Dodaj pozycję do wyboru"),
    destroy=extend_schema(tags=["Menu"], summary="Usuń pozycję z wyboru"),
)
class BookingMenuItemViewSet(viewsets.ModelViewSet):
    """Zarządzanie wybranymi pozycjami menu w rezerwacji."""

    serializer_class = BookingMenuItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "post", "delete", "head", "options"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return BookingMenuItem.objects.none()
        return BookingMenuItem.objects.filter(
            booking_id=self.kwargs["booking_pk"]
        ).select_related("menu_item")

    def perform_create(self, serializer):
        serializer.save(booking_id=self.kwargs["booking_pk"])


# ──────────────────────────────────────────────
# Attractions
# ──────────────────────────────────────────────

@extend_schema_view(
    list=extend_schema(tags=["Atrakcje"], summary="Oferta atrakcji firmy"),
    retrieve=extend_schema(tags=["Atrakcje"], summary="Szczegóły atrakcji"),
)
class AttractionItemViewSet(viewsets.ReadOnlyModelViewSet):
    """Lista i szczegóły oferty atrakcji danej firmy."""

    serializer_class = AttractionItemSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return AttractionItem.objects.none()
        return AttractionItem.objects.filter(
            restaurant_id=self.kwargs["restaurant_pk"],
            is_active=True,
        )


# ──────────────────────────────────────────────
# Reviews (Opinie)
# ──────────────────────────────────────────────

@extend_schema_view(
    list=extend_schema(tags=["Opinie"], summary="Opinie o firmie"),
    create=extend_schema(tags=["Opinie"], summary="Dodaj opinię"),
)
class ReviewViewSet(viewsets.ModelViewSet):
    """Opinie o firmie. GET — publiczny; POST — zalogowany."""

    serializer_class = ReviewSerializer
    http_method_names = ["get", "post", "head", "options"]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ["created_at", "rating"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Review.objects.none()
        return Review.objects.filter(
            restaurant_id=self.kwargs["restaurant_pk"]
        )

    def get_permissions(self):
        if self.action == "create":
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def perform_create(self, serializer):
        serializer.save(
            user=self.request.user,
            restaurant_id=self.kwargs["restaurant_pk"],
        )


# ──────────────────────────────────────────────
# Chat (BookingMessage)
# ──────────────────────────────────────────────

@extend_schema_view(
    list=extend_schema(tags=["Czat"], summary="Wiadomości w rezerwacji"),
    create=extend_schema(tags=["Czat"], summary="Wyślij wiadomość"),
)
class BookingMessageViewSet(viewsets.ModelViewSet):
    """Czat klient ↔ firma w ramach rezerwacji."""

    serializer_class = BookingMessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return BookingMessage.objects.none()
        return BookingMessage.objects.filter(
            booking_id=self.kwargs["booking_pk"]
        )

    def perform_create(self, serializer):
        serializer.save(
            sender=self.request.user,
            booking_id=self.kwargs["booking_pk"],
        )


# ──────────────────────────────────────────────
# CRM Notes (BookingNote)
# ──────────────────────────────────────────────

@extend_schema_view(
    list=extend_schema(tags=["Rezerwacje"], summary="Notatki CRM rezerwacji"),
    create=extend_schema(tags=["Rezerwacje"], summary="Dodaj notatkę CRM"),
)
class BookingNoteViewSet(viewsets.ModelViewSet):
    """Notatki CRM dla właściciela — historia kontaktów z klientem."""

    serializer_class = BookingNoteSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOfRestaurant]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return BookingNote.objects.none()
        return BookingNote.objects.filter(
            booking_id=self.kwargs["booking_pk"]
        )

    def perform_create(self, serializer):
        serializer.save(
            author=self.request.user,
            booking_id=self.kwargs["booking_pk"],
        )
