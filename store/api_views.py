from django.http import JsonResponse
from django.contrib.auth import authenticate
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from functools import wraps
import json

from .models import Product, Order
from .jwt_utils import encode_jwt, decode_jwt

def jwt_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return JsonResponse({'error': 'Unauthorized. Missing or invalid Bearer token.'}, status=401)
        token = auth_header.split(' ')[1]
        payload = decode_jwt(token)
        if not payload:
            return JsonResponse({'error': 'Unauthorized. Token is invalid or expired.'}, status=401)
        try:
            request.jwt_user = User.objects.get(id=payload.get('user_id'))
        except User.DoesNotExist:
            return JsonResponse({'error': 'Unauthorized. User does not exist.'}, status=401)
        return view_func(request, *args, **kwargs)
    return wrapper

@csrf_exempt
def api_token_obtain(request):
    """
    POST API to obtain JWT token by passing username and password
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method is allowed.'}, status=405)
    try:
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
    except Exception:
        return JsonResponse({'error': 'Invalid JSON body.'}, status=400)

    if not username or not password:
        return JsonResponse({'error': 'Username and password are required.'}, status=400)

    user = authenticate(username=username, password=password)
    if user is not None:
        role = 'customer'
        if hasattr(user, 'profile'):
            role = user.profile.role
        elif user.is_superuser:
            role = 'superadmin'

        token = encode_jwt({'user_id': user.id, 'username': user.username, 'role': role})
        return JsonResponse({
            'token': token,
            'role': role,
            'username': user.username,
            'email': user.email
        })
    return JsonResponse({'error': 'Invalid credentials.'}, status=400)

def api_products(request):
    """
    Public endpoint to browse products
    """
    products = Product.objects.filter(stock__gt=0)
    data = []
    for p in products:
        data.append({
            'id': p.id,
            'name': p.name,
            'category': p.category.name,
            'price': float(p.price),
            'discount_price': float(p.discount_price) if p.discount_price else None,
            'effective_price': float(p.effective_price),
            'stock': p.stock,
            'unit': p.get_unit_display(),
            'image_url': p.image.url if p.image else None
        })
    return JsonResponse({'products': data})

@jwt_required
def api_orders(request):
    """
    Protected endpoint to view authenticated user's orders
    """
    orders = Order.objects.filter(user=request.jwt_user)
    data = []
    for o in orders:
        items = []
        for item in o.items.all():
            items.append({
                'product_name': item.product_name,
                'quantity': item.quantity,
                'price': float(item.price),
                'subtotal': float(item.subtotal)
            })
        data.append({
            'order_id': o.id,
            'status': o.get_status_display(),
            'total': float(o.total),
            'address': o.address,
            'phone': o.phone,
            'created_at': o.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'items': items
        })
    return JsonResponse({'orders': data})
