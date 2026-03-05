from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.db.models import Q, Avg, Count, Max
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta, date
import json
import math
import calendar as cal_module

from .models import Restaurant, Booking, Review, RestaurantOwner, BookingNote, Menu, MenuItem, BookingMenuItem, AttractionItem, BookingMessage, RestaurantImage, SavedMenu, MenuItemTemplate
from .forms import BookingForm, ReviewForm, UserRegisterForm, RestaurantSearchForm, OwnerRegisterForm, RestaurantForm, UserSettingsForm


def _get_owner_context(request):
    """Return (memberships_qs, active_restaurant, active_membership) for the current user.

    Uses session key 'active_restaurant_id' to remember which firm is selected.
    Returns (None, None, None) when the user has no firm memberships.
    """
    memberships = RestaurantOwner.objects.filter(
        user=request.user, restaurant__isnull=False,
    ).select_related("restaurant")

    if not memberships.exists():
        # User has an owner record with restaurant=None (just registered)
        if RestaurantOwner.objects.filter(user=request.user).exists():
            return memberships, None, None
        return None, None, None

    active_id = request.session.get("active_restaurant_id")
    active_membership = None

    if active_id:
        active_membership = memberships.filter(restaurant_id=active_id).first()

    if not active_membership:
        active_membership = memberships.first()
        request.session["active_restaurant_id"] = active_membership.restaurant_id

    return memberships, active_membership.restaurant, active_membership


