from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.db.models import Sum

from .models import UserProfile, VendorProfile, Product, Order
from .views import get_or_create_profile
from functools import wraps

def superadmin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('superadmin_login')
        profile = get_or_create_profile(request.user)
        if not request.user.is_superuser and profile.role != 'superadmin':
            messages.error(request, 'Access denied. Only Super Admins can access this area.')
            logout(request)
            return redirect('superadmin_login')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def superadmin_login(request):
    if request.user.is_authenticated:
        profile = get_or_create_profile(request.user)
        if request.user.is_superuser or profile.role == 'superadmin':
            return redirect('superadmin_dashboard')
        return redirect('home')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        user = authenticate(request, username=username, password=password)
        if user is not None:
            profile = get_or_create_profile(user)
            if not user.is_superuser and profile.role != 'superadmin':
                messages.error(request, 'Access denied. You do not have Super Admin credentials.')
                return render(request, 'store/superadmin_login.html')
            
            login(request, user)
            messages.success(request, f'Welcome to Super Admin, {user.username}! 👑')
            return redirect('superadmin_dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'store/superadmin_login.html')

@superadmin_required
def superadmin_dashboard(request):
    pending_vendors = VendorProfile.objects.filter(status='pending').select_related('user')
    approved_vendors = VendorProfile.objects.filter(status='approved').select_related('user')
    rejected_vendors = VendorProfile.objects.filter(status='rejected').select_related('user')
    
    recent_orders = Order.objects.all().order_by('-created_at')[:10]
    total_sales = Order.objects.filter(status='delivered').aggregate(total=Sum('total'))['total'] or 0
    total_orders = Order.objects.count()
    total_users = User.objects.count()
    total_products = Product.objects.count()
    
    return render(request, 'store/superadmin_dashboard.html', {
        'pending_vendors': pending_vendors,
        'approved_vendors': approved_vendors,
        'rejected_vendors': rejected_vendors,
        'recent_orders': recent_orders,
        'total_sales': total_sales,
        'total_orders': total_orders,
        'total_users': total_users,
        'total_products': total_products,
    })

@superadmin_required
@require_POST
def superadmin_approve_vendor(request, vendor_id):
    vendor_profile = get_object_or_404(VendorProfile, id=vendor_id)
    vendor_profile.status = 'approved'
    vendor_profile.save()
    messages.success(request, f'Vendor "{vendor_profile.shop_name}" has been approved! ✅')
    return redirect('superadmin_dashboard')

@superadmin_required
@require_POST
def superadmin_reject_vendor(request, vendor_id):
    vendor_profile = get_object_or_404(VendorProfile, id=vendor_id)
    vendor_profile.status = 'rejected'
    vendor_profile.save()
    messages.warning(request, f'Vendor "{vendor_profile.shop_name}" has been rejected. ❌')
    return redirect('superadmin_dashboard')

@superadmin_required
@require_POST
def superadmin_assign_area(request, vendor_id):
    vendor_profile = get_object_or_404(VendorProfile, id=vendor_id)
    area = request.POST.get('assigned_area', '').strip()
    vendor_profile.assigned_area = area
    vendor_profile.save()
    messages.success(request, f'Assigned delivery area to "{vendor_profile.shop_name}". 📍')
    return redirect('superadmin_dashboard')
