from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import Category, Product, Cart, CartItem, Coupon, DeliverySlot, Order, OrderItem, Recipe

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
    list_display  = ('name', 'category', 'price_display', 'discount_display', 'stock', 'featured_badge', 'recipe_tags')
    list_filter   = ('category', 'is_featured', 'unit')
    search_fields = ('name', 'description')
    list_editable = ('stock',)
    prepopulated_fields = {'slug': ('name',)}
    fieldsets = (
        ('Basic Info', {
            'fields': ('category', 'name', 'slug', 'description', 'image')
        }),
        ('Pricing & Stock', {
            'fields': ('price', 'discount_price', 'stock', 'unit')
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
    model  = OrderItem
    extra  = 0
    readonly_fields = ('product', 'product_name', 'quantity', 'price')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display  = ('id', 'user', 'status_badge', 'total_display', 'delivery_slot', 'created_at')
    list_filter   = ('status',)
    search_fields = ('user__username', 'address', 'phone')
    readonly_fields = ('user', 'subtotal', 'discount_amount', 'delivery_fee', 'total', 'created_at')
    inlines  = [OrderItemInline]
    ordering = ('-created_at',)
    fieldsets = (
        ('Order Info', {
            'fields': ('user', 'status', 'delivery_slot', 'coupon', 'notes')
        }),
        ('Delivery Address', {
            'fields': ('address', 'phone')
        }),
        ('Pricing', {
            'fields': ('subtotal', 'discount_amount', 'delivery_fee', 'total', 'created_at')
        }),
    )

    def status_badge(self, obj):
        colors = {
            'pending':          ('#fef3c7', '#d97706'),
            'confirmed':        ('#e8f8ee', '#1e7e4a'),
            'out_for_delivery': ('#dbeafe', '#1d4ed8'),
            'delivered':        ('#e8f8ee', '#1e7e4a'),
            'cancelled':        ('#fee2e2', '#dc2626'),
        }
        bg, fg = colors.get(obj.status, ('#f3f4f6', '#374151'))
        return format_html(
            '<span style="background:{};color:{};padding:2px 8px;border-radius:20px;font-size:.8rem;font-weight:700">{}</span>',
            bg, fg, obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def total_display(self, obj):
        return format_html('<strong style="color:#1e7e4a">₹{}</strong>', obj.total)
    total_display.short_description = 'Total'


# ── Recipe ────────────────────────────────────────────────────
@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display  = ('emoji', 'name', 'prep_time', 'servings', 'ingredients')
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
            'description': 'Enter comma-separated ingredient tags that match product recipe_tags (e.g. smoothie,banana,milk). The cart page uses these tags to suggest recipes.'
        }),
    )
