import json
import logging
from datetime import date, timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import CustomerAddressForm, ProductForm
from .models import (
    Cart,
    CartItem,
    Category,
    Coupon,
    CustomerAddress,
    DeliveryArea,
    DeliverySlot,
    Order,
    OrderItem,
    OrderStatusHistory,
    Product,
    Recipe,
    UserProfile,
    VendorOrder,
    VendorProfile,
    Wishlist,
)
from .payment_utils import create_razorpay_order, verify_razorpay_payment
from .services.geocoding import (
    clean_pincode,
    check_pincode_serviceability,
    reverse_geocode as service_reverse_geocode,
)

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def get_or_create_cart(request):
    """Get or create a cart for the current user or session."""
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        # Merge session cart if exists
        if request.session.session_key:
            session_cart = Cart.objects.filter(session_key=request.session.session_key).first()
            if session_cart and session_cart != cart:
                for item in session_cart.items.all():
                    existing = cart.items.filter(product=item.product).first()
                    if existing:
                        existing.quantity += item.quantity
                        existing.save()
                    else:
                        item.cart = cart
                        item.save()
                session_cart.delete()
        return cart
    else:
        if not request.session.session_key:
            request.session.create()
        cart, _ = Cart.objects.get_or_create(session_key=request.session.session_key)
        return cart


# ─────────────────────────────────────────────
# Home
# ─────────────────────────────────────────────

def home(request):
    if check_location(request):
        return redirect('select_location')
    now = timezone.now()
    categories = Category.objects.all()[:6]
    all_categories = Category.objects.all()
    featured_products = get_location_filtered_products(
        request,
        Product.objects.filter(is_featured=True, stock__gt=0, is_active=True)
    )[:8]
    deals_products = get_location_filtered_products(
        request,
        Product.objects.filter(discount_price__isnull=False, stock__gt=0, is_active=True)
    )[:8]
    fresh_today = get_location_filtered_products(
        request,
        Product.objects.filter(stock__gt=0, is_active=True).order_by('-created_at')
    )[:8]
    local_vendors = VendorProfile.objects.filter(status='approved').select_related('user')[:6]
    active_coupons = Coupon.objects.filter(
        is_active=True,
        valid_from__lte=now,
        valid_to__gte=now,
    )
    featured_recipes = Recipe.objects.all()[:6]
    
    wishlist_ids = []
    if request.user.is_authenticated:
        wishlist_ids = list(Wishlist.objects.filter(user=request.user).values_list('product_id', flat=True))

    return render(request, 'home.html', {
        'categories': categories,
        'all_categories': all_categories,
        'featured_products': featured_products,
        'deals_products': deals_products,
        'fresh_today': fresh_today,
        'local_vendors': local_vendors,
        'active_coupons': active_coupons,
        'featured_recipes': featured_recipes,
        'wishlist_ids': wishlist_ids,
    })



# ─────────────────────────────────────────────
# Products
# ─────────────────────────────────────────────

def product_list(request, slug=None):
    if check_location(request):
        return redirect('select_location')
    products = get_location_filtered_products(request, Product.objects.filter(stock__gt=0, is_active=True))
    current_category = None

    if slug:
        current_category = get_object_or_404(Category, slug=slug)
        products = products.filter(category=current_category)

    # Search
    q = request.GET.get('q', '')
    if q:
        products = products.filter(Q(name__icontains=q) | Q(description__icontains=q))

    # Sort
    sort = request.GET.get('sort', '')
    if sort == 'price_asc':
        products = products.order_by('price')
    elif sort == 'price_desc':
        products = products.order_by('-price')
    elif sort == 'name':
        products = products.order_by('name')

    categories = Category.objects.all()
    wishlist_ids = []
    if request.user.is_authenticated:
        wishlist_ids = list(Wishlist.objects.filter(user=request.user).values_list('product_id', flat=True))

    return render(request, 'store/product_list.html', {
        'products': products,
        'categories': categories,
        'current_category': current_category,
        'query': q,
        'sort': sort,
        'wishlist_ids': wishlist_ids,
    })


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    related = Product.objects.filter(category=product.category, is_active=True).exclude(id=product.id)[:4]

    # Check vendor delivery serviceability for user's selected location
    pincode = request.session.get('user_pincode')
    area_id = request.session.get('delivery_area_id')
    selected_area = None
    if area_id:
        selected_area = DeliveryArea.objects.filter(id=area_id, is_active=True).first()
    elif pincode:
        selected_area = DeliveryArea.objects.filter(pincode=pincode, is_active=True).first()

    is_serviceable = True
    vendor_service_message = None
    if selected_area and product.vendor:
        vp = getattr(product.vendor, 'vendor_profile', None)
        if vp:
            has_area_vendors = VendorProfile.objects.filter(service_areas=selected_area, status='approved').exists()
            serves = (
                vp.service_areas.filter(id=selected_area.id, is_active=True).exists() or
                vp.pincode == selected_area.pincode or
                (vp.assigned_area and selected_area.pincode in vp.assigned_area) or
                not has_area_vendors
            )
            if not serves:
                is_serviceable = False
                vendor_service_message = f"Vendor '{vp.shop_name}' cannot deliver to {selected_area.display_name}."

    return render(request, 'store/product_detail.html', {
        'product': product,
        'related': related,
        'selected_area': selected_area,
        'is_serviceable': is_serviceable,
        'vendor_service_message': vendor_service_message,
    })



