from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import (
    Category, Product, Cart, CartItem, Coupon, DeliverySlot,
    Order, OrderItem, Recipe, DeliveryArea, VendorProfile,
    VendorOrder, OrderStatusHistory, CustomerAddress, Wishlist
)

# ── Admin site branding ────────────────────────────────────────
admin.site.site_header  = "🛒 FoodBasket Admin"
admin.site.site_title   = "FoodBasket"
admin.site.index_title  = "Manage Your Store"


# ── Category ──────────────────────────────────────────────────
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display  = ('icon', 'name', 'slug', 'product_count', 'description')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)

    def product_count(self, obj):
        count = obj.products.count()
        return format_html('<strong>{}</strong>', count)
    product_count.short_description = 'Products'


# ── Product ───────────────────────────────────────────────────
class ProductAdmin(admin.ModelAdmin):
    list_display  = ('name', 'vendor', 'category', 'price_display', 'discount_display', 'stock', 'is_active', 'featured_badge')
    list_filter   = ('is_active', 'is_featured', 'category', 'unit')
    search_fields = ('name', 'description', 'vendor__username')
    list_editable = ('stock', 'is_active')
    prepopulated_fields = {'slug': ('name',)}
    fieldsets = (
        ('Basic Info', {
            'fields': ('vendor', 'category', 'name', 'slug', 'description', 'image', 'is_active')
        }),
        ('Pricing & Stock', {
            'fields': ('price', 'discount_price', 'stock', 'low_stock_threshold', 'unit')
        }),
        ('Display & Recipes', {
            'fields': ('is_featured', 'recipe_tags'),
            'description': 'Tick "Is Featured" to show on homepage. Recipe tags are comma-separated keywords (e.g. salad,smoothie,curry).'
        }),
    )


    def price_display(self, obj):
        return format_html('<span style="color:#1e7e4a;font-weight:700">₹{}</span>', obj.price)
    price_display.short_description = 'Price'

    def discount_display(self, obj):
        if obj.discount_price:
            return format_html('<span style="color:#f97316;font-weight:700">₹{}</span>', obj.discount_price)
        return '—'
    discount_display.short_description = 'Sale Price'

    def featured_badge(self, obj):
        if obj.is_featured:
            return mark_safe('<span style="background:#e8f8ee;color:#1e7e4a;padding:2px 8px;border-radius:20px;font-size:.8rem;font-weight:700">Featured</span>')
        return '—'
    featured_badge.short_description = 'Featured'

admin.site.register(Product, ProductAdmin)


# ── Cart ──────────────────────────────────────────────────────
class CartItemInline(admin.TabularInline):
    model   = CartItem
    extra   = 0
    readonly_fields = ('product', 'quantity')

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'session_key', 'coupon', 'updated_at')
    inlines      = [CartItemInline]
    readonly_fields = ('user', 'session_key', 'created_at', 'updated_at')


# ── Coupon ────────────────────────────────────────────────────
@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display  = ('code', 'description', 'discount_type', 'discount_value', 'min_order', 'valid_from', 'valid_to', 'used_count', 'status_badge')
    list_filter   = ('discount_type', 'is_active')
    search_fields = ('code', 'description')
    fieldsets = (
        ('Coupon Details', {
            'fields': ('code', 'description', 'is_active'),
            'description': 'The code customers will type at checkout.'
        }),
        ('Discount', {
            'fields': ('discount_type', 'discount_value', 'min_order'),
            'description': 'Choose "Percentage" for % off, "Flat Amount" for fixed ₹ off.'
        }),
        ('Validity', {
            'fields': ('valid_from', 'valid_to', 'max_uses'),
        }),
    )

    def status_badge(self, obj):
        from django.utils import timezone
        now = timezone.now()
        if not obj.is_active:
            return mark_safe('<span style="background:#fee2e2;color:#dc2626;padding:2px 8px;border-radius:20px;font-size:.8rem;font-weight:700">Inactive</span>')
        if now < obj.valid_from or now > obj.valid_to:
            return mark_safe('<span style="background:#fef3c7;color:#d97706;padding:2px 8px;border-radius:20px;font-size:.8rem;font-weight:700">Expired</span>')
        if obj.used_count >= obj.max_uses:
            return mark_safe('<span style="background:#fee2e2;color:#dc2626;padding:2px 8px;border-radius:20px;font-size:.8rem;font-weight:700">Limit Reached</span>')
        return mark_safe('<span style="background:#e8f8ee;color:#1e7e4a;padding:2px 8px;border-radius:20px;font-size:.8rem;font-weight:700">Active</span>')
    status_badge.short_description = 'Status'


