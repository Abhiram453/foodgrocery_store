from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db.models import Q
import json
from datetime import date, timedelta

from .models import (
    Category, Product, Cart, CartItem,
    Coupon, DeliverySlot, Order, OrderItem, Recipe
)


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
    from django.utils import timezone as tz
    now = tz.now()
    categories = Category.objects.all()[:6]
    all_categories = Category.objects.all()
    featured_products = Product.objects.filter(is_featured=True, stock__gt=0)[:8]
    active_coupons = Coupon.objects.filter(
        is_active=True,
        valid_from__lte=now,
        valid_to__gte=now,
    )
    featured_recipes = Recipe.objects.all()[:6]
    return render(request, 'home.html', {
        'categories': categories,
        'all_categories': all_categories,
        'featured_products': featured_products,
        'active_coupons': active_coupons,
        'featured_recipes': featured_recipes,
    })


# ─────────────────────────────────────────────
# Products
# ─────────────────────────────────────────────

def product_list(request, slug=None):
    products = Product.objects.filter(stock__gt=0)
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
    return render(request, 'store/product_list.html', {
        'products': products,
        'categories': categories,
        'current_category': current_category,
        'query': q,
        'sort': sort,
    })


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    related = Product.objects.filter(category=product.category).exclude(id=product.id)[:4]
    return render(request, 'store/product_detail.html', {
        'product': product,
        'related': related,
    })


# ─────────────────────────────────────────────
# Cart
# ─────────────────────────────────────────────

@login_required
def cart_view(request):
    from django.utils import timezone as tz
    now = tz.now()
    cart = get_or_create_cart(request)
    cart_items = cart.items.select_related('product').all()

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
    })


@login_required
@require_POST
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = get_or_create_cart(request)
    quantity = int(request.POST.get('quantity', 1))

    item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    
    # Check if requested quantity exceeds stock
    target_qty = quantity if created else item.quantity + quantity
    if target_qty > product.stock:
        messages.warning(request, f'Sorry, only {product.stock} units of {product.name} are available in stock.')
        next_url = request.POST.get('next', request.META.get('HTTP_REFERER', '/'))
        return redirect(next_url)

    if not created:
        item.quantity += quantity
    else:
        item.quantity = quantity
    item.save()

    messages.success(request, f'"{product.name}" added to cart!')
    next_url = request.POST.get('next', request.META.get('HTTP_REFERER', '/'))
    return redirect(next_url)


@login_required
@require_POST
def update_cart(request):
    data = json.loads(request.body)
    item_id = data.get('item_id')
    quantity = int(data.get('quantity', 1))

    try:
        cart = get_or_create_cart(request)
        item = CartItem.objects.get(id=item_id, cart=cart)
        if quantity <= 0:
            item.delete()
        else:
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
            'total': float(cart.total),
            'item_count': cart.item_count,
        })
    except CartItem.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Item not found'})


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
# Checkout
# ─────────────────────────────────────────────

@login_required
def checkout(request):
    cart = get_or_create_cart(request)
    if not cart.items.exists():
        messages.warning(request, 'Your cart is empty.')
        return redirect('cart')

    today = date.today()
    
    # Auto-generate slots for the next 7 days if they do not exist in the database
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

    if request.method == 'POST':
        address = request.POST.get('address', '').strip()
        phone = request.POST.get('phone', '').strip()
        slot_id = request.POST.get('slot_id')
        payment_method = request.POST.get('payment_method', 'COD')
        raw_notes = request.POST.get('notes', '')

        if not address or not phone:
            messages.error(request, 'Please fill in your address and phone number.')
            return render(request, 'store/checkout.html', {'cart': cart, 'slots': slots})

        slot = None
        slot_note_label = "⚡ Express Local Delivery (Under 45–60 Mins)"
        if slot_id and slot_id != 'express':
            try:
                slot = DeliverySlot.objects.get(id=slot_id)
                if not slot.is_available:
                    messages.error(request, 'The selected delivery slot is full. Please choose another or select Express Delivery.')
                    return render(request, 'store/checkout.html', {'cart': cart, 'slots': slots})
                slot_note_label = f"Scheduled Slot: {slot.get_slot_display()} on {slot.date.strftime('%d %b %Y')}"
            except DeliverySlot.DoesNotExist:
                messages.error(request, 'Invalid delivery slot selection.')
                return render(request, 'store/checkout.html', {'cart': cart, 'slots': slots})

        # Build order notes
        notes = f"Payment Method: {payment_method}\nDelivery Mode: {slot_note_label}"
        if raw_notes:
            notes += f"\nCustomer Notes: {raw_notes}"

        # Create order
        order = Order.objects.create(
            user=request.user,
            delivery_slot=slot,
            coupon=cart.coupon,
            address=address,
            phone=phone,
            subtotal=cart.subtotal,
            discount_amount=cart.discount_amount,
            delivery_fee=cart.delivery_fee,
            total=cart.total,
            notes=notes,
        )

        # Create order items
        for item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=item.product,
                product_name=item.product.name,
                quantity=item.quantity,
                price=item.product.effective_price,
            )
            # Reduce stock
            item.product.stock -= item.quantity
            item.product.save()

        # Update slot bookings if a specific slot was selected
        if slot:
            slot.current_bookings += 1
            slot.save()

        # Update coupon usage
        if cart.coupon:
            cart.coupon.used_count += 1
            cart.coupon.save()

        # Clear cart
        cart.items.all().delete()
        cart.coupon = None
        cart.save()

        messages.success(request, f'Order #{order.id} placed successfully! 🎉 Delivery in under 60 mins!')
        return redirect('order_confirm', order_id=order.id)

    return render(request, 'store/checkout.html', {'cart': cart, 'slots': slots})


@login_required
def order_confirm(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'store/order_confirm.html', {'order': order})


@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).prefetch_related('items')
    return render(request, 'store/orders.html', {'orders': orders})


@login_required
@require_POST
def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    if order.status in ['pending', 'confirmed']:
        # Restock products
        for item in order.items.all():
            if item.product:
                item.product.stock += item.quantity
                item.product.save()

        # Decrement slot booking if slot was chosen
        if order.delivery_slot and order.delivery_slot.current_bookings > 0:
            order.delivery_slot.current_bookings -= 1
            order.delivery_slot.save()

        order.status = 'cancelled'
        order.save()
        messages.success(request, f'Order #{order.id} has been cancelled successfully. Items restored to inventory.')
    else:
        messages.error(request, f'Order #{order.id} cannot be cancelled as it is already {order.get_status_display().lower()}.')

    next_url = request.POST.get('next') or 'order_history'
    return redirect(next_url)


@login_required
def account_view(request):
    user_orders = Order.objects.filter(user=request.user)
    recent_orders = user_orders[:5]
    total_spent = sum(o.total for o in user_orders)
    cart = get_or_create_cart(request)
    return render(request, 'store/account.html', {
        'recent_orders': recent_orders,
        'order_count': user_orders.count(),
        'total_spent': total_spent,
        'cart_item_count': cart.item_count,
    })


# ─────────────────────────────────────────────
# Recipes
# ─────────────────────────────────────────────

@login_required
def recipes_view(request):
    recipes = Recipe.objects.all()
    return render(request, 'store/recipes.html', {'recipes': recipes})


# ─────────────────────────────────────────────
# Delivery Slots AJAX
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