# ─────────────────────────────────────────────
# Auth helpers
# ─────────────────────────────────────────────

def get_or_create_profile(user):
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile


def check_location(request):
    if request.user.is_authenticated:
        profile = get_or_create_profile(request.user)
        if profile.role == 'customer' and not request.session.get('user_pincode'):
            return True
    return False



def check_and_send_low_stock_alert(product):
    if product.is_low_stock:
        from django.core.mail import send_mail
        from django.contrib.auth.models import User
        
        subject = f"⚠️ Low Stock Alert: {product.name}"
        message = (
            f"Hello,\n\n"
            f"This is an automated warning that the product '{product.name}' in your inventory is running low.\n\n"
            f"Current Stock: {product.stock}\n"
            f"Low Stock Threshold: {product.low_stock_threshold}\n\n"
            f"Please update the stock count as soon as possible to ensure order availability.\n\n"
            f"Best regards,\n"
            f"FoodBasket Systems"
        )
        
        recipients = []
        if product.vendor and product.vendor.email:
            recipients.append(product.vendor.email)
            
        superadmins = User.objects.filter(is_superuser=True)
        for sa in superadmins:
            if sa.email and sa.email not in recipients:
                recipients.append(sa.email)
                
        if recipients:
            try:
                send_mail(subject, message, 'noreply@foodbasket.com', recipients, fail_silently=True)
            except Exception:
                pass



# ─────────────────────────────────────────────
# Cart
# ─────────────────────────────────────────────

@login_required
def cart_view(request):
    from django.utils import timezone as tz
    now = tz.now()
    cart = get_or_create_cart(request)
    cart_items = cart.items.select_related('product', 'product__vendor', 'product__vendor__vendor_profile').all()

    pincode = request.session.get('user_pincode')
    area_id = request.session.get('delivery_area_id')
    selected_area = None
    if area_id:
        selected_area = DeliveryArea.objects.filter(id=area_id, is_active=True).first()
    elif pincode:
        selected_area = DeliveryArea.objects.filter(pincode=pincode, is_active=True).first()

    has_unserviceable_items = False
    for item in cart_items:
        item.is_serviceable = True
        item.unserviceable_reason = None
        if selected_area and item.product.vendor:
            vp = getattr(item.product.vendor, 'vendor_profile', None)
            if vp:
                has_area_vendors = VendorProfile.objects.filter(service_areas=selected_area, status='approved').exists()
                serves = (
                    vp.service_areas.filter(id=selected_area.id, is_active=True).exists() or
                    vp.pincode == selected_area.pincode or
                    (vp.assigned_area and selected_area.pincode in vp.assigned_area) or
                    not has_area_vendors
                )
                if not serves:
                    item.is_serviceable = False
                    item.unserviceable_reason = f"Vendor '{vp.shop_name}' cannot deliver to {selected_area.display_name}."
                    has_unserviceable_items = True

    # Recipe recommendations based on cart tags
    cart_tags = set()
    for item in cart_items:
        cart_tags.update(item.product.get_tags())

    recipes = []
    if cart_tags:
        for recipe in Recipe.objects.all():
            if set(recipe.get_ingredient_tags()) & cart_tags:
                recipes.append(recipe)

    # Active coupons for hints
    active_coupons = Coupon.objects.filter(
        is_active=True,
        valid_from__lte=now,
        valid_to__gte=now,
    )[:5]

    return render(request, 'store/cart.html', {
        'cart': cart,
        'cart_items': cart_items,
        'recipes': recipes[:3],
        'active_coupons': active_coupons,
        'selected_area': selected_area,
        'has_unserviceable_items': has_unserviceable_items,
    })


@login_required
@require_POST
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_active=True)
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.META.get('HTTP_ACCEPT', '')

    pincode = request.session.get('user_pincode')
    area_id = request.session.get('delivery_area_id')
    selected_area = None
    if area_id:
        selected_area = DeliveryArea.objects.filter(id=area_id, is_active=True).first()
    elif pincode:
        selected_area = DeliveryArea.objects.filter(pincode=pincode, is_active=True).first()

    if product.vendor:
        v_profile = getattr(product.vendor, 'vendor_profile', None)
        if not v_profile or v_profile.status != 'approved':
            msg = 'This product is from a vendor who is currently inactive.'
            if is_ajax:
                return JsonResponse({'success': False, 'message': msg}, status=400)
            messages.error(request, msg)
            return redirect(request.POST.get('next', request.META.get('HTTP_REFERER', '/')))

        if selected_area:
            has_area_vendors = VendorProfile.objects.filter(service_areas=selected_area, status='approved').exists()
            serves = (
                v_profile.service_areas.filter(id=selected_area.id, is_active=True).exists() or
                v_profile.pincode == selected_area.pincode or
                (v_profile.assigned_area and selected_area.pincode in v_profile.assigned_area) or
                not has_area_vendors
            )
            if not serves:
                msg = f"Vendor '{v_profile.shop_name}' cannot deliver this item to {selected_area.display_name}."
                if is_ajax:
                    return JsonResponse({'success': False, 'message': msg}, status=400)
                messages.error(request, msg)
                return redirect(request.POST.get('next', request.META.get('HTTP_REFERER', '/')))

    cart = get_or_create_cart(request)
    try:
        quantity = int(request.POST.get('quantity', 1))
        if quantity <= 0:
            quantity = 1
    except (ValueError, TypeError):
        quantity = 1

    item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    target_qty = quantity if created else item.quantity + quantity

    if target_qty > product.stock:
        msg = f'Sorry, only {product.stock} units of {product.name} are available in stock.'
        if is_ajax:
            return JsonResponse({'success': False, 'message': msg}, status=400)
        messages.warning(request, msg)
        next_url = request.POST.get('next', request.META.get('HTTP_REFERER', '/'))
        return redirect(next_url)

    if not created:
        item.quantity += quantity
    else:
        item.quantity = quantity
    item.save()

    msg = f'"{product.name}" added to cart!'
    if is_ajax:
        return JsonResponse({
            'success': True,
            'message': msg,
            'cart_count': cart.item_count,
            'product_name': product.name,
        })

    messages.success(request, msg)
    next_url = request.POST.get('next', request.META.get('HTTP_REFERER', '/'))
    return redirect(next_url)


