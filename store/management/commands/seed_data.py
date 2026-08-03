from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, timedelta
from store.models import Category, Product, Coupon, DeliverySlot, Recipe


CATEGORIES = [
    {'name': 'Fruits', 'slug': 'fruits', 'icon': '🍎', 'description': 'Fresh seasonal fruits'},
    {'name': 'Vegetables', 'slug': 'vegetables', 'icon': '🥦', 'description': 'Farm-fresh vegetables'},
    {'name': 'Dairy', 'slug': 'dairy', 'icon': '🥛', 'description': 'Milk, cheese & dairy products'},
    {'name': 'Bakery', 'slug': 'bakery', 'icon': '🍞', 'description': 'Breads, cakes & pastries'},
    {'name': 'Beverages', 'slug': 'beverages', 'icon': '🧃', 'description': 'Juices, drinks & more'},
    {'name': 'Snacks', 'slug': 'snacks', 'icon': '🍿', 'description': 'Chips, nuts & munchies'},
]

PRODUCTS = [
    # Fruits
    {'category': 'fruits', 'name': 'Red Apples', 'price': 120, 'discount_price': 99, 'unit': 'kg', 'is_featured': True, 'recipe_tags': 'salad,smoothie,dessert', 'description': 'Crisp and juicy red apples, freshly sourced from Himachal Pradesh.'},
    {'category': 'fruits', 'name': 'Bananas', 'price': 40, 'unit': 'dozen', 'is_featured': True, 'recipe_tags': 'smoothie,dessert,snack', 'description': 'Sweet and ripe bananas, packed with natural energy.'},
    {'category': 'fruits', 'name': 'Mangoes', 'price': 180, 'discount_price': 149, 'unit': 'kg', 'is_featured': True, 'recipe_tags': 'smoothie,salad,dessert', 'description': 'Alphonso mangoes – the king of fruits.'},
    {'category': 'fruits', 'name': 'Watermelon', 'price': 80, 'unit': 'piece', 'recipe_tags': 'juice,salad', 'description': 'Refreshing watermelon, perfect for hot summer days.'},
    {'category': 'fruits', 'name': 'Grapes', 'price': 90, 'discount_price': 75, 'unit': 'kg', 'recipe_tags': 'salad,snack', 'description': 'Sweet seedless green grapes.'},
    # Vegetables
    {'category': 'vegetables', 'name': 'Spinach', 'price': 30, 'unit': 'piece', 'is_featured': True, 'recipe_tags': 'salad,curry,smoothie', 'description': 'Fresh green spinach, rich in iron and vitamins.'},
    {'category': 'vegetables', 'name': 'Tomatoes', 'price': 45, 'unit': 'kg', 'recipe_tags': 'curry,salad,pasta', 'description': 'Farm-fresh red tomatoes.'},
    {'category': 'vegetables', 'name': 'Onions', 'price': 35, 'unit': 'kg', 'recipe_tags': 'curry,salad', 'description': 'Red onions – a kitchen essential.'},
    {'category': 'vegetables', 'name': 'Potatoes', 'price': 30, 'unit': 'kg', 'is_featured': True, 'recipe_tags': 'curry,snack,fries', 'description': 'Versatile potatoes for all your cooking needs.'},
    {'category': 'vegetables', 'name': 'Broccoli', 'price': 60, 'unit': 'piece', 'recipe_tags': 'salad,stir-fry', 'description': 'Fresh broccoli florets, rich in fiber.'},
    {'category': 'vegetables', 'name': 'Carrots', 'price': 40, 'unit': 'kg', 'recipe_tags': 'salad,smoothie,curry', 'description': 'Crunchy orange carrots.'},
    # Dairy
    {'category': 'dairy', 'name': 'Full Cream Milk', 'price': 28, 'unit': 'litre', 'is_featured': True, 'recipe_tags': 'smoothie,dessert,tea', 'description': 'Fresh pasteurized full cream milk.'},
    {'category': 'dairy', 'name': 'Paneer', 'price': 90, 'discount_price': 79, 'unit': 'piece', 'is_featured': True, 'recipe_tags': 'curry,salad', 'description': 'Soft and fresh cottage cheese.'},
    {'category': 'dairy', 'name': 'Curd (Yogurt)', 'price': 45, 'unit': 'piece', 'recipe_tags': 'smoothie,raita,snack', 'description': 'Creamy homestyle curd, set fresh daily.'},
    {'category': 'dairy', 'name': 'Butter', 'price': 55, 'unit': 'piece', 'recipe_tags': 'dessert,baking', 'description': 'Amul salted butter.'},
    {'category': 'dairy', 'name': 'Cheese Slices', 'price': 120, 'discount_price': 99, 'unit': 'pack', 'recipe_tags': 'sandwich,snack', 'description': 'Processed cheese slices – 10 slices pack.'},
    # Bakery
    {'category': 'bakery', 'name': 'Whole Wheat Bread', 'price': 45, 'unit': 'piece', 'is_featured': True, 'recipe_tags': 'sandwich,snack,breakfast', 'description': 'Soft whole wheat loaf, freshly baked daily.'},
    {'category': 'bakery', 'name': 'Croissants', 'price': 60, 'discount_price': 49, 'unit': 'pack', 'recipe_tags': 'breakfast,snack', 'description': 'Buttery flaky croissants, pack of 4.'},
    {'category': 'bakery', 'name': 'Multigrain Biscuits', 'price': 40, 'unit': 'pack', 'recipe_tags': 'snack,tea', 'description': 'Crunchy multigrain biscuits.'},
    {'category': 'bakery', 'name': 'Chocolate Cake', 'price': 350, 'discount_price': 299, 'unit': 'piece', 'is_featured': True, 'recipe_tags': 'dessert', 'description': 'Rich dark chocolate birthday cake (500g).'},
    # Beverages
    {'category': 'beverages', 'name': 'Orange Juice', 'price': 80, 'unit': 'litre', 'is_featured': True, 'recipe_tags': 'juice,smoothie,breakfast', 'description': 'Fresh pressed 100% orange juice with no added sugar.'},
    {'category': 'beverages', 'name': 'Green Tea', 'price': 150, 'discount_price': 120, 'unit': 'pack', 'recipe_tags': 'tea,healthy', 'description': 'Premium Darjeeling green tea, 25 bags.'},
    {'category': 'beverages', 'name': 'Coconut Water', 'price': 50, 'unit': 'piece', 'recipe_tags': 'juice,healthy', 'description': 'Natural tender coconut water – tetrapack.'},
    # Snacks
    {'category': 'snacks', 'name': 'Mixed Nuts', 'price': 220, 'discount_price': 189, 'unit': 'pack', 'is_featured': True, 'recipe_tags': 'snack,salad', 'description': 'Premium mix of almonds, cashews and walnuts.'},
    {'category': 'snacks', 'name': 'Potato Chips', 'price': 30, 'unit': 'pack', 'recipe_tags': 'snack,fries', 'description': 'Classic salted potato chips, crispy and delicious.'},
    {'category': 'snacks', 'name': 'Dark Chocolate', 'price': 110, 'discount_price': 89, 'unit': 'piece', 'recipe_tags': 'dessert,snack', 'description': '70% dark chocolate bar with hints of vanilla.'},
]

