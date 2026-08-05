from django.urls import path
from . import views
from . import api_views
from . import vendor_views
from . import superadmin_views

urlpatterns = [
    path('', views.home, name='home'),

    # Products
    path('store/', views.product_list, name='product_list'),
    path('store/<slug:slug>/', views.product_list, name='category_products'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),

    # Cart
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/', views.update_cart, name='update_cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/apply-coupon/', views.apply_coupon, name='apply_coupon'),
    path('cart/remove-coupon/', views.remove_coupon, name='remove_coupon'),

    # Checkout, Account & Orders
    path('checkout/', views.checkout, name='checkout'),
    path('order/confirm/<int:order_id>/', views.order_confirm, name='order_confirm'),
    path('order/invoice/<int:order_id>/', views.order_invoice, name='order_invoice'),
    path('orders/', views.order_history, name='order_history'),
    path('orders/cancel/<int:order_id>/', views.cancel_order, name='cancel_order'),
    path('account/', views.account_view, name='account'),
    path('select-location/', views.select_location, name='select_location'),

    # Vendor portal routes
    path('vendor/login/', vendor_views.vendor_login, name='vendor_login'),
    path('vendor/register/', vendor_views.vendor_register, name='vendor_register'),
    path('vendor/pending/', vendor_views.vendor_pending, name='vendor_pending'),
    path('vendor/dashboard/', vendor_views.vendor_dashboard, name='vendor_dashboard'),
    path('vendor/products/new/', vendor_views.vendor_product_form, name='vendor_product_new'),
    path('vendor/products/<int:product_id>/edit/', vendor_views.vendor_product_form, name='vendor_product_edit'),
    path('vendor/products/<int:product_id>/delete/', vendor_views.vendor_product_delete, name='vendor_product_delete'),
    path('vendor/orders/', vendor_views.vendor_orders, name='vendor_orders'),
    path('vendor/orders/<int:order_id>/status-update/', vendor_views.vendor_order_status_update, name='vendor_order_status_update'),

    # Super Admin portal routes
    path('superadmin/login/', superadmin_views.superadmin_login, name='superadmin_login'),
    path('superadmin/dashboard/', superadmin_views.superadmin_dashboard, name='superadmin_dashboard'),
    path('superadmin/vendor/<int:vendor_id>/approve/', superadmin_views.superadmin_approve_vendor, name='superadmin_approve_vendor'),
    path('superadmin/vendor/<int:vendor_id>/reject/', superadmin_views.superadmin_reject_vendor, name='superadmin_reject_vendor'),
    path('superadmin/vendor/<int:vendor_id>/assign-area/', superadmin_views.superadmin_assign_area, name='superadmin_assign_area'),

    # Wishlist
    path('wishlist/', views.wishlist_view, name='wishlist'),
    path('wishlist/toggle/<int:product_id>/', views.toggle_wishlist, name='toggle_wishlist'),

    # Recipes
    path('recipes/', views.recipes_view, name='recipes'),

    # AJAX
    path('api/slots/', views.get_slots, name='get_slots'),
    path('api/search/autocomplete/', views.search_autocomplete, name='search_autocomplete'),
    path('api/location/set/', views.set_location, name='set_location'),
    path('api/location/reverse-geocode/', views.reverse_geocode, name='reverse_geocode'),

    # REST API endpoints (JWT protected)
    path('api/token/', api_views.api_token_obtain, name='api_token_obtain'),
    path('api/products/', api_views.api_products, name='api_products'),
    path('api/orders/', api_views.api_orders, name='api_orders'),
]