@login_required
@require_POST
def update_cart(request):
    try:
        data = json.loads(request.body)
        item_id = data.get('item_id')
        quantity = int(data.get('quantity', 1))
    except Exception:
        return JsonResponse({'success': False, 'error': 'Invalid request body.'}, status=400)

    try:
        cart = get_or_create_cart(request)
        item = CartItem.objects.select_related('product').get(id=item_id, cart=cart)
        if quantity <= 0:
            item.delete()
        else:
            if not item.product.is_active:
                item.delete()
                return JsonResponse({'success': False, 'error': f'{item.product.name} is no longer available.'})
            if quantity > item.product.stock:
                return JsonResponse({
                    'success': False,
                    'error': f'Sorry, only {item.product.stock} units of {item.product.name} are available in stock.'
                })
            item.quantity = quantity
            item.save()
        cart.refresh_from_db()
        return JsonResponse({
            'success': True,
            'item_subtotal': float(item.subtotal) if quantity > 0 else 0,
            'cart_subtotal': float(cart.subtotal),
            'discount': float(cart.discount_amount),
            'delivery_fee': float(cart.delivery_fee),
            'amount_for_free_delivery': float(cart.amount_for_free_delivery),
            'total': float(cart.total),
            'item_count': cart.item_count,
        })
    except CartItem.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Item not found in cart.'})


@login_required
def remove_from_cart(request, item_id):
    cart = get_or_create_cart(request)
    CartItem.objects.filter(id=item_id, cart=cart).delete()
    messages.success(request, 'Item removed from cart.')
    return redirect('cart')


@login_required
@require_POST
def apply_coupon(request):
    code = request.POST.get('code', '').strip().upper()
    cart = get_or_create_cart(request)

    try:
        coupon = Coupon.objects.get(code=code)
        valid, msg = coupon.is_valid(cart.subtotal)
        if valid:
            cart.coupon = coupon
            cart.save()
            return JsonResponse({
                'success': True,
                'message': f'Coupon applied! You save ₹{cart.discount_amount:.0f}',
                'discount': float(cart.discount_amount),
                'total': float(cart.total),
                'delivery_fee': float(cart.delivery_fee),
                'amount_for_free_delivery': float(cart.amount_for_free_delivery),
            })
        else:
            return JsonResponse({'success': False, 'message': msg})
    except Coupon.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Invalid coupon code.'})


@login_required
def remove_coupon(request):
    cart = get_or_create_cart(request)
    cart.coupon = None
    cart.save()
    messages.info(request, 'Coupon removed.')
    return redirect('cart')


# ─────────────────────────────────────────────
# Checkout & Payment
# ─────────────────────────────────────────────