COUPONS = [
    {'code': 'FRESH10', 'description': '10% off on all orders', 'discount_type': 'percentage', 'discount_value': 10, 'min_order': 200},
    {'code': 'SAVE50', 'description': 'Flat ₹50 off on orders above ₹500', 'discount_type': 'flat', 'discount_value': 50, 'min_order': 500},
    {'code': 'DAIRY15', 'description': '15% off – Dairy special', 'discount_type': 'percentage', 'discount_value': 15, 'min_order': 150},
    {'code': 'NEWUSER', 'description': 'New user special – 20% off', 'discount_type': 'percentage', 'discount_value': 20, 'min_order': 100},
    {'code': 'BIGBUY', 'description': 'Flat ₹100 off on orders above ₹1000', 'discount_type': 'flat', 'discount_value': 100, 'min_order': 1000},
]

RECIPES = [
    {'name': 'Fresh Fruit Smoothie', 'emoji': '🥤', 'description': 'A refreshing blend of banana, mango and milk for a perfect morning boost.', 'ingredients': 'smoothie,banana,mango,milk', 'prep_time': 5, 'servings': 2},
    {'name': 'Palak Paneer', 'emoji': '🍛', 'description': 'Classic Indian cottage cheese in a creamy spinach gravy.', 'ingredients': 'curry,paneer,spinach,tomato,onion', 'prep_time': 30, 'servings': 4},
    {'name': 'Garden Salad', 'emoji': '🥗', 'description': 'Crisp salad with fresh veggies, apples and a honey dressing.', 'ingredients': 'salad,apple,carrot,spinach,tomato', 'prep_time': 10, 'servings': 2},
    {'name': 'Banana Bread', 'emoji': '🍌', 'description': 'Moist and fluffy banana bread made with ripe bananas and butter.', 'ingredients': 'baking,banana,butter,dessert', 'prep_time': 60, 'servings': 8},
    {'name': 'Cheese Sandwich', 'emoji': '🥪', 'description': 'Quick and satisfying grilled cheese sandwich with whole wheat bread.', 'ingredients': 'sandwich,bread,cheese,butter', 'prep_time': 10, 'servings': 2},
    {'name': 'Mango Lassi', 'emoji': '🥛', 'description': 'Sweet and chilled mango yogurt drink – a classic summer treat.', 'ingredients': 'smoothie,mango,curd,milk', 'prep_time': 5, 'servings': 2},
    {'name': 'Aloo Curry', 'emoji': '🥔', 'description': 'Spiced potato curry with tomatoes and onions, pairs with roti or rice.', 'ingredients': 'curry,potato,tomato,onion', 'prep_time': 25, 'servings': 3},
    {'name': 'Mixed Nuts Trail Mix', 'emoji': '🥜', 'description': 'Quick energy-boosting snack mix with nuts and dark chocolate chunks.', 'ingredients': 'snack,nuts,chocolate', 'prep_time': 2, 'servings': 4},
]


