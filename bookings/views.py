import json

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.db.models import Q, Avg

from .models import Restaurant, Booking, Review
from .forms import BookingForm, ReviewForm, UserRegisterForm, RestaurantSearchForm


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
    """Rejestracja nowego użytkownika."""
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
