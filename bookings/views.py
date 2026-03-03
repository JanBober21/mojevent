from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.db.models import Q, Avg, Count
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta
import json

from .models import Restaurant, Booking, Review, RestaurantOwner
from .forms import BookingForm, ReviewForm, UserRegisterForm, RestaurantSearchForm, OwnerRegisterForm, RestaurantForm


# ── Strona główna ──────────────────────────────────────────────────────────────

def home(request):
    """Strona główna z wyróżnionymi restauracjami."""
    featured = Restaurant.objects.filter(is_active=True).annotate(
        avg_rating=Avg("reviews__rating")
    ).order_by("-avg_rating")[:6]

    # Build map markers JSON for restaurants with GPS coordinates
    all_restaurants = Restaurant.objects.filter(is_active=True)
    markers = []
    for r in all_restaurants:
        if r.latitude and r.longitude:
            markers.append({
                "name": r.name,
                "city": r.city,
                "lat": float(r.latitude),
                "lng": float(r.longitude),
                "price": str(r.price_per_person),
                "max_guests": r.max_guests,
                "pk": r.pk,
            })

    return render(request, "bookings/home.html", {
        "featured_restaurants": featured,
        "map_markers_json": json.dumps(markers),
    })


# ── Restauracje ────────────────────────────────────────────────────────────────

def restaurant_list(request):
    """Lista restauracji z filtrowaniem."""
    form = RestaurantSearchForm(request.GET or None)
    qs = Restaurant.objects.filter(is_active=True).annotate(avg_rating=Avg("reviews__rating"))

    if form.is_valid():
        city = form.cleaned_data.get("city")
        min_guests = form.cleaned_data.get("min_guests")
        max_price = form.cleaned_data.get("max_price")
        has_parking = form.cleaned_data.get("has_parking")
        has_garden = form.cleaned_data.get("has_garden")
        has_dance_floor = form.cleaned_data.get("has_dance_floor")

        if city:
            qs = qs.filter(city__icontains=city)
        if min_guests:
            qs = qs.filter(max_guests__gte=min_guests)
        if max_price:
            qs = qs.filter(price_per_person__lte=max_price)
        if has_parking:
            qs = qs.filter(has_parking=True)
        if has_garden:
            qs = qs.filter(has_garden=True)
        if has_dance_floor:
            qs = qs.filter(has_dance_floor=True)

    return render(request, "bookings/restaurant_list.html", {
        "restaurants": qs,
        "form": form,
    })


def restaurant_detail(request, pk):
    """Szczegóły restauracji z opiniami."""
    restaurant = get_object_or_404(Restaurant, pk=pk, is_active=True)
    reviews = restaurant.reviews.select_related("user").all()
    review_form = None

    if request.user.is_authenticated:
        existing_review = Review.objects.filter(
            user=request.user, restaurant=restaurant
        ).first()
        if not existing_review:
            review_form = ReviewForm()

    return render(request, "bookings/restaurant_detail.html", {
        "restaurant": restaurant,
        "reviews": reviews,
        "review_form": review_form,
    })


# ── Rezerwacje ─────────────────────────────────────────────────────────────────

@login_required
def booking_create(request, restaurant_pk):
    """Tworzenie nowej rezerwacji."""
    restaurant = get_object_or_404(Restaurant, pk=restaurant_pk, is_active=True)

    if request.method == "POST":
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.user = request.user
            booking.restaurant = restaurant

            if booking.guest_count > restaurant.max_guests:
                form.add_error(
                    "guest_count",
                    f"Restauracja przyjmuje maksymalnie {restaurant.max_guests} gości.",
                )
            else:
                # Sprawdź czy data jest wolna
                if Booking.objects.filter(
                    restaurant=restaurant,
                    event_date=booking.event_date,
                ).exclude(status=Booking.Status.CANCELLED).exists():
                    form.add_error(
                        "event_date",
                        "Ta data jest już zarezerwowana w tej restauracji.",
                    )
                else:
                    booking.save()
                    messages.success(
                        request,
                        f"Rezerwacja na {booking.get_event_type_display()} została złożona! "
                        f"Oczekuj na potwierdzenie.",
                    )
                    return redirect("booking_detail", pk=booking.pk)
    else:
        form = BookingForm(initial={
            "first_name": request.user.first_name,
            "last_name": request.user.last_name,
            "email": request.user.email,
        })

    return render(request, "bookings/booking_form.html", {
        "form": form,
        "restaurant": restaurant,
    })


@login_required
def booking_detail(request, pk):
    """Szczegóły rezerwacji."""
    booking = get_object_or_404(Booking, pk=pk, user=request.user)
    return render(request, "bookings/booking_detail.html", {"booking": booking})


