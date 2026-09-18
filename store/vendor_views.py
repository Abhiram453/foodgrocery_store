from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.db.models import Sum, F
from django.db import transaction
from django.utils import timezone

from .models import UserProfile, VendorProfile, Product, Order, OrderItem, VendorOrder, OrderStatusHistory
from .forms import VendorRegisterForm, VendorProductForm
from .views import get_or_create_profile
from functools import wraps

def vendor_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('vendor_login')
        profile = get_or_create_profile(request.user)
        if profile.role != 'vendor':
            messages.error(request, 'Access denied. You are not a registered vendor.')
            logout(request)
            return redirect('vendor_login')
        vendor_profile = getattr(request.user, 'vendor_profile', None)
        if not vendor_profile or vendor_profile.status != 'approved':
            return redirect('vendor_pending')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def vendor_login(request):
    if request.user.is_authenticated:
        profile = get_or_create_profile(request.user)
        if profile.role == 'vendor':
            vendor_profile = getattr(request.user, 'vendor_profile', None)
            if vendor_profile and vendor_profile.status == 'approved':
                return redirect('vendor_dashboard')
            return redirect('vendor_pending')
        return redirect('home')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        user = authenticate(request, username=username, password=password)
        if user is not None:
            profile = get_or_create_profile(user)
            if profile.role != 'vendor':
                messages.error(request, 'Access denied. This account is not registered as a vendor.')
                return render(request, 'store/vendor_login.html')
            
            login(request, user)
            vendor_profile = getattr(user, 'vendor_profile', None)
            if not vendor_profile or vendor_profile.status != 'approved':
                return redirect('vendor_pending')
            
            messages.success(request, f'Welcome back, {user.username}! (Vendor Dashboard)')
            return redirect('vendor_dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'store/vendor_login.html')

def vendor_register(request):
    if request.user.is_authenticated:
        return redirect('home')
        
    if request.method == 'POST':
        form = VendorRegisterForm(request.POST)
        if form.is_valid():
            # Create User
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password']
            )
            # Update role to vendor
            profile = get_or_create_profile(user)
            profile.role = 'vendor'
            profile.save()
            
            # Create VendorProfile
            VendorProfile.objects.create(
                user=user,
                shop_name=form.cleaned_data['shop_name'],
                shop_address=form.cleaned_data['shop_address'],
                pincode=form.cleaned_data['pincode'],
                status='pending'
            )
            
            # Authenticate & log in
            login(request, user)
            messages.success(request, 'Registration submitted! Your shop details are pending approval.')
            return redirect('vendor_pending')
    else:
        form = VendorRegisterForm()
    return render(request, 'store/vendor_register.html', {'form': form})

@login_required
def vendor_pending(request):
    profile = get_or_create_profile(request.user)
    if profile.role != 'vendor':
        return redirect('home')
    vendor_profile = getattr(request.user, 'vendor_profile', None)
    if vendor_profile and vendor_profile.status == 'approved':
        return redirect('vendor_dashboard')
    return render(request, 'store/vendor_pending.html', {'vendor_profile': vendor_profile})

@vendor_required
def vendor_dashboard(request):
    products = Product.objects.filter(vendor=request.user, is_active=True).order_by('-created_at')
    low_stock_products = [p for p in products if p.is_low_stock]
    
    # Calculate vendor statistics excluding cancelled orders
    vendor_orders_active = VendorOrder.objects.filter(
        vendor=request.user,
        status__in=['confirmed', 'out_for_delivery', 'delivered']
    )
    total_sales = vendor_orders_active.aggregate(total=Sum('subtotal'))['total'] or 0
    total_orders = vendor_orders_active.count()
    avg_order_value = float(total_sales) / total_orders if total_orders > 0 else 0.0
    
    return render(request, 'store/vendor_dashboard.html', {
        'products': products,
        'low_stock_products': low_stock_products,
        'total_sales': total_sales,
        'total_orders': total_orders,
        'avg_order_value': avg_order_value,
    })