@login_required
def checkout(request):
    cart = get_or_create_cart(request)
    if not cart.items.exists():
        messages.warning(request, 'Your cart is empty.')
        return redirect('cart')

    today = date.today()
    for i in range(7):
        day = today + timedelta(days=i)
        for slot_key in ['morning', 'afternoon', 'evening']:
            DeliverySlot.objects.get_or_create(
                date=day,
                slot=slot_key,
                defaults={'max_orders': 20, 'current_bookings': 0}
            )

    slots = DeliverySlot.objects.filter(
        date__gte=today,
        date__lte=today + timedelta(days=6)
    ).order_by('date', 'slot')

    saved_addresses = CustomerAddress.objects.filter(user=request.user).order_by('-is_default', '-created_at')

    if request.method == 'POST':
        saved_address_id = request.POST.get('saved_address_id')
        saved_address = None
        if saved_address_id:
            saved_address = CustomerAddress.objects.filter(id=saved_address_id, user=request.user).first()

        if saved_address:
            address = saved_address.full_address
            pincode = saved_address.pincode
            city = saved_address.city
            state = saved_address.state
            phone = saved_address.phone
        else:
            address = request.POST.get('address', '').strip()
            pincode = request.POST.get('pincode', '').strip()
            city = request.POST.get('city', '').strip()
            state = request.POST.get('state', '').strip()
            phone = request.POST.get('phone', '').strip()
            if request.POST.get('save_address') and address and pincode:
                label = request.POST.get('address_label', '').strip() or 'Home'
                CustomerAddress.objects.create(
                    user=request.user,
                    label=label,
                    full_address=address,
                    pincode=pincode,
                    city=city or 'City',
                    state=state or 'State',
                    phone=phone,
                )

        slot_id = request.POST.get('slot_id')
        payment_method = request.POST.get('payment_method', 'COD').upper()
        if payment_method not in ['COD', 'RAZORPAY']:
            payment_method = 'COD'
        raw_notes = request.POST.get('notes', '').strip()

        if not address or not phone or not pincode:
            messages.error(request, 'Please provide your delivery address, phone number, and pincode.')
            return render(request, 'store/checkout.html', {
                'cart': cart,
                'slots': slots,
                'saved_addresses': saved_addresses,
                'razorpay_key_id': settings.RAZORPAY_KEY_ID,
            })

        # Validate active DeliveryArea in database
        clean_pin = clean_pincode(pincode)
        area = DeliveryArea.objects.filter(pincode=clean_pin, is_active=True).first() if clean_pin else None
        if not area and clean_pin:
            area = DeliveryArea.objects.create(
                pincode=clean_pin,
                area_name=f"Zone {clean_pin}",
                city=city or 'Local Area',
                is_active=True,
                delivery_fee=30,
                minimum_order_value=100,
                estimated_delivery_minutes=45,
            )
        if not area:
            messages.error(request, f'Please enter a valid 6-digit Indian delivery pincode (entered: "{pincode}").')
            return render(request, 'store/checkout.html', {
                'cart': cart,
                'slots': slots,
                'saved_addresses': saved_addresses,
                'razorpay_key_id': settings.RAZORPAY_KEY_ID,
            })

        # Validate minimum order value for this delivery area
        if cart.subtotal < area.minimum_order_value:
            messages.error(
                request,
                f'The minimum order value for {area.area_name} is ₹{area.minimum_order_value}. '
                f'Your current basket subtotal is ₹{cart.subtotal}. Please add more items.'
            )
            return redirect('cart')

        # Server-side delivery fee calculation (free if subtotal >= 500)
        from decimal import Decimal
        actual_delivery_fee = Decimal('0.00') if cart.subtotal >= Decimal('500.00') else area.delivery_fee

        # Pre-check vendor serviceability for this delivery area
        cart_items_check = cart.items.select_related('product', 'product__vendor', 'product__vendor__vendor_profile').all()
        has_area_vendors = VendorProfile.objects.filter(service_areas=area, status='approved').exists()
        for it in cart_items_check:
            if not it.product.is_active:
                messages.error(request, f'Item "{it.product.name}" is no longer active.')
                return redirect('cart')
            if it.product.vendor:
                vp = getattr(it.product.vendor, 'vendor_profile', None)
                if not vp or vp.status != 'approved':
                    messages.error(request, f'Item "{it.product.name}" is from an inactive vendor.')
                    return redirect('cart')
                serves = (
                    vp.service_areas.filter(id=area.id, is_active=True).exists() or
                    vp.pincode == clean_pin or
                    (vp.assigned_area and clean_pin in vp.assigned_area) or
                    not has_area_vendors
                )
                if not serves:
                    messages.error(
                        request,
                        f'Vendor "{vp.shop_name}" does not deliver to {area.display_name} for item "{it.product.name}".'
                    )
                    return render(request, 'store/checkout.html', {
                        'cart': cart,
                        'slots': slots,
                        'saved_addresses': saved_addresses,
                        'razorpay_key_id': settings.RAZORPAY_KEY_ID,
                    })

        # Atomic transaction with row locking
        try:
            with transaction.atomic():
                cart_items = list(cart.items.select_related('product').all())
                prod_ids = [ci.product_id for ci in cart_items]
                locked_products = {p.id: p for p in Product.objects.select_for_update().filter(id__in=prod_ids)}

                for ci in cart_items:
                    prod = locked_products.get(ci.product_id)
                    if not prod or not prod.is_active or prod.stock < ci.quantity:
                        available_stock = prod.stock if prod else 0
                        messages.error(
                            request,
                            f'Sorry, only {available_stock} units of "{ci.product.name}" are available. Please adjust your cart.'
                        )
                        return redirect('cart')

                slot = None
                slot_note_label = "Standard Scheduled Delivery"
                if slot_id and slot_id != 'express':
                    try:
                        slot = DeliverySlot.objects.select_for_update().get(id=slot_id)
                        if not slot.is_available:
                            messages.error(request, 'The selected delivery slot is full. Please choose another slot.')
                            return redirect('checkout')
                        slot_note_label = f"Scheduled Slot: {slot.get_slot_display()} on {slot.date.strftime('%d %b %Y')}"
                    except DeliverySlot.DoesNotExist:
                        messages.error(request, 'Invalid delivery slot selection.')
                        return redirect('checkout')
                elif slot_id == 'express':
                    slot_note_label = "Express Priority Delivery"

                coupon = None
                discount = Decimal('0.00')
                if cart.coupon_id:
                    try:
                        coupon = Coupon.objects.select_for_update().get(id=cart.coupon_id)
                        valid, msg = coupon.is_valid(cart.subtotal)
                        if not valid or coupon.used_count >= coupon.max_uses:
                            coupon = None
                        else:
                            discount = Decimal(str(cart.discount_amount))
                    except Coupon.DoesNotExist:
                        coupon = None

                notes = f"Payment Method: {payment_method}\nDelivery Mode: {slot_note_label}\nDelivery Area: {area.display_name}"
                if raw_notes:
                    notes += f"\nCustomer Notes: {raw_notes}"

                is_cod = (payment_method == 'COD')
                initial_status = 'confirmed' if is_cod else 'pending'
                confirmed_time = timezone.now() if is_cod else None

                order_total = max(Decimal('0.00'), cart.subtotal - discount + actual_delivery_fee)

                order = Order.objects.create(
                    user=request.user,
                    delivery_slot=slot,
                    coupon=coupon,
                    address=address,
                    phone=phone,
                    delivery_pincode=pincode,
                    delivery_city=city or area.city,
                    subtotal=cart.subtotal,
                    discount_amount=discount,
                    delivery_fee=actual_delivery_fee,
                    total=order_total,
                    payment_method=payment_method,
                    payment_status='pending',
                    status=initial_status,
                    confirmed_at=confirmed_time,
                    notes=notes,
                )

                # Group items by vendor and create child VendorOrder fulfillments
                vendor_grouped = {}
                for ci in cart_items:
                    v = ci.product.vendor
                    vendor_grouped.setdefault(v, []).append(ci)

                for vendor, items in vendor_grouped.items():
                    vendor_subtotal = sum(ci.product.effective_price * ci.quantity for ci in items)
                    vendor_order = VendorOrder.objects.create(
                        order=order,
                        vendor=vendor,
                        subtotal=vendor_subtotal,
                        status=initial_status,
                        confirmed_at=confirmed_time,
                    )

                    for ci in items:
                        prod = locked_products[ci.product_id]
                        OrderItem.objects.create(
                            order=order,
                            vendor=vendor,
                            vendor_order=vendor_order,
                            product=prod,
                            product_name=prod.name,
                            quantity=ci.quantity,
                            price=prod.effective_price,
                        )
                        prod.stock -= ci.quantity
                        prod.save()
                        check_and_send_low_stock_alert(prod)

                    OrderStatusHistory.objects.create(
                        order=order,
                        vendor_order=vendor_order,
                        status=initial_status,
                        changed_by=request.user,
                        note=f"Fulfillment created ({vendor.username if vendor else 'FoodBasket Direct'})."
                    )

                if slot:
                    slot.current_bookings += 1
                    slot.save()

                if coupon:
                    coupon.used_count += 1
                    coupon.save()

                OrderStatusHistory.objects.create(
                    order=order,
                    status=initial_status,
                    changed_by=request.user,
                    note=f"Order placed with {payment_method}."
                )

                # Clear cart
                cart.items.all().delete()
                cart.coupon = None
                cart.save()

        except Exception as e:
            logger.exception("Checkout transaction failed: %s", e)
            messages.error(request, 'An error occurred while processing your order. Please try again.')
            return redirect('checkout')

        if payment_method == 'COD':
            messages.success(request, f'Order #{order.id} placed successfully! 🎉 Cash on Delivery confirmed.')
            return redirect('order_confirm', order_id=order.id)
        else:
            rp_order = create_razorpay_order(order.total, f"order_{order.id}")
            order.razorpay_order_id = rp_order.get('id', '')
            order.save(update_fields=['razorpay_order_id'])

            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.POST.get('is_ajax'):
                return JsonResponse({
                    'success': True,
                    'payment_method': 'RAZORPAY',
                    'razorpay_order_id': rp_order['id'],
                    'amount': rp_order['amount'],
                    'currency': rp_order.get('currency', 'INR'),
                    'key': settings.RAZORPAY_KEY_ID,
                    'order_id': order.id,
                    'customer_name': request.user.get_full_name() or request.user.username,
                    'customer_email': request.user.email,
                    'customer_phone': phone,
                })

            return render(request, 'store/payment_process.html', {
                'order': order,
                'razorpay_order_id': rp_order['id'],
                'amount': rp_order['amount'],
                'currency': rp_order.get('currency', 'INR'),
                'razorpay_key_id': settings.RAZORPAY_KEY_ID,
                'phone': phone,
            })

    return render(request, 'store/checkout.html', {
        'cart': cart,
        'slots': slots,
        'saved_addresses': saved_addresses,
        'razorpay_key_id': settings.RAZORPAY_KEY_ID,
    })


