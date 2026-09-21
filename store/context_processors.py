from .models import Cart, DeliveryArea


def cart_count(request):
    count = 0
    try:
        if request.user.is_authenticated:
            cart = Cart.objects.filter(user=request.user).first()
        else:
            session_key = request.session.session_key
            cart = Cart.objects.filter(session_key=session_key).first() if session_key else None

        if cart:
            count = cart.item_count
    except Exception:
        pass
    return {'cart_count': count}


def delivery_location(request):
    """
    Exposes the currently selected delivery area from user session/profile.
    Validates that the selected DeliveryArea is still active in the database.
    """
    area = None
    pincode = request.session.get('user_pincode')
    area_id = request.session.get('delivery_area_id')

    try:
        if area_id:
            area = DeliveryArea.objects.filter(id=area_id, is_active=True).first()
        elif pincode:
            area = DeliveryArea.objects.filter(pincode=pincode, is_active=True).first()
    except Exception:
        area = None

    if area:
        label = area.display_name
        is_active = True
    elif pincode:
        label = f"Pincode: {pincode}"
        is_active = False
    else:
        label = "Select Location"
        is_active = False

    return {
        'selected_delivery_area': area,
        'user_pincode': pincode,
        'user_location_label': label,
        'location_is_active': is_active,
    }