# ── Delivery Slot ─────────────────────────────────────────────
@admin.register(DeliverySlot)
class DeliverySlotAdmin(admin.ModelAdmin):
    list_display  = ('date', 'slot_display', 'max_orders', 'current_bookings', 'remaining', 'availability_badge')
    list_filter   = ('slot', 'date')
    ordering      = ('date', 'slot')
    list_editable = ('max_orders',)

    def slot_display(self, obj):
        return obj.get_slot_display()
    slot_display.short_description = 'Time Slot'

    def remaining(self, obj):
        return obj.slots_remaining
    remaining.short_description = 'Remaining'

    def availability_badge(self, obj):
        if obj.is_available:
            return mark_safe('<span style="background:#e8f8ee;color:#1e7e4a;padding:2px 8px;border-radius:20px;font-size:.8rem;font-weight:700">Open</span>')
        return mark_safe('<span style="background:#fee2e2;color:#dc2626;padding:2px 8px;border-radius:20px;font-size:.8rem;font-weight:700">Full</span>')
    availability_badge.short_description = 'Status'


# ── Order ─────────────────────────────────────────────────────
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'vendor', 'vendor_order', 'product_name', 'quantity', 'price')


class VendorOrderInline(admin.TabularInline):
    model = VendorOrder
    extra = 0
    readonly_fields = ('vendor', 'subtotal', 'status', 'created_at')


class OrderStatusHistoryInline(admin.TabularInline):
    model = OrderStatusHistory
    extra = 0
    readonly_fields = ('vendor_order', 'status', 'changed_by', 'timestamp', 'note')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status_badge', 'payment_status_badge', 'total_display', 'delivery_slot', 'created_at')
    list_filter = ('status', 'payment_status', 'payment_method')
    search_fields = ('user__username', 'address', 'phone', 'delivery_pincode', 'razorpay_order_id', 'payment_id')
    readonly_fields = ('user', 'subtotal', 'discount_amount', 'delivery_fee', 'total', 'created_at', 'razorpay_order_id', 'payment_id', 'paid_at')
    inlines = [VendorOrderInline, OrderItemInline, OrderStatusHistoryInline]
    ordering = ('-created_at',)
    fieldsets = (
        ('Order Info', {
            'fields': ('user', 'status', 'delivery_slot', 'coupon', 'notes')
        }),
        ('Payment', {
            'fields': ('payment_method', 'payment_status', 'payment_id', 'razorpay_order_id', 'paid_at')
        }),
        ('Delivery Address', {
            'fields': ('delivery_address', 'delivery_pincode', 'delivery_city', 'delivery_phone', 'address', 'phone')
        }),
        ('Pricing & Timestamps', {
            'fields': ('subtotal', 'discount_amount', 'delivery_fee', 'total', 'created_at', 'confirmed_at', 'out_for_delivery_at', 'delivered_at', 'cancelled_at')
        }),
    )

    def status_badge(self, obj):
        colors = {
            'pending': ('#fef3c7', '#d97706'),
            'confirmed': ('#e8f8ee', '#1e7e4a'),
            'out_for_delivery': ('#dbeafe', '#1d4ed8'),
            'delivered': ('#e8f8ee', '#1e7e4a'),
            'cancelled': ('#fee2e2', '#dc2626'),
        }
        bg, fg = colors.get(obj.status, ('#f3f4f6', '#374151'))
        return format_html(
            '<span style="background:{};color:{};padding:2px 8px;border-radius:20px;font-size:.8rem;font-weight:700">{}</span>',
            bg, fg, obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def payment_status_badge(self, obj):
        colors = {
            'pending': ('#fef3c7', '#d97706'),
            'paid': ('#e8f8ee', '#1e7e4a'),
            'failed': ('#fee2e2', '#dc2626'),
            'refunded': ('#e0e7ff', '#4338ca'),
        }
        bg, fg = colors.get(obj.payment_status, ('#f3f4f6', '#374151'))
        return format_html(
            '<span style="background:{};color:{};padding:2px 8px;border-radius:20px;font-size:.8rem;font-weight:700">{} ({})</span>',
            bg, fg, obj.get_payment_status_display(), obj.payment_method
        )
    payment_status_badge.short_description = 'Payment'

    def total_display(self, obj):
        return format_html('<strong style="color:#1e7e4a">₹{}</strong>', obj.total)
    total_display.short_description = 'Total'


# ── Vendor Order ──────────────────────────────────────────────
@admin.register(VendorOrder)
class VendorOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'vendor', 'subtotal', 'status_badge', 'created_at')
    list_filter = ('status', 'vendor')
    search_fields = ('order__id', 'vendor__username', 'vendor__vendor_profile__shop_name')

    def status_badge(self, obj):
        colors = {
            'pending': ('#fef3c7', '#d97706'),
            'confirmed': ('#e8f8ee', '#1e7e4a'),
            'out_for_delivery': ('#dbeafe', '#1d4ed8'),
            'delivered': ('#e8f8ee', '#1e7e4a'),
            'cancelled': ('#fee2e2', '#dc2626'),
        }
        bg, fg = colors.get(obj.status, ('#f3f4f6', '#374151'))
        return format_html(
            '<span style="background:{};color:{};padding:2px 8px;border-radius:20px;font-size:.8rem;font-weight:700">{}</span>',
            bg, fg, obj.get_status_display()
        )
    status_badge.short_description = 'Status'