@vendor_required
def vendor_product_form(request, product_id=None):
    product = get_object_or_404(Product, pk=product_id) if product_id else None
    if product and product.vendor != request.user:
        messages.error(request, 'You do not have permission to edit this product.')
        return redirect('vendor_dashboard')

    form = VendorProductForm(request.POST or None, request.FILES or None, instance=product)
    if request.method == 'POST' and form.is_valid():
        obj = form.save(commit=False)
        obj.vendor = request.user
        obj.is_active = True
        obj.save()
        messages.success(request, f'Product "{obj.name}" saved successfully.')
        return redirect('vendor_dashboard')

    return render(request, 'store/vendor_product_form.html', {'form': form, 'product': product})

@vendor_required
@require_POST
def vendor_product_delete(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    if product.vendor != request.user:
        messages.error(request, 'You do not have permission to delete this product.')
        return redirect('vendor_dashboard')
    
    # Soft archive instead of hard delete to preserve historical order references
    product.archive()
    messages.success(request, f'Product "{product.name}" archived successfully.')
    return redirect('vendor_dashboard')

@vendor_required
def vendor_orders(request):
    orders = VendorOrder.objects.filter(
        vendor=request.user
    ).select_related('order', 'order__user').prefetch_related('items', 'items__product').order_by('-created_at')
    return render(request, 'store/vendor_orders.html', {'orders': orders})

@vendor_required
@require_POST
def vendor_order_status_update(request, order_id):
    vendor_order = get_object_or_404(VendorOrder, id=order_id, vendor=request.user)
    new_status = request.POST.get('status')
    
    if not vendor_order.can_transition_to(new_status):
        messages.error(request, f'Cannot transition fulfillment #{vendor_order.id} from {vendor_order.get_status_display()} to {new_status}.')
        return redirect('vendor_orders')

    with transaction.atomic():
        vendor_order.status = new_status
        now = timezone.now()
        if new_status == 'confirmed':
            vendor_order.confirmed_at = now
        elif new_status == 'out_for_delivery':
            vendor_order.out_for_delivery_at = now
        elif new_status == 'delivered':
            vendor_order.delivered_at = now
        elif new_status == 'cancelled':
            vendor_order.cancelled_at = now
        vendor_order.save()

        OrderStatusHistory.objects.create(
            order=vendor_order.order,
            vendor_order=vendor_order,
            status=new_status,
            changed_by=request.user,
            note=f"Vendor '{request.user.username}' updated fulfillment status to {vendor_order.get_status_display()}."
        )

        # Sync parent order status based on all child fulfillments
        siblings = vendor_order.order.vendor_orders.all()
        statuses = set(siblings.values_list('status', flat=True))
        parent_order = vendor_order.order

        if statuses == {'delivered'}:
            parent_order.status = 'delivered'
            parent_order.delivered_at = now
            parent_order.save()
            OrderStatusHistory.objects.create(
                order=parent_order,
                status='delivered',
                changed_by=request.user,
                note="All vendor fulfillments delivered. Order fulfilled."
            )
        elif statuses == {'cancelled'}:
            parent_order.status = 'cancelled'
            parent_order.cancelled_at = now
            parent_order.save()
        elif 'out_for_delivery' in statuses and parent_order.status not in ['out_for_delivery', 'delivered']:
            parent_order.status = 'out_for_delivery'
            parent_order.out_for_delivery_at = now
            parent_order.save()
        elif all(s in ['confirmed', 'out_for_delivery', 'delivered'] for s in statuses) and parent_order.status == 'pending':
            parent_order.status = 'confirmed'
            parent_order.confirmed_at = now
            parent_order.save()

    messages.success(request, f'Fulfillment #{vendor_order.id} updated to {vendor_order.get_status_display()}.')
    return redirect('vendor_orders')