def _haversine_km(lat1, lon1, lat2, lon2):
    """Oblicz odległość w km między dwoma punktami GPS (Haversine)."""
    R = 6371  # promień Ziemi w km
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (math.sin(d_lat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(d_lon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ── Strona główna ──────────────────────────────────────────────────────────────

def home(request):
    """Strona główna z wyróżnionymi firmami."""
    featured = Restaurant.objects.filter(is_active=True).annotate(
        avg_rating=Avg("reviews__rating")
    ).order_by("-avg_rating")[:6]

    # Build map markers JSON for firms with GPS coordinates
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
                "firm_type": r.get_firm_type_display(),
            })

    return render(request, "bookings/home.html", {
        "featured_restaurants": featured,
        "map_markers_json": json.dumps(markers),
        "restaurant_count": Restaurant.objects.filter(is_active=True).count(),
        "booking_count": Booking.objects.count(),
        "review_count": Review.objects.count(),
    })


# ── Restauracje ────────────────────────────────────────────────────────────────

def restaurant_list(request):
    """Lista firm z filtrowaniem."""
    form = RestaurantSearchForm(request.GET or None)
    qs = Restaurant.objects.filter(is_active=True).annotate(avg_rating=Avg("reviews__rating"))

    firm_type_filter = request.GET.get("firm_type", "")

    if form.is_valid():
        firm_type = form.cleaned_data.get("firm_type")
        city = form.cleaned_data.get("city")
        min_guests = form.cleaned_data.get("min_guests")
        max_price = form.cleaned_data.get("max_price")
        has_parking = form.cleaned_data.get("has_parking")
        has_garden = form.cleaned_data.get("has_garden")
        has_dance_floor = form.cleaned_data.get("has_dance_floor")
        user_lat = form.cleaned_data.get("user_lat")
        user_lng = form.cleaned_data.get("user_lng")

        if firm_type:
            qs = qs.filter(firm_type=firm_type)
            firm_type_filter = firm_type
        if city:
            qs = qs.filter(city__icontains=city)
        event_date = form.cleaned_data.get("event_date")
        if event_date:
            booked_ids = Booking.objects.filter(
                event_date=event_date,
            ).exclude(status="cancelled").values_list("restaurant_id", flat=True)
            qs = qs.exclude(pk__in=booked_ids)
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

        # Filtrowanie cateringów po promieniu dowozu
        if firm_type == "catering" and user_lat and user_lng:
            nearby_ids = []
            for r in qs:
                if r.latitude and r.longitude:
                    dist = _haversine_km(
                        float(user_lat), float(user_lng),
                        float(r.latitude), float(r.longitude),
                    )
                    if dist <= r.delivery_radius_km:
                        nearby_ids.append(r.pk)
            qs = qs.filter(pk__in=nearby_ids)

    return render(request, "bookings/restaurant_list.html", {
        "restaurants": qs,
        "form": form,
        "firm_type_filter": firm_type_filter,
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

    # Menu widoczne publicznie (tylko z aktywnego menu)
    active_menu = Menu.objects.filter(restaurant=restaurant, is_active=True).first()
    visible_menu = MenuItem.objects.filter(
        restaurant=restaurant, is_visible=True,
        menu=active_menu,
    ) if active_menu else MenuItem.objects.none()
    categories = MenuItem.Category.choices
    menu_by_category = []
    for cat_value, cat_label in categories:
        items = visible_menu.filter(category=cat_value)
        if items.exists():
            menu_by_category.append({"label": cat_label, "items": items})

    # Czy menu jest zapisane?
    is_menu_saved = False
    if request.user.is_authenticated and menu_by_category:
        is_menu_saved = SavedMenu.objects.filter(
            user=request.user, restaurant=restaurant
        ).exists()

    # Oferta atrakcji (tylko dla typu attraction)
    attraction_items = []
    if restaurant.firm_type == Restaurant.FirmType.ATTRACTION:
        from .models import AttractionItem
        tags = AttractionItem.Tag.choices
        for tag_value, tag_label in tags:
            items = AttractionItem.objects.filter(
                restaurant=restaurant, tag=tag_value, is_active=True
            )
            if items.exists():
                attraction_items.append({"label": tag_label, "items": items})

    return render(request, "bookings/restaurant_detail.html", {
        "restaurant": restaurant,
        "reviews": reviews,
        "review_form": review_form,
        "menu_by_category": menu_by_category,
        "is_menu_saved": is_menu_saved,
        "attraction_items": attraction_items,
        "gallery_images": restaurant.gallery_images.all(),
    })


# ── Rezerwacje ─────────────────────────────────────────────────────────────────

@login_required
def booking_create(request, restaurant_pk):
    """Tworzenie nowej rezerwacji."""
    restaurant = get_object_or_404(Restaurant, pk=restaurant_pk, is_active=True)
    is_attraction = restaurant.firm_type == Restaurant.FirmType.ATTRACTION

    if request.method == "POST":
        form = BookingForm(request.POST, firm_type=restaurant.firm_type)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.user = request.user
            booking.restaurant = restaurant

            guest_ok = True
            if not is_attraction and booking.guest_count and booking.guest_count > restaurant.max_guests:
                form.add_error(
                    "guest_count",
                    f"Firma przyjmuje maksymalnie {restaurant.max_guests} gości.",
                )
                guest_ok = False

            if guest_ok:
                # Sprawdź czy data jest wolna
                if Booking.objects.filter(
                    restaurant=restaurant,
                    event_date=booking.event_date,
                ).exclude(status=Booking.Status.CANCELLED).exists():
                    form.add_error(
                        "event_date",
                        "Ta data jest już zarezerwowana w tej firmie.",
                    )
                else:
                    booking.save()
                    # Auto-wyślij wiadomość powitalną od właściciela firmy
                    if restaurant.welcome_message.strip():
                        owner_qs = restaurant.owners.filter(role="owner").select_related("user")
                        if not owner_qs.exists():
                            owner_qs = restaurant.owners.select_related("user")
                        if owner_qs.exists():
                            BookingMessage.objects.create(
                                booking=booking,
                                sender=owner_qs.first().user,
                                content=restaurant.welcome_message.strip(),
                            )

                    # Catering → przekieruj do ekranu wyboru menu
                    if restaurant.firm_type == Restaurant.FirmType.CATERING:
                        _active = Menu.objects.filter(restaurant=restaurant, is_active=True).first()
                        menu_items = MenuItem.objects.filter(
                            restaurant=restaurant, is_visible=True, menu=_active,
                        ) if _active else MenuItem.objects.none()
                        if menu_items.exists():
                            messages.info(
                                request,
                                "Rezerwacja złożona! Teraz wybierz pozycje z menu cateringowego.",
                            )
                            return redirect("booking_catering_menu", pk=booking.pk)

                    label = booking.get_event_type_display() if booking.event_type else "atrakcję"
                    messages.success(
                        request,
                        f"Rezerwacja na {label} została złożona! "
                        f"Oczekuj na potwierdzenie.",
                    )
                    return redirect("booking_detail", pk=booking.pk)
    else:
        initial = {
            "first_name": request.user.first_name,
            "last_name": request.user.last_name,
            "email": request.user.email,
        }
        # Auto-fill phone from user profile
        if hasattr(request.user, "profile") and request.user.profile.phone:
            initial["phone"] = request.user.profile.phone
        form = BookingForm(
            firm_type=restaurant.firm_type,
            initial=initial,
        )

    return render(request, "bookings/booking_form.html", {
        "form": form,
        "restaurant": restaurant,
        "is_attraction": is_attraction,
    })


@login_required
def booking_detail(request, pk):
    """Szczegóły rezerwacji."""
    booking = get_object_or_404(Booking, pk=pk, user=request.user)

    if request.method == "POST" and request.POST.get("action") == "send_message":
        content = request.POST.get("message", "").strip()
        if content:
            BookingMessage.objects.create(
                booking=booking,
                sender=request.user,
                content=content,
            )
            messages.success(request, "Wiadomość wysłana.")
        return redirect("booking_detail", pk=booking.pk)

    chat_messages = booking.chat_messages.select_related("sender").all()
    return render(request, "bookings/booking_detail.html", {
        "booking": booking,
        "chat_messages": chat_messages,
    })


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
        messages.warning(request, "Już dodałeś opinię o tej firmie.")
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


# ── Login redirect ─────────────────────────────────────────────────────────────

@login_required
def login_redirect_view(request):
    """Przekieruj po logowaniu — firma → panel firmy, klient → strona główna."""
    if RestaurantOwner.objects.filter(user=request.user, restaurant__isnull=False).exists():
        return redirect("owner_dashboard")
    return redirect("home")


# ── Ustawienia konta ───────────────────────────────────────────────────────────

@login_required
def account_settings(request):
    """Ustawienia konta użytkownika — imię, nazwisko, email, telefon, miasto."""
    from .models import UserProfile
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        form = UserSettingsForm(request.POST)
        if form.is_valid():
            request.user.first_name = form.cleaned_data["first_name"]
            request.user.last_name = form.cleaned_data["last_name"]
            request.user.email = form.cleaned_data["email"]
            request.user.save()
            profile.phone = form.cleaned_data["phone"]
            profile.city = form.cleaned_data["city"]
            profile.client_type = form.cleaned_data["client_type"]
            profile.company_name = form.cleaned_data.get("company_name", "")
            profile.company_address = form.cleaned_data.get("company_address", "")
            profile.company_nip = form.cleaned_data.get("company_nip", "")
            profile.save()
            messages.success(request, "Ustawienia konta zostały zapisane.")
            next_url = request.GET.get("next", "account_settings")
            return redirect(next_url)
    else:
        form = UserSettingsForm(initial={
            "first_name": request.user.first_name,
            "last_name": request.user.last_name,
            "email": request.user.email,
            "phone": profile.phone,
            "city": profile.city or "Poznań",
            "client_type": profile.client_type or "private",
            "company_name": profile.company_name,
            "company_address": profile.company_address,
            "company_nip": profile.company_nip,
        })

    is_new_google = request.GET.get("new") == "1"
    return render(request, "bookings/account_settings.html", {
        "form": form,
        "is_new_google": is_new_google,
    })


# ── Autoryzacja ────────────────────────────────────────────────────────────────

def register(request):
    """Rejestracja nowego użytkownika (klienta)."""
    if request.method == "POST":
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Utwórz profil z telefonem i danymi firmowymi
            from .models import UserProfile
            UserProfile.objects.create(
                user=user,
                phone=form.cleaned_data.get("phone", ""),
                client_type=form.cleaned_data.get("client_type", "private"),
                company_name=form.cleaned_data.get("company_name", ""),
                company_address=form.cleaned_data.get("company_address", ""),
                company_nip=form.cleaned_data.get("company_nip", ""),
            )
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")
            messages.success(request, f"Witaj, {user.first_name}! Konto zostało utworzone.")
            return redirect("home")
    else:
        form = UserRegisterForm()
    return render(request, "bookings/register.html", {"form": form})


def owner_register(request):
    """Rejestracja właściciela firmy."""
    if request.method == "POST":
        form = OwnerRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Utwórz profil z telefonem
            from .models import UserProfile
            UserProfile.objects.create(
                user=user,
                phone=form.cleaned_data.get("phone", ""),
            )
            RestaurantOwner.objects.create(user=user, restaurant=None, role="owner")
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")
            messages.success(request, f"Witaj, {user.first_name}! Konto właściciela zostało utworzone. Dodaj teraz swoją firmę.")
            return redirect("owner_restaurant_create")
    else:
        form = OwnerRegisterForm()
    return render(request, "bookings/owner_register.html", {"form": form})


def _save_gallery_images(request, restaurant):
    """Save gallery image URLs submitted from the form."""
    # Delete images marked for removal
    delete_ids = request.POST.getlist("delete_image")
    if delete_ids:
        RestaurantImage.objects.filter(
            restaurant=restaurant, pk__in=delete_ids
        ).delete()

    # Add new image URLs
    new_urls = request.POST.getlist("new_image_url")
    new_captions = request.POST.getlist("new_image_caption")
    max_order = (
        restaurant.gallery_images.aggregate(Max("order"))["order__max"] or 0
    )
    for i, url in enumerate(new_urls):
        url = url.strip()
        if url:
            caption = new_captions[i].strip() if i < len(new_captions) else ""
            max_order += 1
            RestaurantImage.objects.create(
                restaurant=restaurant,
                image_url=url,
                caption=caption,
                order=max_order,
            )


@login_required
def owner_restaurant_create(request):
    """Dodawanie nowej firmy przez właściciela."""
    # Check user is an owner type at all
    if not RestaurantOwner.objects.filter(user=request.user).exists():
        messages.error(request, "Nie masz konta właściciela firmy.")
        return redirect("home")

    if request.method == "POST":
        form = RestaurantForm(request.POST)
        if form.is_valid():
            restaurant = form.save()
            # Create or update the placeholder membership
            placeholder = RestaurantOwner.objects.filter(
                user=request.user, restaurant__isnull=True
            ).first()
            if placeholder:
                placeholder.restaurant = restaurant
                placeholder.save()
            else:
                RestaurantOwner.objects.create(
                    user=request.user, restaurant=restaurant, role="owner"
                )
            _save_gallery_images(request, restaurant)
            request.session["active_restaurant_id"] = restaurant.pk
            messages.success(request, f"Firma '{restaurant.name}' została dodana!")
            return redirect("owner_dashboard")
    else:
        form = RestaurantForm()
    return render(request, "bookings/owner/restaurant_form.html", {"form": form, "editing": False})


@login_required
def owner_restaurant_edit(request):
    """Edycja aktywnej firmy."""
    memberships, restaurant, membership = _get_owner_context(request)
    if memberships is None:
        messages.error(request, "Nie masz konta właściciela firmy.")
        return redirect("home")
    if not restaurant:
        messages.info(request, "Najpierw dodaj swoją firmę.")
        return redirect("owner_restaurant_create")

    if request.method == "POST":
        form = RestaurantForm(request.POST, instance=restaurant)
        if form.is_valid():
            form.save()
            _save_gallery_images(request, restaurant)
            messages.success(request, "Dane firmy zostały zaktualizowane.")
            return redirect("owner_dashboard")
    else:
        form = RestaurantForm(instance=restaurant)
    return render(request, "bookings/owner/restaurant_form.html", {
        "form": form, "editing": True, "restaurant": restaurant,
        "gallery_images": restaurant.gallery_images.all(),
    })


# ── Panel właścicieli restauracji ─────────────────────────────────────────────

@login_required
def owner_dashboard(request):
    """Panel główny właściciela firmy."""
    memberships, restaurant, membership = _get_owner_context(request)
    if memberships is None:
        messages.error(request, "Nie masz konta właściciela firmy.")
        return redirect("home")
    if not restaurant:
        messages.info(request, "Najpierw dodaj swoją firmę.")
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
    memberships, restaurant, membership = _get_owner_context(request)
    if memberships is None:
        return redirect("home")
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
    memberships, restaurant, membership = _get_owner_context(request)
    if memberships is None:
        return redirect("home")
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

        elif action == "add_note":
            note_date = request.POST.get("note_date")
            note_title = request.POST.get("note_title", "").strip()
            note_content = request.POST.get("note_content", "").strip()
            if note_date and note_title and note_content:
                BookingNote.objects.create(
                    booking=booking,
                    author=request.user,
                    date=note_date,
                    title=note_title,
                    content=note_content,
                )
                messages.success(request, "Notatka została dodana.")
            else:
                messages.error(request, "Wypełnij wszystkie pola notatki.")

        elif action == "delete_note":
            note_id = request.POST.get("note_id")
            BookingNote.objects.filter(id=note_id, booking=booking).delete()
            messages.success(request, "Notatka została usunięta.")
        elif action == "send_message":
            content = request.POST.get("message", "").strip()
            if content:
                BookingMessage.objects.create(
                    booking=booking,
                    sender=request.user,
                    content=content,
                )
                messages.success(request, "Wiadomość wysłana.")

        elif action == "close_deal":
            agreed_price = request.POST.get("deal_agreed_price", "").strip()
            deal_terms = request.POST.get("deal_terms", "").strip()
            if agreed_price:
                try:
                    from decimal import Decimal
                    booking.deal_agreed_price = Decimal(agreed_price)
                    booking.deal_terms = deal_terms
                    booking.deal_closed_at = timezone.now()
                    booking.status = Booking.Status.CONFIRMED
                    booking.save()
                    messages.success(request, "Deal zamknięty! Umowa została wygenerowana.")
                    return redirect("owner_booking_agreement", booking_id=booking.id)
                except Exception:
                    messages.error(request, "Nieprawidłowa cena.")
            else:
                messages.error(request, "Podaj uzgodnioną cenę.")

        elif action == "reopen_deal":
            booking.deal_closed_at = None
            booking.deal_agreed_price = None
            booking.deal_terms = ""
            booking.save()
            messages.success(request, "Deal został otwarty ponownie.")
        
        return redirect("owner_booking_detail", booking_id=booking.id)

    notes = booking.crm_notes.all()
    chat_messages = booking.chat_messages.select_related("sender").all()
    today = timezone.now().date().isoformat()
    
    return render(request, "bookings/owner/booking_detail.html", {
        "restaurant": restaurant,
        "booking": booking,
        "notes": notes,
        "chat_messages": chat_messages,
        "today": today,
    })


@login_required
def owner_booking_agreement(request, booking_id):
    """Wyświetlenie umowy / potwierdzenia dealu — do druku / PDF."""
    memberships, restaurant, membership = _get_owner_context(request)
    if memberships is None:
        return redirect("home")
    if not restaurant:
        return redirect("owner_restaurant_create")

    booking = get_object_or_404(Booking, id=booking_id, restaurant=restaurant)

    if not booking.deal_closed_at:
        messages.error(request, "Deal nie został jeszcze zamknięty.")
        return redirect("owner_booking_detail", booking_id=booking.id)

    menu_selections = booking.menu_selections.select_related("menu_item").all()
    menu_total = sum(s.subtotal for s in menu_selections)

    return render(request, "bookings/owner/agreement.html", {
        "restaurant": restaurant,
        "booking": booking,
        "menu_selections": menu_selections,
        "menu_total": menu_total,
    })


@login_required
def owner_calendar(request):
    """Kalendarz rezerwacji restauracji — widok miesięczny."""
    memberships, restaurant, membership = _get_owner_context(request)
    if memberships is None:
        messages.error(request, "Nie masz uprawnień do zarządzania firmą.")
        return redirect("home")
    if not restaurant:
        return redirect("owner_restaurant_create")

    # Obsługa nawigacji miesięcy
    today = timezone.now().date()
    try:
        year = int(request.GET.get("year", today.year))
        month = int(request.GET.get("month", today.month))
        if month < 1 or month > 12:
            raise ValueError
    except (ValueError, TypeError):
        year, month = today.year, today.month

    # Poprzedni / następny miesiąc
    if month == 1:
        prev_month, prev_year = 12, year - 1
    else:
        prev_month, prev_year = month - 1, year
    if month == 12:
        next_month, next_year = 1, year + 1
    else:
        next_month, next_year = month + 1, year

    # Polska nazwa miesiąca
    MONTH_NAMES_PL = [
        "", "Styczeń", "Luty", "Marzec", "Kwiecień", "Maj", "Czerwiec",
        "Lipiec", "Sierpień", "Wrzesień", "Październik", "Listopad", "Grudzień",
    ]
    month_name = MONTH_NAMES_PL[month]

    # Rezerwacje w tym miesiącu
    bookings = Booking.objects.filter(
        restaurant=restaurant,
        event_date__year=year,
        event_date__month=month,
    ).exclude(status=Booking.Status.CANCELLED).select_related('user')

    # Mapuj rezerwacje na dni
    bookings_by_day = {}
    for b in bookings:
        day = b.event_date.day
        if day not in bookings_by_day:
            bookings_by_day[day] = []
        bookings_by_day[day].append({
            "id": b.id,
            "type_display": b.get_event_type_display(),
            "guest_count": b.guest_count,
            "status": b.status,
            "client": f"{b.first_name} {b.last_name}",
        })

    # Buduj siatkę kalendarza (poniedziałek = 0)
    first_weekday, days_in_month = cal_module.monthrange(year, month)
    calendar_days = []

    # Puste komórki przed pierwszym dniem
    for _ in range(first_weekday):
        calendar_days.append({"day": 0, "events": [], "is_today": False})

    # Dni miesiąca
    for day in range(1, days_in_month + 1):
        is_today = (year == today.year and month == today.month and day == today.day)
        calendar_days.append({
            "day": day,
            "events": bookings_by_day.get(day, []),
            "is_today": is_today,
        })

    # Statystyki miesiąca
    month_stats = {
        "total": bookings.count(),
        "confirmed": bookings.filter(status=Booking.Status.CONFIRMED).count(),
        "pending": bookings.filter(status=Booking.Status.PENDING).count(),
        "total_guests": sum(b.guest_count or 0 for b in bookings),
    }

    return render(request, "bookings/owner/calendar.html", {
        "restaurant": restaurant,
        "calendar_days": calendar_days,
        "year": year,
        "month": month,
        "month_name": month_name,
        "prev_month": prev_month,
        "prev_year": prev_year,
        "next_month": next_month,
        "next_year": next_year,
        "month_stats": month_stats,
    })


# ── Menu restauracji (panel właściciela) ──────────────────────────────────────────

@login_required
def owner_menu(request):
    """Zarządzanie menu restauracji (wiele menu)."""
    memberships, restaurant, membership = _get_owner_context(request)
    if memberships is None:
        return redirect("home")
    if not restaurant:
        return redirect("owner_restaurant_create")

    def _upsert_template(category, name, price):
        """Zapisz / zaktualizuj pozycje w globalnym katalogu podpowiedzi."""
        try:
            tpl, created = MenuItemTemplate.objects.get_or_create(
                category=category, name=name,
                defaults={"last_price": price},
            )
            if not created:
                tpl.last_price = price
                tpl.usage_count = tpl.usage_count + 1
                tpl.save(update_fields=["last_price", "usage_count", "updated_at"])
        except Exception:
            pass

    def _touch_menu(menu_obj):
        """Zaznacz kto ostatnio edytował menu."""
        menu_obj.last_edited_by = request.user
        menu_obj.save(update_fields=["last_edited_by", "last_edited_at"])

    # --- Pobierz / utwórz bieżące menu ---
    all_menus = Menu.objects.filter(restaurant=restaurant).annotate(
        item_count=Count("items"),
    ).select_related("last_edited_by")

    # Wybrane menu (z GET param lub aktywne)
    selected_menu_id = request.GET.get("menu_id") or request.POST.get("menu_id")
    current_menu = None
    if selected_menu_id:
        current_menu = all_menus.filter(id=selected_menu_id).first()
    if not current_menu:
        current_menu = all_menus.filter(is_active=True).first()
    if not current_menu:
        # Brak żadnego menu — utwórz domyślne
        current_menu = Menu.objects.create(
            restaurant=restaurant,
            name="Menu główne",
            is_active=True,
            last_edited_by=request.user,
        )
        all_menus = Menu.objects.filter(restaurant=restaurant).annotate(
            item_count=Count("items"),
        ).select_related("last_edited_by")

    if request.method == "POST":
        action = request.POST.get("action")

        # ── Nowe menu ──
        if action == "create_menu":
            menu_name = request.POST.get("menu_name", "").strip()
            if menu_name:
                new_menu = Menu.objects.create(
                    restaurant=restaurant,
                    name=menu_name,
                    last_edited_by=request.user,
                )
                messages.success(request, f'Utworzono menu "{menu_name}".')
                return redirect(f"{request.path}?menu_id={new_menu.id}")
            else:
                messages.error(request, "Podaj nazwę menu.")
                return redirect(request.get_full_path())

        # ── Ustaw jako aktualne ──
        elif action == "set_active":
            Menu.objects.filter(restaurant=restaurant).update(is_active=False)
            current_menu.is_active = True
            current_menu.save(update_fields=["is_active"])
            messages.success(request, f'Menu "{current_menu.name}" jest teraz aktualnym menu.')
            return redirect(f"{request.path}?menu_id={current_menu.id}")

        # ── Zmień nazwę menu ──
        elif action == "rename_menu":
            new_name = request.POST.get("menu_name", "").strip()
            if new_name:
                current_menu.name = new_name
                current_menu.save(update_fields=["name"])
                _touch_menu(current_menu)
                messages.success(request, "Zmieniono nazwę menu.")
            return redirect(f"{request.path}?menu_id={current_menu.id}")

        # ── Usuń menu ──
        elif action == "delete_menu":
            if current_menu.is_active:
                messages.error(request, "Nie można usunąć aktualnego menu. Najpierw ustaw inne menu jako aktualne.")
            else:
                name = current_menu.name
                current_menu.delete()
                messages.success(request, f'Usunięto menu "{name}".')
            return redirect("owner_menu")

        # ── Dodaj pozycję ──
        elif action == "add":
            category = request.POST.get("category", "")
            name = request.POST.get("name", "").strip()
            description = request.POST.get("description", "").strip()
            price = request.POST.get("price", "0")
            is_visible = request.POST.get("is_visible") == "on"
            if name and category:
                try:
                    MenuItem.objects.create(
                        restaurant=restaurant,
                        menu=current_menu,
                        category=category,
                        name=name,
                        description=description,
                        price=price,
                        is_visible=is_visible,
                    )
                    _upsert_template(category, name, price)
                    _touch_menu(current_menu)
                    messages.success(request, f"Dodano: {name}")
                except Exception:
                    messages.error(request, "Błąd przy dodawaniu pozycji.")
            else:
                messages.error(request, "Podaj nazwę i kategorię.")
            return redirect(f"{request.path}?menu_id={current_menu.id}")

        # ── Edytuj pozycję ──
        elif action == "edit":
            item_id = request.POST.get("item_id")
            item = MenuItem.objects.filter(id=item_id, restaurant=restaurant).first()
            if item:
                item.category = request.POST.get("category", item.category)
                item.name = request.POST.get("name", item.name).strip()
                item.description = request.POST.get("description", "").strip()
                item.price = request.POST.get("price", item.price)
                item.is_visible = request.POST.get("is_visible") == "on"
                item.save()
                _upsert_template(item.category, item.name, item.price)
                _touch_menu(current_menu)
                messages.success(request, f"Zaktualizowano: {item.name}")
            return redirect(f"{request.path}?menu_id={current_menu.id}")

        # ── Usuń pozycję ──
        elif action == "delete":
            item_id = request.POST.get("item_id")
            MenuItem.objects.filter(id=item_id, restaurant=restaurant).delete()
            _touch_menu(current_menu)
            messages.success(request, "Pozycja usunięta.")
            return redirect(f"{request.path}?menu_id={current_menu.id}")

        return redirect(f"{request.path}?menu_id={current_menu.id}")

    # Grupuj pozycje wg kategorii — tylko z bieżącego menu
    categories = MenuItem.Category.choices
    menu_by_category = []
    for cat_value, cat_label in categories:
        items = MenuItem.objects.filter(
            restaurant=restaurant, menu=current_menu, category=cat_value,
        )
        menu_by_category.append({
            "value": cat_value,
            "label": cat_label,
            "items": items,
            "count": items.count(),
        })

    return render(request, "bookings/owner/menu.html", {
        "restaurant": restaurant,
        "menu_by_category": menu_by_category,
        "categories": categories,
        "all_menus": all_menus,
        "current_menu": current_menu,
    })


# ── Wybór menu przez klienta ────────────────────────────────────────────────

@login_required
def booking_menu_select(request, pk):
    """Wybór/edycja menu przez klienta po rezerwacji."""
    booking = get_object_or_404(Booking, pk=pk, user=request.user)
    restaurant = booking.restaurant
    active_menu = Menu.objects.filter(restaurant=restaurant, is_active=True).first()
    menu_items = MenuItem.objects.filter(
        restaurant=restaurant, is_visible=True, menu=active_menu,
    ) if active_menu else MenuItem.objects.none()

    if not menu_items.exists():
        messages.info(request, "Ta firma nie udostępniła jeszcze menu.")
        return redirect("booking_detail", pk=pk)

    if request.method == "POST":
        # Zbierz obecne wybory, żeby porównać z nowymi
        old_selections = {s.menu_item_id: s.quantity for s in booking.menu_selections.all()}

        # Usuń stare wybory
        booking.menu_selections.all().delete()

        new_selections = []
        for item in menu_items:
            qty_str = request.POST.get(f"qty_{item.id}", "0")
            try:
                qty = int(qty_str)
            except ValueError:
                qty = 0
            if qty > 0:
                BookingMenuItem.objects.create(
                    booking=booking,
                    menu_item=item,
                    quantity=qty,
                )
                new_selections.append(f"{item.name} x{qty}")

        # Loguj w CRM
        if new_selections:
            changes_text = "\n".join(new_selections)
            note_title = "Zmiana wyboru menu" if old_selections else "Wybór menu"
            BookingNote.objects.create(
                booking=booking,
                author=request.user,
                date=timezone.now().date(),
                title=note_title,
                content=f"Klient zaktualizował wybór menu:\n{changes_text}",
            )
            messages.success(request, "Menu zostało zapisane.")
        else:
            if old_selections:
                BookingNote.objects.create(
                    booking=booking,
                    author=request.user,
                    date=timezone.now().date(),
                    title="Usunięcie wyboru menu",
                    content="Klient usunął wszystkie pozycje z menu.",
                )
            messages.info(request, "Nie wybrano żadnych pozycji menu.")

        return redirect("booking_detail", pk=pk)

    # Przygotuj dane z aktualnymi wyborami
    current_selections = {s.menu_item_id: s.quantity for s in booking.menu_selections.all()}
    categories = MenuItem.Category.choices
    menu_by_category = []
    for cat_value, cat_label in categories:
        items = menu_items.filter(category=cat_value)
        items_with_qty = []
        for item in items:
            items_with_qty.append({
                "item": item,
                "qty": current_selections.get(item.id, 0),
            })
        if items_with_qty:
            menu_by_category.append({
                "label": cat_label,
                "items": items_with_qty,
            })

    return render(request, "bookings/booking_menu.html", {
        "booking": booking,
        "restaurant": restaurant,
        "menu_by_category": menu_by_category,
    })


@login_required
def booking_catering_menu(request, pk):
    """Ekran wyboru menu cateringowego — wyświetlany po złożeniu rezerwacji na catering."""
    booking = get_object_or_404(Booking, pk=pk, user=request.user)
    restaurant = booking.restaurant

    if restaurant.firm_type != Restaurant.FirmType.CATERING:
        return redirect("booking_detail", pk=pk)

    active_menu = Menu.objects.filter(restaurant=restaurant, is_active=True).first()
    menu_items = MenuItem.objects.filter(
        restaurant=restaurant, is_visible=True, menu=active_menu,
    ) if active_menu else MenuItem.objects.none()

    if request.method == "POST":
        # Zapisz wybory menu
        booking.menu_selections.all().delete()

        new_selections = []
        for item in menu_items:
            qty_str = request.POST.get(f"qty_{item.id}", "0")
            try:
                qty = int(qty_str)
            except ValueError:
                qty = 0
            if qty > 0:
                BookingMenuItem.objects.create(
                    booking=booking,
                    menu_item=item,
                    quantity=qty,
                )
                new_selections.append(f"{item.name} x{qty}")

        if new_selections:
            changes_text = "\n".join(new_selections)
            BookingNote.objects.create(
                booking=booking,
                author=request.user,
                date=timezone.now().date(),
                title="Wybór menu cateringowego",
                content=f"Klient wybrał pozycje z menu:\n{changes_text}",
            )
            messages.success(request, "Menu cateringowe zostało zapisane! Rezerwacja złożona.")
        else:
            messages.success(request, "Rezerwacja złożona bez wyboru menu.")

        return redirect("booking_detail", pk=pk)

    # Przygotuj dane menu pogrupowane po kategoriach
    current_selections = {s.menu_item_id: s.quantity for s in booking.menu_selections.all()}
    categories = MenuItem.Category.choices
    menu_by_category = []
    for cat_value, cat_label in categories:
        items = menu_items.filter(category=cat_value)
        items_with_qty = []
        for item in items:
            items_with_qty.append({
                "item": item,
                "qty": current_selections.get(item.id, 0),
            })
        if items_with_qty:
            menu_by_category.append({
                "label": cat_label,
                "items": items_with_qty,
            })

    return render(request, "bookings/booking_catering_menu.html", {
        "booking": booking,
        "restaurant": restaurant,
        "menu_by_category": menu_by_category,
    })


# ── Oferta atrakcji ─────────────────────────────────────────────────────────

@login_required
def owner_attractions(request):
    """Zarządzanie ofertą atrakcji."""
    memberships, restaurant, membership = _get_owner_context(request)
    if memberships is None:
        return redirect("home")
    if not restaurant:
        return redirect("owner_restaurant_create")

    if restaurant.firm_type != Restaurant.FirmType.ATTRACTION:
        messages.error(request, "Ta zakładka jest dostępna tylko dla firm typu Atrakcje.")
        return redirect("owner_dashboard")

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "add":
            name = request.POST.get("name", "").strip()
            description = request.POST.get("description", "").strip()
            image_url = request.POST.get("image_url", "").strip()
            price = request.POST.get("price", "0")
            tag = request.POST.get("tag", "")
            if name and tag:
                try:
                    AttractionItem.objects.create(
                        restaurant=restaurant,
                        name=name,
                        description=description,
                        image_url=image_url,
                        price=price,
                        tag=tag,
                    )
                    messages.success(request, f"Dodano: {name}")
                except Exception:
                    messages.error(request, "Błąd przy dodawaniu pozycji.")
            else:
                messages.error(request, "Podaj nazwę i tag.")

        elif action == "edit":
            item_id = request.POST.get("item_id")
            item = AttractionItem.objects.filter(id=item_id, restaurant=restaurant).first()
            if item:
                item.name = request.POST.get("name", item.name).strip()
                item.description = request.POST.get("description", "").strip()
                item.image_url = request.POST.get("image_url", "").strip()
                item.price = request.POST.get("price", item.price)
                item.tag = request.POST.get("tag", item.tag)
                item.is_active = request.POST.get("is_active") == "on"
                item.save()
                messages.success(request, f"Zaktualizowano: {item.name}")

        elif action == "delete":
            item_id = request.POST.get("item_id")
            AttractionItem.objects.filter(id=item_id, restaurant=restaurant).delete()
            messages.success(request, "Pozycja usunięta.")

        return redirect("owner_attractions")

    tags = AttractionItem.Tag.choices
    items_by_tag = []
    for tag_value, tag_label in tags:
        items = AttractionItem.objects.filter(restaurant=restaurant, tag=tag_value)
        items_by_tag.append({
            "value": tag_value,
            "label": tag_label,
            "items": items,
            "count": items.count(),
        })

    return render(request, "bookings/owner/attractions.html", {
        "restaurant": restaurant,
        "items_by_tag": items_by_tag,
        "tags": tags,
    })


# ── Zarządzanie firmami (multi-firma) ──────────────────────────────────────────

@login_required
def owner_firms(request):
    """Lista firm użytkownika, przełączanie aktywnej firmy, zarządzanie pracownikami."""
    if not RestaurantOwner.objects.filter(user=request.user).exists():
        messages.error(request, "Nie masz konta właściciela firmy.")
        return redirect("home")

    memberships = RestaurantOwner.objects.filter(
        user=request.user, restaurant__isnull=False,
    ).select_related("restaurant")

    active_id = request.session.get("active_restaurant_id")

    # Handle POST actions
    if request.method == "POST":
        action = request.POST.get("action")

        if action == "switch":
            new_id = request.POST.get("restaurant_id")
            if memberships.filter(restaurant_id=new_id).exists():
                request.session["active_restaurant_id"] = int(new_id)
                messages.success(request, "Przełączono aktywną firmę.")
            return redirect("owner_firms")

        elif action == "remove_worker":
            worker_id = request.POST.get("membership_id")
            # Only owners can remove workers
            membership_to_delete = RestaurantOwner.objects.filter(
                id=worker_id, role="worker",
            ).first()
            if membership_to_delete:
                # Verify current user is owner of that restaurant
                is_owner = RestaurantOwner.objects.filter(
                    user=request.user,
                    restaurant=membership_to_delete.restaurant,
                    role="owner",
                ).exists()
                if is_owner:
                    membership_to_delete.delete()
                    messages.success(request, "Pracownik usunięty z firmy.")
            return redirect("owner_firms")

        elif action == "add_worker":
            restaurant_id = request.POST.get("restaurant_id")
            worker_username = request.POST.get("worker_username", "").strip()
            # Verify user is owner of this restaurant
            is_owner = RestaurantOwner.objects.filter(
                user=request.user, restaurant_id=restaurant_id, role="owner",
            ).exists()
            if is_owner and worker_username:
                from django.contrib.auth.models import User as UserModel
                try:
                    worker_user = UserModel.objects.get(username=worker_username)
                    _, created = RestaurantOwner.objects.get_or_create(
                        user=worker_user,
                        restaurant_id=restaurant_id,
                        defaults={"role": "worker"},
                    )
                    if created:
                        messages.success(request, f"Dodano pracownika: {worker_user.get_full_name() or worker_username}")
                    else:
                        messages.info(request, "Ten użytkownik jest już członkiem firmy.")
                except UserModel.DoesNotExist:
                    messages.error(request, f"Nie znaleziono użytkownika: {worker_username}")
            return redirect("owner_firms")

    # Build context: list of firms with their workers
    firms_data = []
    for m in memberships:
        all_members = RestaurantOwner.objects.filter(
            restaurant=m.restaurant,
        ).select_related("user")
        firms_data.append({
            "membership": m,
            "restaurant": m.restaurant,
            "is_active": m.restaurant_id == active_id,
            "is_owner": m.role == "owner",
            "members": all_members,
        })

    return render(request, "bookings/owner/firms.html", {
        "firms_data": firms_data,
        "active_id": active_id,
    })


@login_required
def owner_switch_firm(request, restaurant_id):
    """Quick switch active firm (GET-based for navbar dropdown)."""
    membership = RestaurantOwner.objects.filter(
        user=request.user, restaurant_id=restaurant_id,
    ).first()
    if membership:
        request.session["active_restaurant_id"] = restaurant_id
    return redirect(request.GET.get("next", "owner_dashboard"))


# ── API podpowiedzi menu ──────────────────────────────────────────────────────

@login_required
def menu_suggestions_api(request):
    """Zwraca JSON z podpowiedziami pozycji menu (autocomplete)."""
    q = request.GET.get("q", "").strip()
    category = request.GET.get("category", "").strip()

    qs = MenuItemTemplate.objects.all()
    if category:
        qs = qs.filter(category=category)
    if q:
        qs = qs.filter(name__icontains=q)

    results = list(
        qs.values("name", "category", "last_price")[:20]
    )
    # Konwertuj Decimal na float dla JSON
    for r in results:
        r["last_price"] = float(r["last_price"])
    return JsonResponse(results, safe=False)


# ── Zapisane menu ──────────────────────────────────────────────────────────────

@login_required
def toggle_save_menu(request, restaurant_pk):
    """Zapisz / usuń menu restauracji z ulubionych."""
    restaurant = get_object_or_404(Restaurant, pk=restaurant_pk, is_active=True)
    saved, created = SavedMenu.objects.get_or_create(
        user=request.user, restaurant=restaurant,
    )
    if not created:
        saved.delete()
        messages.info(request, "Usunięto menu z zapisanych.")
    else:
        messages.success(request, "Zapisano menu!")
    next_url = request.GET.get("next")
    if next_url:
        return redirect(next_url)
    return redirect("restaurant_detail", pk=restaurant_pk)


@login_required
def saved_menus_list(request):
    """Lista zapisanych menu użytkownika."""
    saved = SavedMenu.objects.filter(user=request.user).select_related(
        "restaurant"
    )
    # Wczytaj menu dla każdej firmy
    entries = []
    for s in saved:
        visible_menu = MenuItem.objects.filter(
            restaurant=s.restaurant, is_visible=True
        )
        categories = MenuItem.Category.choices
        menu_by_category = []
        for cat_value, cat_label in categories:
            items = visible_menu.filter(category=cat_value)
            if items.exists():
                menu_by_category.append({"label": cat_label, "items": items})
        entries.append({
            "saved": s,
            "restaurant": s.restaurant,
            "menu_by_category": menu_by_category,
        })
    return render(request, "bookings/saved_menus.html", {
        "entries": entries,
    })