# ── Vendor Profile ────────────────────────────────────────────
@admin.register(VendorProfile)
class VendorProfileAdmin(admin.ModelAdmin):
    list_display = ('shop_name', 'user', 'status_badge', 'pincode', 'service_areas_count', 'created_at')
    list_filter = ('status',)
    search_fields = ('shop_name', 'user__username', 'pincode', 'assigned_area')
    filter_horizontal = ('service_areas',)

    def status_badge(self, obj):
        colors = {
            'pending': ('#fef3c7', '#d97706'),
            'approved': ('#e8f8ee', '#1e7e4a'),
            'rejected': ('#fee2e2', '#dc2626'),
        }
        bg, fg = colors.get(obj.status, ('#f3f4f6', '#374151'))
        return format_html(
            '<span style="background:{};color:{};padding:2px 8px;border-radius:20px;font-size:.8rem;font-weight:700">{}</span>',
            bg, fg, obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def service_areas_count(self, obj):
        return obj.service_areas.count()
    service_areas_count.short_description = 'Service Areas'


# ── Delivery Area ─────────────────────────────────────────────
@admin.register(DeliveryArea)
class DeliveryAreaAdmin(admin.ModelAdmin):
    list_display = (
        'pincode', 'area_name', 'city', 'state',
        'delivery_fee_display', 'min_order_display',
        'estimated_delivery_minutes', 'vendors_count', 'is_active'
    )
    list_filter = ('city', 'state', 'is_active')
    search_fields = ('pincode', 'area_name', 'city')
    list_editable = ('is_active',)
    fieldsets = (
        ('Area Details', {
            'fields': ('pincode', 'area_name', 'city', 'state', 'is_active')
        }),
        ('Coordinates (Geofencing & Reverse Geocoding)', {
            'fields': ('latitude', 'longitude'),
            'description': 'Latitude and Longitude in decimal degrees (e.g. 9.9252, 78.1198)'
        }),
        ('Delivery Rates & SLA Estimates', {
            'fields': ('delivery_fee', 'minimum_order_value', 'estimated_delivery_minutes'),
            'description': 'Default delivery fee, minimum basket threshold, and estimated minutes for delivery.'
        }),
    )

    def delivery_fee_display(self, obj):
        return format_html('<span style="font-weight:700;color:#1e7e4a">₹{}</span>', obj.delivery_fee)
    delivery_fee_display.short_description = 'Fee'

    def min_order_display(self, obj):
        return format_html('<span>₹{}</span>', obj.minimum_order_value)
    min_order_display.short_description = 'Min Order'

    def vendors_count(self, obj):
        count = obj.vendors.filter(status='approved').count()
        return format_html('<strong>{}</strong>', count)
    vendors_count.short_description = 'Active Vendors'


# ── Customer Address ──────────────────────────────────────────
@admin.register(CustomerAddress)
class CustomerAddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'label', 'full_address', 'pincode', 'city', 'phone', 'is_default')
    list_filter = ('city', 'is_default')
    search_fields = ('user__username', 'pincode', 'phone')


# ── Order Status History ──────────────────────────────────────
@admin.register(OrderStatusHistory)
class OrderStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ('order', 'vendor_order', 'status', 'changed_by', 'timestamp', 'note')
    list_filter = ('status', 'timestamp')
    search_fields = ('order__id', 'changed_by__username', 'note')


# ── Wishlist ──────────────────────────────────────────────────
@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'created_at')
    search_fields = ('user__username', 'product__name')


# ── Recipe ────────────────────────────────────────────────────
@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('emoji', 'name', 'prep_time', 'servings', 'ingredients')
    search_fields = ('name', 'ingredients')
    fieldsets = (
        ('Recipe Details', {
            'fields': ('name', 'emoji', 'description', 'image'),
        }),
        ('Info', {
            'fields': ('prep_time', 'servings'),
        }),
        ('Ingredient Tags', {
            'fields': ('ingredients',),
            'description': 'Enter comma-separated ingredient tags that match product recipe_tags (e.g. smoothie,banana,milk).'
        }),
    )

