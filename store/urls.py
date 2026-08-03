from django.urls import path
from . import views

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
    path('orders/', views.order_history, name='order_history'),
    path('orders/cancel/<int:order_id>/', views.cancel_order, name='cancel_order'),
    path('account/', views.account_view, name='account'),

    # Vendor / wishlist
    path('vendor/dashboard/', views.vendor_dashboard, name='vendor_dashboard'),
    path('vendor/products/new/', views.vendor_product_form, name='vendor_product_new'),
    path('vendor/products/<int:product_id>/edit/', views.vendor_product_form, name='vendor_product_edit'),
    path('vendor/products/<int:product_id>/delete/', views.vendor_product_delete, name='vendor_product_delete'),
    path('wishlist/', views.wishlist_view, name='wishlist'),
    path('wishlist/toggle/<int:product_id>/', views.toggle_wishlist, name='toggle_wishlist'),

    # Recipes
    path('recipes/', views.recipes_view, name='recipes'),

    # AJAX
    path('api/slots/', views.get_slots, name='get_slots'),
]
