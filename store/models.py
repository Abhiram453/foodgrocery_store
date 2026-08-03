from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.text import slugify
from django.utils import timezone


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('customer', 'Customer'),
        ('vendor', 'Vendor'),
        ('admin', 'Admin'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')
    email_verified = models.BooleanField(default=False)
    phone = models.CharField(max_length=15, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} ({self.role})"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='🛒')

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Product(models.Model):
    UNIT_CHOICES = [
        ('kg', 'per kg'),
        ('piece', 'per piece'),
        ('litre', 'per litre'),
        ('pack', 'per pack'),
        ('dozen', 'per dozen'),
    ]
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    vendor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='products', null=True, blank=True)
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    discount_price = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    stock = models.PositiveIntegerField(default=100)
    low_stock_threshold = models.PositiveIntegerField(default=5)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES, default='piece')
    is_featured = models.BooleanField(default=False)
    recipe_tags = models.CharField(max_length=300, blank=True, help_text='Comma-separated tags e.g. salad,smoothie')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_featured', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def effective_price(self):
        return self.discount_price if self.discount_price else self.price

    @property
    def discount_percent(self):
        if self.discount_price and self.price:
            return int(((self.price - self.discount_price) / self.price) * 100)
        return 0

    def get_tags(self):
        return [t.strip().lower() for t in self.recipe_tags.split(',') if t.strip()]

    @property
    def is_low_stock(self):
        return self.stock <= self.low_stock_threshold


class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlist_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='wishlisted_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')

    def __str__(self):
        return f"{self.user.username} -> {self.product.name}"


class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    session_key = models.CharField(max_length=40, null=True, blank=True)
    coupon = models.ForeignKey('Coupon', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart ({self.user or self.session_key})"

    @property
    def subtotal(self):
        return sum(item.subtotal for item in self.items.all())

    @property
    def discount_amount(self):
        if not self.coupon:
            return 0
        if self.coupon.discount_type == 'percentage':
            return round(self.subtotal * self.coupon.discount_value / 100, 2)
        return min(self.coupon.discount_value, self.subtotal)

    @property
    def delivery_fee(self):
        return 0 if self.subtotal >= 500 else 40

    @property
    def total(self):
        return max(0, self.subtotal - self.discount_amount + self.delivery_fee)

    @property
    def item_count(self):
        return sum(item.quantity for item in self.items.all())


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity}x {self.product.name}"

    @property
    def subtotal(self):
        return self.product.effective_price * self.quantity


class Coupon(models.Model):
    DISCOUNT_TYPES = [
        ('percentage', 'Percentage'),
        ('flat', 'Flat Amount'),
    ]
    code = models.CharField(max_length=20, unique=True)
    description = models.CharField(max_length=200, blank=True)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPES)
    discount_value = models.DecimalField(max_digits=6, decimal_places=2)
    min_order = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    max_uses = models.PositiveIntegerField(default=100)
    used_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.code

    def is_valid(self, order_total):
        now = timezone.now()
        if not self.is_active:
            return False, "Coupon is inactive."
        if now < self.valid_from or now > self.valid_to:
            return False, "Coupon has expired."
        if self.used_count >= self.max_uses:
            return False, "Coupon usage limit reached."
        if order_total < self.min_order:
            return False, f"Minimum order ₹{self.min_order} required."
        return True, "Valid"


class DeliverySlot(models.Model):
    SLOT_CHOICES = [
        ('morning', '🌅 Morning (8 AM – 12 PM)'),
        ('afternoon', '☀️ Afternoon (12 PM – 5 PM)'),
        ('evening', '🌆 Evening (5 PM – 9 PM)'),
    ]
    date = models.DateField()
    slot = models.CharField(max_length=20, choices=SLOT_CHOICES)
    max_orders = models.PositiveIntegerField(default=20)
    current_bookings = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('date', 'slot')
        ordering = ['date', 'slot']

    def __str__(self):
        return f"{self.date} – {self.get_slot_display()}"

    @property
    def is_available(self):
        return self.current_bookings < self.max_orders

    @property
    def slots_remaining(self):
        return max(0, self.max_orders - self.current_bookings)


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', '⏳ Pending'),
        ('confirmed', '✅ Confirmed'),
        ('out_for_delivery', '🚚 Out for Delivery'),
        ('delivered', '📦 Delivered'),
        ('cancelled', '❌ Cancelled'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    delivery_slot = models.ForeignKey(DeliverySlot, on_delete=models.SET_NULL, null=True)
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    address = models.TextField()
    phone = models.CharField(max_length=15)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    delivery_fee = models.DecimalField(max_digits=6, decimal_places=2, default=40)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.id} – {self.user.username}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    product_name = models.CharField(max_length=200)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        return f"{self.quantity}x {self.product_name}"

    @property
    def subtotal(self):
        return self.price * self.quantity


class Recipe(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    ingredients = models.CharField(max_length=500, help_text='Comma-separated ingredient tags')
    image = models.ImageField(upload_to='recipes/', blank=True, null=True)
    prep_time = models.PositiveIntegerField(default=15, help_text='Minutes')
    servings = models.PositiveIntegerField(default=2)
    emoji = models.CharField(max_length=10, default='🍽️')

    def __str__(self):
        return self.name

    def get_ingredient_tags(self):
        return [t.strip().lower() for t in self.ingredients.split(',') if t.strip()]