@login_required
def booking_list(request):
    """Lista rezerwacji użytkownika."""
    bookings = Booking.objects.filter(user=request.user).select_related("restaurant")
    return render(request, "bookings/booking_list.html", {"bookings": bookings})


@login_required
def booking_cancel(request, pk):
    """Anulowanie rezerwacji."""
    booking = get_object_or_404(Booking, pk=pk, user=request.user)

    if booking.status in (Booking.Status.PENDING, Booking.Status.CONFIRMED):
        booking.status = Booking.Status.CANCELLED
        booking.save()
        messages.success(request, "Rezerwacja została anulowana.")
    else:
        messages.error(request, "Nie można anulować tej rezerwacji.")

    return redirect("booking_list")


# ── Opinie ─────────────────────────────────────────────────────────────────────

@login_required
def review_create(request, restaurant_pk):
    """Dodawanie opinii o restauracji."""
    restaurant = get_object_or_404(Restaurant, pk=restaurant_pk)

    if Review.objects.filter(user=request.user, restaurant=restaurant).exists():
        messages.warning(request, "Już dodałeś opinię o tej restauracji.")
        return redirect("restaurant_detail", pk=restaurant.pk)

    if request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.restaurant = restaurant
            review.save()
            messages.success(request, "Dziękujemy za opinię!")
            return redirect("restaurant_detail", pk=restaurant.pk)
    else:
        form = ReviewForm()

    return render(request, "bookings/review_form.html", {
        "form": form,
        "restaurant": restaurant,
    })


# ── Autoryzacja ────────────────────────────────────────────────────────────────

def register(request):
    """Rejestracja nowego użytkownika (klienta)."""
    if request.method == "POST":
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Witaj, {user.first_name}! Konto zostało utworzone.")
            return redirect("home")
    else:
        form = UserRegisterForm()
    return render(request, "bookings/register.html", {"form": form})


def owner_register(request):
    """Rejestracja właściciela restauracji."""
    if request.method == "POST":
        form = OwnerRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            RestaurantOwner.objects.create(user=user, restaurant=None)
            login(request, user)
            messages.success(request, f"Witaj, {user.first_name}! Konto właściciela zostało utworzone. Dodaj teraz swoją restaurację.")
            return redirect("owner_restaurant_create")
    else:
        form = OwnerRegisterForm()
    return render(request, "bookings/owner_register.html", {"form": form})


@login_required
def owner_restaurant_create(request):
    """Dodawanie restauracji przez właściciela."""
    try:
        owner = request.user.restaurant_owner
    except RestaurantOwner.DoesNotExist:
        messages.error(request, "Nie masz konta właściciela restauracji.")
        return redirect("home")

    if owner.restaurant:
        messages.info(request, "Masz już przypisaną restaurację. Możesz ją edytować.")
        return redirect("owner_restaurant_edit")

    if request.method == "POST":
        form = RestaurantForm(request.POST)
        if form.is_valid():
            restaurant = form.save()
            owner.restaurant = restaurant
            owner.save()
            messages.success(request, f"Restauracja '{restaurant.name}' została dodana!")
            return redirect("owner_dashboard")
    else:
        form = RestaurantForm()
    return render(request, "bookings/owner/restaurant_form.html", {"form": form, "editing": False})


@login_required
def owner_restaurant_edit(request):
    """Edycja restauracji przez właściciela."""
    try:
        owner = request.user.restaurant_owner
        restaurant = owner.restaurant
    except RestaurantOwner.DoesNotExist:
        messages.error(request, "Nie masz konta właściciela restauracji.")
        return redirect("home")

    if not restaurant:
        messages.info(request, "Najpierw dodaj swoją restaurację.")
        return redirect("owner_restaurant_create")

    if request.method == "POST":
        form = RestaurantForm(request.POST, instance=restaurant)
        if form.is_valid():
            form.save()
            messages.success(request, "Dane restauracji zostały zaktualizowane.")
            return redirect("owner_dashboard")
    else:
        form = RestaurantForm(instance=restaurant)
    return render(request, "bookings/owner/restaurant_form.html", {"form": form, "editing": True, "restaurant": restaurant})


# ── Panel właścicieli restauracji ─────────────────────────────────────────────