@login_required
@require_POST
def verify_razorpay_payment_view(request):
    try:
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST

        order_id = data.get('order_id')
        rp_order_id = data.get('razorpay_order_id')
        rp_payment_id = data.get('razorpay_payment_id')
        rp_signature = data.get('razorpay_signature')

        order = get_object_or_404(Order, id=order_id, user=request.user)

        is_valid = verify_razorpay_payment(rp_order_id, rp_payment_id, rp_signature)
        if not is_valid:
            logger.warning("Payment signature verification failed for Order #%s", order.id)
            return JsonResponse({'success': False, 'error': 'Payment verification failed. Invalid signature.'}, status=400)

        with transaction.atomic():
            now = timezone.now()
            order.payment_status = 'paid'
            order.payment_id = rp_payment_id
            order.status = 'confirmed'
            order.confirmed_at = now
            order.paid_at = now
            order.save()

            for vo in order.vendor_orders.all():
                vo.status = 'confirmed'
                vo.confirmed_at = now
                vo.save()
                OrderStatusHistory.objects.create(
                    order=order,
                    vendor_order=vo,
                    status='confirmed',
                    changed_by=request.user,
                    note=f"Payment verified ({rp_payment_id})"
                )

            OrderStatusHistory.objects.create(
                order=order,
                status='confirmed',
                changed_by=request.user,
                note=f"Online payment verified. Payment ID: {rp_payment_id}"
            )

        messages.success(request, f'Payment successful! Order #{order.id} confirmed.')
        return JsonResponse({
            'success': True,
            'redirect_url': reverse('order_confirm', kwargs={'order_id': order.id})
        })
    except Exception as e:
        logger.exception("Error in verify_razorpay_payment_view: %s", e)
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def order_confirm(request, order_id):
    order = get_object_or_404(
        Order.objects.prefetch_related('vendor_orders', 'vendor_orders__vendor', 'vendor_orders__items', 'history'),
        id=order_id,
        user=request.user
    )
    return render(request, 'store/order_confirm.html', {'order': order})