class Command(BaseCommand):
    help = 'Seeds the database with sample grocery data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding FoodBasket database...')

        # Categories
        cat_map = {}
        for cat_data in CATEGORIES:
            cat, _ = Category.objects.get_or_create(
                slug=cat_data['slug'],
                defaults={
                    'name': cat_data['name'],
                    'icon': cat_data['icon'],
                    'description': cat_data['description'],
                }
            )
            cat_map[cat_data['slug']] = cat
        self.stdout.write(self.style.SUCCESS(f'  OK: {len(CATEGORIES)} categories created'))

        # Products
        for p in PRODUCTS:
            slug = p['name'].lower().replace(' ', '-').replace('(', '').replace(')', '')
            product, _ = Product.objects.get_or_create(
                slug=slug,
                defaults={
                    'category': cat_map[p['category']],
                    'name': p['name'],
                    'price': p['price'],
                    'discount_price': p.get('discount_price'),
                    'unit': p.get('unit', 'piece'),
                    'is_featured': p.get('is_featured', False),
                    'recipe_tags': p.get('recipe_tags', ''),
                    'description': p.get('description', ''),
                    'stock': 100,
                }
            )
        self.stdout.write(self.style.SUCCESS(f'  OK: {len(PRODUCTS)} products created'))

        # Coupons
        now = timezone.now()
        for c in COUPONS:
            Coupon.objects.get_or_create(
                code=c['code'],
                defaults={
                    'description': c['description'],
                    'discount_type': c['discount_type'],
                    'discount_value': c['discount_value'],
                    'min_order': c['min_order'],
                    'valid_from': now,
                    'valid_to': now + timedelta(days=365),
                    'max_uses': 1000,
                    'is_active': True,
                }
            )
        self.stdout.write(self.style.SUCCESS(f'  OK: {len(COUPONS)} coupons created'))

        # Delivery slots for next 7 days
        slots_created = 0
        for i in range(7):
            day = date.today() + timedelta(days=i)
            for slot_key in ['morning', 'afternoon', 'evening']:
                _, created = DeliverySlot.objects.get_or_create(
                    date=day,
                    slot=slot_key,
                    defaults={'max_orders': 20, 'current_bookings': 0}
                )
                if created:
                    slots_created += 1
        self.stdout.write(self.style.SUCCESS(f'  OK: {slots_created} delivery slots created'))

        # Recipes
        for r in RECIPES:
            Recipe.objects.get_or_create(
                name=r['name'],
                defaults={
                    'emoji': r['emoji'],
                    'description': r['description'],
                    'ingredients': r['ingredients'],
                    'prep_time': r['prep_time'],
                    'servings': r['servings'],
                }
            )
        self.stdout.write(self.style.SUCCESS(f'  OK: {len(RECIPES)} recipes created'))

        self.stdout.write(self.style.SUCCESS('FoodBasket seeded successfully!'))
