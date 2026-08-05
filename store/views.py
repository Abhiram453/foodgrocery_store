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
    Coupon, DeliverySlot, Order, OrderItem, Recipe, UserProfile, Wishlist
)
from .forms import ProductForm


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
    from django.utils import timezone as tz
    now = tz.now()
    categories = Category.objects.all()[:6]
    all_categories = Category.objects.all()
    featured_products = get_location_filtered_products(request, Product.objects.filter(is_featured=True, stock__gt=0))[:8]
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
    products = get_location_filtered_products(request, Product.objects.filter(stock__gt=0))
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
    if check_location(request):
        return redirect('select_location')
    product = get_object_or_404(Product, slug=slug)
    related = Product.objects.filter(category=product.category).exclude(id=product.id)[:4]
    return render(request, 'store/product_detail.html', {
        'product': product,
        'related': related,
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
    if check_location(request):
        return redirect('select_location')
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
            check_and_send_low_stock_alert(item.product)

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
def order_invoice(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'store/order_invoice.html', {'order': order})



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
# Vendor dashboard & wishlist
# ─────────────────────────────────────────────

@login_required
def vendor_dashboard(request):
    profile = get_or_create_profile(request.user)
    if profile.role != 'vendor' and not request.user.is_staff:
        messages.error(request, 'Only vendors can access this area.')
        return redirect('home')

    products = Product.objects.filter(vendor=request.user).order_by('-created_at')
    low_stock_products = [p for p in products if p.is_low_stock]
    return render(request, 'store/vendor_dashboard.html', {
        'products': products,
        'low_stock_products': low_stock_products,
    })


@login_required
def vendor_product_form(request, product_id=None):
    profile = get_or_create_profile(request.user)
    if profile.role != 'vendor' and not request.user.is_staff:
        messages.error(request, 'Only vendors can access this area.')
        return redirect('home')

    product = get_object_or_404(Product, pk=product_id) if product_id else None
    if product and product.vendor_id not in [request.user.id, None] and not request.user.is_staff:
        messages.error(request, 'You can only edit your own products.')
        return redirect('vendor_dashboard')

    form = ProductForm(request.POST or None, request.FILES or None, instance=product)
    if request.method == 'POST' and form.is_valid():
        obj = form.save(commit=False)
        obj.vendor = request.user
        obj.save()
        messages.success(request, 'Product saved successfully.')
        return redirect('vendor_dashboard')

    return render(request, 'store/vendor_product_form.html', {'form': form, 'product': product})


@login_required
@require_POST
def vendor_product_delete(request, product_id):
    profile = get_or_create_profile(request.user)
    if profile.role != 'vendor' and not request.user.is_staff:
        messages.error(request, 'Only vendors can access this area.')
        return redirect('home')

    product = get_object_or_404(Product, pk=product_id)
    if product.vendor_id != request.user.id and not request.user.is_staff:
        messages.error(request, 'You can only delete your own products.')
        return redirect('vendor_dashboard')

    product.delete()
    messages.success(request, 'Product removed successfully.')
    return redirect('vendor_dashboard')


@login_required
@require_POST
def toggle_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    wishlist_item, created = Wishlist.objects.get_or_create(user=request.user, product=product)
    if not created:
        wishlist_item.delete()
        messages.info(request, f'Removed {product.name} from wishlist.')
    else:
        messages.success(request, f'Added {product.name} to wishlist.')
    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER') or 'home'
    return redirect(next_url)


@login_required
def wishlist_view(request):
    items = Wishlist.objects.filter(user=request.user).select_related('product')
    return render(request, 'store/wishlist.html', {'items': items})


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


def search_autocomplete(request):
    query = request.GET.get('q', '').strip()
    result = []
    if len(query) >= 2:
        products = Product.objects.filter(
            Q(name__icontains=query) | Q(category__name__icontains=query)
        ).select_related('category')[:6]
        for p in products:
            result.append({
                'name': p.name,
                'price': float(p.effective_price),
                'category': p.category.name,
                'icon': p.category.icon,
                'url': f'/product/{p.slug}/'
            })
    return JsonResponse({'results': result})


from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def set_location(request):
    """
    AJAX view to set the user's pincode in the session.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            pincode = data.get('pincode', '').strip()
            area_name = data.get('area_name', '').strip()
        except Exception:
            pincode = request.POST.get('pincode', '').strip()
            area_name = request.POST.get('area_name', '').strip()

        if pincode:
            request.session['user_pincode'] = pincode
            if area_name:
                request.session['user_area_name'] = area_name
            else:
                area_mapping = {
                    '500001': 'Koti, Hyderabad',
                    '500032': 'Gachibowli, Hyderabad',
                    '500072': 'Kukatpally, Hyderabad',
                    '500081': 'Madhapur, Hyderabad',
                    '110001': 'Connaught Place, New Delhi',
                    '400001': 'Fort, Mumbai',
                    '600001': 'George Town, Chennai',
                    '560001': 'Majestic, Bengaluru',
                    '625001': 'Madurai Main, Madurai',
                    '625020': 'K.Pudur, Madurai',
                    '625009': 'Anna Nagar, Madurai',
                    '625003': 'Tallakulam, Madurai',
                }
                request.session['user_area_name'] = area_mapping.get(pincode, f"Pincode: {pincode}")

            return JsonResponse({'success': True, 'pincode': pincode, 'area_name': request.session['user_area_name']})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)


def reverse_geocode(request):
    """
    Simulates reverse geocoding from coordinates to local pincode & area.
    """
    lat = request.GET.get('lat')
    lng = request.GET.get('lng')
    
    pincode = '500032'
    area_name = 'Gachibowli, Hyderabad'
    
    if lat and lng:
        try:
            flat = float(lat)
            flng = float(lng)
            if int(flat * 10) % 2 == 0:
                pincode = '500072'
                area_name = 'Kukatpally, Hyderabad'
            elif int(flng * 10) % 2 == 0:
                pincode = '500081'
                area_name = 'Madhapur, Hyderabad'
        except ValueError:
            pass
            
    return JsonResponse({
        'success': True,
        'pincode': pincode,
        'area_name': area_name
    })


def get_location_filtered_products(request, queryset=None):
    if queryset is None:
        queryset = Product.objects.filter(stock__gt=0)
    pincode = request.session.get('user_pincode')
    if pincode:
        queryset = queryset.filter(
            Q(vendor__vendor_profile__pincode=pincode) |
            Q(vendor__vendor_profile__assigned_area__icontains=pincode) |
            Q(vendor__isnull=True)
        )
    return queryset


def select_location(request):
    if not request.user.is_authenticated:
        return redirect('login')
        
    profile = get_or_create_profile(request.user)
    if profile.role != 'customer':
        return redirect('home')

    if request.method == 'POST':
        pincode = request.POST.get('pincode', '').strip()
        if pincode:
            request.session['user_pincode'] = pincode
            
            # Simple mock area mapping
            area_mapping = {
                '500001': 'Koti, Hyderabad',
                '500032': 'Gachibowli, Hyderabad',
                '500072': 'Kukatpally, Hyderabad',
                '500081': 'Madhapur, Hyderabad',
                '110001': 'Connaught Place, New Delhi',
                '400001': 'Fort, Mumbai',
                '600001': 'George Town, Chennai',
                '560001': 'Majestic, Bengaluru',
                '625001': 'Madurai Main, Madurai',
                '625020': 'K.Pudur, Madurai',
                '625009': 'Anna Nagar, Madurai',
                '625003': 'Tallakulam, Madurai',
            }
            request.session['user_area_name'] = area_mapping.get(pincode, f"Pincode: {pincode}")
            
            next_url = request.GET.get('next') or 'home'
            messages.success(request, f"Delivery location set to {request.session['user_area_name']}! 📍")
            return redirect(next_url)
            
    return render(request, 'store/select_location.html')