@login_required
def owner_dashboard(request):
    """Panel główny właściciela restauracji."""
    try:
        owner = request.user.restaurant_owner
    except RestaurantOwner.DoesNotExist:
        messages.error(request, "Nie masz konta właściciela restauracji.")
        return redirect("home")

    restaurant = owner.restaurant
    if not restaurant:
        messages.info(request, "Najpierw dodaj swoją restaurację.")
        return redirect("owner_restaurant_create")
    
    today = timezone.now().date()
    
    # Statystyki
    stats = {
        "total_bookings": Booking.objects.filter(restaurant=restaurant).count(),
        "pending_bookings": Booking.objects.filter(restaurant=restaurant, status=Booking.Status.PENDING).count(),
        "upcoming_bookings": Booking.objects.filter(
            restaurant=restaurant,
            event_date__gte=today,
            status=Booking.Status.CONFIRMED
        ).count(),
        "this_month_bookings": Booking.objects.filter(
            restaurant=restaurant,
            event_date__year=today.year,
            event_date__month=today.month
        ).count(),
    }
    
    # Najnowsze rezerwacje
    recent_bookings = Booking.objects.filter(restaurant=restaurant).order_by("-created_at")[:5]
    
    # Nadchodzące rezerwacje
    upcoming_bookings = Booking.objects.filter(
        restaurant=restaurant,
        event_date__gte=today,
        status=Booking.Status.CONFIRMED
    ).order_by("event_date")[:5]
    
    context = {
        "restaurant": restaurant,
        "stats": stats,
        "recent_bookings": recent_bookings,
        "upcoming_bookings": upcoming_bookings,
    }
    return render(request, "bookings/owner/dashboard.html", context)


@login_required
def owner_bookings(request):
    """Lista wszystkich rezerwacji właściciela restauracji."""
    try:
        owner = request.user.restaurant_owner
    except RestaurantOwner.DoesNotExist:
        return redirect("home")

    restaurant = owner.restaurant
    if not restaurant:
        return redirect("owner_restaurant_create")
    
    status_filter = request.GET.get("status", "")
    bookings = Booking.objects.filter(restaurant=restaurant)
    
    if status_filter:
        bookings = bookings.filter(status=status_filter)
    
    bookings = bookings.order_by("-event_date")
    
    context = {
        "restaurant": restaurant,
        "bookings": bookings,
        "status_filter": status_filter,
        "status_choices": Booking.Status.choices,
    }
    return render(request, "bookings/owner/bookings.html", context)


@login_required
def owner_booking_detail(request, booking_id):
    """Szczegóły rezerwacji z opcją zatwierdzania/odrzucania."""
    try:
        owner = request.user.restaurant_owner
    except RestaurantOwner.DoesNotExist:
        return redirect("home")

    restaurant = owner.restaurant
    if not restaurant:
        return redirect("owner_restaurant_create")
    
    booking = get_object_or_404(Booking, id=booking_id, restaurant=restaurant)
    
    if request.method == "POST":
        action = request.POST.get("action")
        
        if action == "confirm" and booking.status == Booking.Status.PENDING:
            booking.status = Booking.Status.CONFIRMED
            booking.save()
            messages.success(request, f"Rezerwacja #{booking.id} została potwierdzona.")
            
        elif action == "cancel" and booking.status in (Booking.Status.PENDING, Booking.Status.CONFIRMED):
            booking.status = Booking.Status.CANCELLED
            booking.save()
            messages.success(request, f"Rezerwacja #{booking.id} została anulowana.")
        
        return redirect("owner_booking_detail", booking_id=booking.id)
    
    return render(request, "bookings/owner/booking_detail.html", {
        "restaurant": restaurant,
        "booking": booking,
    })


@login_required
def owner_calendar(request):
    """Kalendarz rezerwacji restauracji."""
    try:
        owner = request.user.restaurant_owner
    except RestaurantOwner.DoesNotExist:
        messages.error(request, "Nie masz uprawnień do zarządzania restauracją.")
        return redirect("home")

    restaurant = owner.restaurant
    if not restaurant:
        return redirect("owner_restaurant_create")
    
    # Pobierz wszystkie rezerwacje (nie tylko z wybranego miesiąca)
    bookings = Booking.objects.filter(
        restaurant=restaurant,
    ).exclude(status=Booking.Status.CANCELLED).select_related('user')
    
    # JSON data for FullCalendar v6
    calendar_events = []
    for booking in bookings:
        color = {
            Booking.Status.PENDING: "#ffc107",     # żółty
            Booking.Status.CONFIRMED: "#28a745",   # zielony  
            Booking.Status.COMPLETED: "#6c757d",   # szary
        }.get(booking.status, "#dc3545")  # czerwony default
        
        calendar_events.append({
            "title": f"{booking.get_event_type_display()} ({booking.guest_count} osób)",
            "date": booking.event_date.strftime("%Y-%m-%d"),
            "backgroundColor": color,
            "url": f"/owner/booking/{booking.id}/"
        })
    
    return render(request, "bookings/owner/calendar.html", {
        "restaurant": restaurant,
        "calendar_events": json.dumps(calendar_events),
        "bookings": bookings,
    })