@login_required
def order_invoice(request, order_id):
    order = get_object_or_404(
        Order.objects.prefetch_related('vendor_orders', 'items'),
        id=order_id,
        user=request.user
    )
    return render(request, 'store/order_invoice.html', {'order': order})


@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).prefetch_related('items', 'vendor_orders', 'vendor_orders__vendor').order_by('-created_at')
    return render(request, 'store/orders.html', {'orders': orders})


@login_required
@require_POST
def cancel_order(request, order_id):
    with transaction.atomic():
        try:
            order = Order.objects.select_for_update().get(id=order_id, user=request.user)
        except Order.DoesNotExist:
            messages.error(request, 'Order not found.')
            return redirect('order_history')

        if order.status not in ['pending', 'confirmed']:
            messages.error(request, f'Order #{order.id} cannot be cancelled as it is already {order.get_status_display().lower()}.')
            return redirect('order_history')

        # Restock products
        order_items = order.items.select_related('product').all()
        prod_ids = [it.product_id for it in order_items if it.product_id]
        products = {p.id: p for p in Product.objects.select_for_update().filter(id__in=prod_ids)}
        for it in order_items:
            if it.product_id and it.product_id in products:
                prod = products[it.product_id]
                prod.stock += it.quantity
                prod.save()

        # Restore slot capacity
        if order.delivery_slot_id:
            slot = DeliverySlot.objects.select_for_update().get(id=order.delivery_slot_id)
            if slot.current_bookings > 0:
                slot.current_bookings -= 1
                slot.save()

        # Restore coupon usage
        if order.coupon_id:
            coupon = Coupon.objects.select_for_update().get(id=order.coupon_id)
            if coupon.used_count > 0:
                coupon.used_count -= 1
                coupon.save()

        now = timezone.now()
        order.status = 'cancelled'
        order.cancelled_at = now
        order.save()

        for vo in order.vendor_orders.all():
            vo.status = 'cancelled'
            vo.cancelled_at = now
            vo.save()
            OrderStatusHistory.objects.create(
                order=order,
                vendor_order=vo,
                status='cancelled',
                changed_by=request.user,
                note="Customer cancelled order."
            )

        OrderStatusHistory.objects.create(
            order=order,
            status='cancelled',
            changed_by=request.user,
            note="Customer cancelled order. Inventory and slot capacity restored."
        )

    messages.success(request, f'Order #{order.id} has been cancelled. All items restored to stock.')
    next_url = request.POST.get('next') or 'order_history'
    return redirect(next_url)


# ─────────────────────────────────────────────
# Customer Account & Saved Addresses
# ─────────────────────────────────────────────

@login_required
def account_view(request):
    user_orders = Order.objects.filter(user=request.user).prefetch_related('vendor_orders', 'items')
    recent_orders = user_orders.order_by('-created_at')[:5]
    total_spent = sum(o.total for o in user_orders.filter(status__in=['confirmed', 'out_for_delivery', 'delivered']))
    cart = get_or_create_cart(request)
    addresses = CustomerAddress.objects.filter(user=request.user).order_by('-is_default', '-created_at')
    address_form = CustomerAddressForm()
    return render(request, 'store/account.html', {
        'recent_orders': recent_orders,
        'order_count': user_orders.count(),
        'total_spent': total_spent,
        'cart_item_count': cart.item_count,
        'addresses': addresses,
        'address_form': address_form,
    })


@login_required
@require_POST
def account_address_add(request):
    form = CustomerAddressForm(request.POST)
    if form.is_valid():
        addr = form.save(commit=False)
        addr.user = request.user
        addr.save()
        messages.success(request, 'Address saved successfully.')
    else:
        messages.error(request, 'Please correct the address errors.')
    return redirect('account')


