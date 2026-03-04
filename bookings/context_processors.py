from bookings.models import RestaurantOwner


def active_firm(request):
    """Inject active firm data into every template (for navbar)."""
    if not hasattr(request, "user") or not request.user.is_authenticated:
        return {}

    memberships = RestaurantOwner.objects.filter(
        user=request.user, restaurant__isnull=False,
    ).select_related("restaurant")

    if not memberships.exists():
        return {"is_firm_member": False}

    active_id = request.session.get("active_restaurant_id")
    active_membership = memberships.filter(restaurant_id=active_id).first()

    if not active_membership:
        active_membership = memberships.first()
        if active_membership:
            request.session["active_restaurant_id"] = active_membership.restaurant_id

    return {
        "is_firm_member": True,
        "active_restaurant": active_membership.restaurant if active_membership else None,
        "active_membership": active_membership,
        "firm_memberships": memberships,
    }