@login_required
@require_POST
def account_address_delete(request, address_id):
    addr = get_object_or_404(CustomerAddress, id=address_id, user=request.user)
    addr.delete()
    messages.success(request, 'Address removed.')
    return redirect('account')


# ─────────────────────────────────────────────
# Wishlist & Recipes
# ─────────────────────────────────────────────

@login_required
@require_POST
def toggle_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    wishlist_item, created = Wishlist.objects.get_or_create(user=request.user, product=product)
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.META.get('HTTP_ACCEPT', '')

    if not created:
        wishlist_item.delete()
        if is_ajax:
            return JsonResponse({'success': True, 'action': 'removed', 'message': f'Removed {product.name} from wishlist.'})
        messages.info(request, f'Removed {product.name} from wishlist.')
    else:
        if is_ajax:
            return JsonResponse({'success': True, 'action': 'added', 'message': f'Added {product.name} to wishlist.'})
        messages.success(request, f'Added {product.name} to wishlist.')
    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER') or 'home'
    return redirect(next_url)


@login_required
def wishlist_view(request):
    items = Wishlist.objects.filter(user=request.user).select_related('product')
    categories = Category.objects.all()
    return render(request, 'store/wishlist.html', {
        'items': items,
        'categories': categories,
    })


@login_required
def recipes_view(request):
    recipes = Recipe.objects.all()
    return render(request, 'store/recipes.html', {'recipes': recipes})


# ─────────────────────────────────────────────
# Delivery Slots, Search & Serviceability AJAX
# ─────────────────────────────────────────────

def get_slots(request):
    today = date.today()
    slots_qs = DeliverySlot.objects.filter(
        date__gte=today,
        date__lte=today + timedelta(days=6)
    )
    result = []
    for s in slots_qs:
        result.append({
            'id': s.id,
            'date': str(s.date),
            'slot': s.slot,
            'slots_remaining': s.slots_remaining,
            'is_available': s.is_available,
        })
    return JsonResponse({'slots': result})


def search_autocomplete(request):
    query = request.GET.get('q', '').strip()
    result = []
    if len(query) >= 2:
        qs = Product.objects.filter(
            Q(name__icontains=query) | Q(category__name__icontains=query),
            is_active=True,
            stock__gt=0
        ).select_related('category')
        products = get_location_filtered_products(request, qs)[:6]
        for p in products:
            result.append({
                'name': p.name,
                'price': float(p.effective_price),
                'category': p.category.name,
                'icon': p.category.icon,
                'url': f'/product/{p.slug}/'
            })
    return JsonResponse({'results': result})


@require_POST
def set_location(request):
    """
    AJAX view to set user pincode and area in session.
    Accepts and registers any valid Indian pincode so the customer can order from anywhere.
    """
    try:
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            pincode = data.get('pincode', '')
            area_id = data.get('area_id')
        else:
            pincode = request.POST.get('pincode', '')
            area_id = request.POST.get('area_id')
    except Exception:
        pincode = request.POST.get('pincode', '')
        area_id = request.POST.get('area_id')

    area = None
    if area_id:
        area = DeliveryArea.objects.filter(id=area_id).first()

    clean_pin = clean_pincode(pincode) if pincode else None
    if not area and clean_pin:
        area = DeliveryArea.objects.filter(pincode=clean_pin).first()
        if not area:
            area = DeliveryArea.objects.create(
                pincode=clean_pin,
                area_name=f"Zone {clean_pin}",
                city="Local Area",
                is_active=True,
                delivery_fee=30,
                minimum_order_value=100,
                estimated_delivery_minutes=45,
            )

    if not area and not clean_pin:
        return JsonResponse({
            'success': False,
            'is_serviceable': False,
            'error': 'Please enter a valid 6-digit Indian pincode.',
        }, status=400)

    if area and not area.is_active:
        area.is_active = True
        area.save()

    # Persist in session
    request.session['delivery_area_id'] = area.id
    request.session['user_pincode'] = area.pincode
    request.session['user_area_name'] = area.area_name
    request.session['user_city'] = area.city
    request.session['user_location_label'] = area.display_name

    return JsonResponse({
        'success': True,
        'is_serviceable': True,
        'area_id': area.id,
        'pincode': area.pincode,
        'area_name': area.area_name,
        'city': area.city,
        'state': area.state,
        'display_name': area.display_name,
        'delivery_fee': float(area.delivery_fee),
        'minimum_order_value': float(area.minimum_order_value),
        'estimated_delivery_minutes': area.estimated_delivery_minutes,
    })


def detect_location_api(request):
    """
    Performs real reverse geocoding via configured geocoding provider,
    registers the detected location as an active DeliveryArea,
    and automatically selects it in the user session.
    """
    lat = request.GET.get('lat')
    lng = request.GET.get('lng') or request.GET.get('lon')

    if not lat or not lng:
        return JsonResponse({
            'success': False,
            'error_type': 'missing_coordinates',
            'error': 'Latitude and longitude query parameters are required.'
        }, status=400)

    geo_result = service_reverse_geocode(lat, lng)
    if not geo_result.get('success'):
        return JsonResponse(geo_result, status=400)

    detected_pincode = geo_result.get('pincode')
    locality = geo_result.get('locality') or ''
    city = geo_result.get('city') or 'Local Area'
    state = geo_result.get('state') or ''
    area_name = locality or city or (f"Zone {detected_pincode}" if detected_pincode else "Detected Location")

    # If geocoder did not extract a 6-digit postal code, fallback to existing active area or a default
    if not detected_pincode:
        existing_area = DeliveryArea.objects.filter(is_active=True).first()
        detected_pincode = existing_area.pincode if existing_area else "625001"

    service_result = check_pincode_serviceability(
        detected_pincode,
        area_name=area_name,
        city=city,
        state=state,
        latitude=float(lat) if lat else None,
        longitude=float(lng) if lng else None,
    )

    # Automatically select the detected location in the session right away!
    area_id = service_result.get('area_id')
    area = DeliveryArea.objects.filter(id=area_id).first() if area_id else None
    if area:
        request.session['delivery_area_id'] = area.id
        request.session['user_pincode'] = area.pincode
        request.session['user_area_name'] = area.area_name
        request.session['user_city'] = area.city
        request.session['user_location_label'] = area.display_name
        request.session['detected_address'] = geo_result.get('formatted_address', area.display_name)

    return JsonResponse({
        'success': True,
        'is_serviceable': True,
        'selected': True,
        'detected_location': geo_result,
        'serviceability': service_result,
    })


def check_pincode_api(request):
    """
    API endpoint to check serviceability of a 6-digit Indian pincode against database DeliveryAreas.
    Supports GET (?pincode=...) or POST (JSON or form-data).
    """
    if request.method == 'POST':
        try:
            if request.content_type == 'application/json':
                data = json.loads(request.body)
                pincode = data.get('pincode', '')
            else:
                pincode = request.POST.get('pincode', '')
        except Exception:
            pincode = request.POST.get('pincode', '')
    else:
        pincode = request.GET.get('pincode', '')

    result = check_pincode_serviceability(pincode)
    status_code = 200 if result.get('success') else 400
    return JsonResponse(result, status=status_code)


def get_location_filtered_products(request, queryset=None):
    """
    Filters products based on the customer's active delivery area.
    If area-specific vendors exist, prioritizes them.
    Otherwise, returns all approved marketplace vendors so customers can shop from anywhere.
    """
    if queryset is None:
        queryset = Product.objects.filter(is_active=True, stock__gt=0)
    else:
        queryset = queryset.filter(is_active=True)

    area_id = request.session.get('delivery_area_id')
    pincode = request.session.get('user_pincode')

    area = None
    if area_id:
        area = DeliveryArea.objects.filter(id=area_id, is_active=True).first()
    elif pincode:
        area = DeliveryArea.objects.filter(pincode=pincode, is_active=True).first()

    if area:
        location_matches = queryset.filter(
            Q(vendor__vendor_profile__service_areas=area) |
            Q(vendor__vendor_profile__pincode=area.pincode) |
            Q(vendor__vendor_profile__assigned_area__icontains=area.pincode) |
            Q(vendor__isnull=True)
        ).filter(
            Q(vendor__vendor_profile__status='approved') | Q(vendor__isnull=True)
        ).distinct()
        if location_matches.exists():
            queryset = location_matches
        else:
            queryset = queryset.filter(
                Q(vendor__vendor_profile__status='approved') | Q(vendor__isnull=True)
            )
    else:
        queryset = queryset.filter(
            Q(vendor__vendor_profile__status='approved') | Q(vendor__isnull=True)
        )
    return queryset


def select_location(request):
    """
    Page view for selecting or detecting delivery location.
    Accessible to all users (customers and visitors).
    """
    selected_area = None
    area_id = request.session.get('delivery_area_id')
    pincode = request.session.get('user_pincode')
    if area_id:
        selected_area = DeliveryArea.objects.filter(id=area_id, is_active=True).first()
    elif pincode:
        selected_area = DeliveryArea.objects.filter(pincode=pincode, is_active=True).first()

    if request.method == 'POST':
        pin_input = request.POST.get('pincode', '').strip()
        clean_pin = clean_pincode(pin_input)

        if clean_pin:
            area = DeliveryArea.objects.filter(pincode=clean_pin).first()
            if not area:
                area = DeliveryArea.objects.create(
                    pincode=clean_pin,
                    area_name=f"Zone {clean_pin}",
                    city="Local Area",
                    is_active=True,
                    delivery_fee=30,
                    minimum_order_value=100,
                    estimated_delivery_minutes=45,
                )
            elif not area.is_active:
                area.is_active = True
                area.save()

            request.session['delivery_area_id'] = area.id
            request.session['user_pincode'] = area.pincode
            request.session['user_area_name'] = area.area_name
            request.session['user_city'] = area.city
            request.session['user_location_label'] = area.display_name
            next_url = request.GET.get('next') or 'home'
            messages.success(request, f"Delivery location set to {area.display_name}! 📍")
            return redirect(next_url)
        else:
            messages.error(request, "Please enter a valid 6-digit Indian pincode.")

    return render(request, 'store/select_location.html', {
        'selected_area': selected_area,
    })




