from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from datetime import date, timedelta

from .models import (
    Category, Product, Cart, CartItem, Coupon, DeliverySlot,
    Order, OrderItem, VendorOrder, VendorProfile, UserProfile,
    DeliveryArea, OrderStatusHistory, CustomerAddress, Wishlist
)
from .payment_utils import create_razorpay_order, verify_razorpay_payment


class MultiVendorMarketplaceTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.customer = User.objects.create_user(username='customer1', password='password123', email='cust@test.com')
        self.vendor1 = User.objects.create_user(username='vendor1', password='password123', email='v1@test.com')
        self.vendor2 = User.objects.create_user(username='vendor2', password='password123', email='v2@test.com')

        # Vendor Profiles
        vp1_profile = UserProfile.objects.get(user=self.vendor1)
        vp1_profile.role = 'vendor'
        vp1_profile.save()
        self.vp1 = VendorProfile.objects.create(
            user=self.vendor1, shop_name="Organic Farm", pincode="625001", status="approved"
        )

        vp2_profile = UserProfile.objects.get(user=self.vendor2)
        vp2_profile.role = 'vendor'
        vp2_profile.save()
        self.vp2 = VendorProfile.objects.create(
            user=self.vendor2, shop_name="Daily Dairy", pincode="625001", status="approved"
        )

        # Delivery Area
        self.area = DeliveryArea.objects.create(
            pincode="625001", area_name="Madurai Main", city="Madurai", state="Tamil Nadu", is_active=True
        )
        self.vp1.service_areas.add(self.area)
        self.vp2.service_areas.add(self.area)

        # Category & Products
        self.category = Category.objects.create(name="Produce", slug="produce")
        self.product1 = Product.objects.create(
            category=self.category, vendor=self.vendor1, name="Fresh Apples", slug="fresh-apples",
            price=100, discount_price=80, stock=20, is_active=True
        )
        self.product2 = Product.objects.create(
            category=self.category, vendor=self.vendor2, name="Full Cream Milk", slug="full-cream-milk",
            price=50, stock=30, is_active=True
        )

        # Delivery Slot
        self.slot = DeliverySlot.objects.create(
            date=date.today(), slot='morning', max_orders=10, current_bookings=0
        )

    def test_multi_vendor_atomic_checkout(self):
        """Checkout with products from 2 vendors creates 1 Order and 2 VendorOrders."""
        self.client.login(username='customer1', password='password123')
        
        # Add products to cart
        self.client.post(reverse('add_to_cart', args=[self.product1.id]), {'quantity': 2})
        self.client.post(reverse('add_to_cart', args=[self.product2.id]), {'quantity': 3})

        # Submit checkout with COD
        checkout_data = {
            'address': '12 Meenakshi Street',
            'pincode': '625001',
            'city': 'Madurai',
            'phone': '9876543210',
            'payment_method': 'COD',
            'slot_id': self.slot.id,
        }
        response = self.client.post(reverse('checkout'), checkout_data)
        self.assertEqual(response.status_code, 302)

        # Check Order
        order = Order.objects.filter(user=self.customer).first()
        self.assertIsNotNone(order)
        self.assertEqual(order.status, 'confirmed')
        self.assertEqual(order.delivery_pincode, '625001')

        # Check 2 distinct VendorOrder fulfillments
        vendor_orders = order.vendor_orders.all()
        self.assertEqual(vendor_orders.count(), 2)

        vo1 = vendor_orders.filter(vendor=self.vendor1).first()
        self.assertIsNotNone(vo1)
        self.assertEqual(vo1.subtotal, 160)  # 2 * 80
        self.assertEqual(vo1.status, 'confirmed')

        vo2 = vendor_orders.filter(vendor=self.vendor2).first()
        self.assertIsNotNone(vo2)
        self.assertEqual(vo2.subtotal, 150)  # 3 * 50
        self.assertEqual(vo2.status, 'confirmed')

        # Check Stock Deductions
        self.product1.refresh_from_db()
        self.product2.refresh_from_db()
        self.assertEqual(self.product1.stock, 18)
        self.assertEqual(self.product2.stock, 27)

        # Check Slot Bookings
        self.slot.refresh_from_db()
        self.assertEqual(self.slot.current_bookings, 1)

    def test_vendor_order_isolation_and_state_machine(self):
        """Vendor 1 can transition their own fulfillment, but cannot touch Vendor 2's fulfillment."""
        # Create an Order with fulfillments
        order = Order.objects.create(
            user=self.customer, address="Test Addr", phone="9876543210",
            delivery_pincode="625001", subtotal=200, total=240, status="confirmed"
        )
        vo1 = VendorOrder.objects.create(order=order, vendor=self.vendor1, subtotal=100, status="confirmed")
        vo2 = VendorOrder.objects.create(order=order, vendor=self.vendor2, subtotal=100, status="confirmed")

        # Login Vendor 1
        self.client.login(username='vendor1', password='password123')

        # Vendor 1 accesses orders
        res = self.client.get(reverse('vendor_orders'))
        self.assertContains(res, f"VO-{vo1.id}")
        self.assertNotContains(res, f"VO-{vo2.id}")

        # Vendor 1 transitions vo1 from confirmed to out_for_delivery
        res = self.client.post(reverse('vendor_order_status_update', args=[vo1.id]), {'status': 'out_for_delivery'})
        self.assertEqual(res.status_code, 302)
        vo1.refresh_from_db()
        self.assertEqual(vo1.status, 'out_for_delivery')

        # Vendor 1 attempts to modify Vendor 2's fulfillment -> 404 forbidden/not found
        res = self.client.post(reverse('vendor_order_status_update', args=[vo2.id]), {'status': 'delivered'})
        self.assertEqual(res.status_code, 404)
        vo2.refresh_from_db()
        self.assertEqual(vo2.status, 'confirmed')

        # Invalid transition test: vo1 cannot jump backwards from out_for_delivery to pending
        res = self.client.post(reverse('vendor_order_status_update', args=[vo1.id]), {'status': 'pending'})
        vo1.refresh_from_db()
        self.assertEqual(vo1.status, 'out_for_delivery')  # Rejected by can_transition_to

    def test_atomic_order_cancellation(self):
        """Customer cancels order: stock, slot capacity, and child vendor orders are restored/cancelled."""
        order = Order.objects.create(
            user=self.customer, address="Test Addr", phone="9876543210",
            delivery_slot=self.slot, subtotal=160, total=200, status="confirmed"
        )
        self.slot.current_bookings = 1
        self.slot.save()
        
        vo1 = VendorOrder.objects.create(order=order, vendor=self.vendor1, subtotal=160, status="confirmed")
        OrderItem.objects.create(
            order=order, vendor=self.vendor1, vendor_order=vo1, product=self.product1,
            product_name=self.product1.name, quantity=5, price=80
        )
        self.product1.stock = 15
        self.product1.save()

        self.client.login(username='customer1', password='password123')
        res = self.client.post(reverse('cancel_order', args=[order.id]))
        self.assertEqual(res.status_code, 302)

        order.refresh_from_db()
        self.assertEqual(order.status, 'cancelled')

        vo1.refresh_from_db()
        self.assertEqual(vo1.status, 'cancelled')

        self.product1.refresh_from_db()
        self.assertEqual(self.product1.stock, 20)  # Restored from 15 to 20

        self.slot.refresh_from_db()
        self.assertEqual(self.slot.current_bookings, 0)  # Restored

    def test_unserviceable_pincode_rejected_at_checkout(self):
        """Checkout fails if customer enters an invalid pincode format."""
        self.client.login(username='customer1', password='password123')
        self.client.post(reverse('add_to_cart', args=[self.product1.id]), {'quantity': 1})

        checkout_data = {
            'address': 'Non-serviced area address',
            'pincode': '000000',  # Invalid pincode format (starts with 0)
            'city': 'Unknown',
            'phone': '9876543210',
            'payment_method': 'COD',
        }
        res = self.client.post(reverse('checkout'), checkout_data)
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'valid 6-digit Indian delivery pincode')
        self.assertEqual(Order.objects.count(), 0)

    def test_product_soft_archiving(self):
        """Archiving product sets is_active=False without deleting existing order item links."""
        order = Order.objects.create(
            user=self.customer, address="Test", phone="9876543210",
            subtotal=80, total=120, status="confirmed"
        )
        item = OrderItem.objects.create(
            order=order, product=self.product1, product_name=self.product1.name,
            quantity=1, price=80
        )

        # Archive product
        self.product1.archive()
        self.assertFalse(self.product1.is_active)

        # Historical order item remains intact
        item.refresh_from_db()
        self.assertEqual(item.product, self.product1)

        # Inactive product excluded from catalog listing
        res = self.client.get(reverse('product_list'))
        self.assertNotContains(res, 'Fresh Apples')

    def test_razorpay_verification_endpoint(self):
        """verify_razorpay_payment_view validates signature and marks Order and VendorOrders confirmed."""
        order = Order.objects.create(
            user=self.customer, address="Test", phone="9876543210",
            payment_method="RAZORPAY", payment_status="pending",
            subtotal=80, total=120, status="pending"
        )
        vo = VendorOrder.objects.create(order=order, vendor=self.vendor1, subtotal=80, status="pending")

        self.client.login(username='customer1', password='password123')
        verify_payload = {
            'order_id': order.id,
            'razorpay_order_id': f'order_mock_{order.id}',
            'razorpay_payment_id': 'pay_mock_123',
            'razorpay_signature': 'sig_mock_123',
        }
        res = self.client.post(
            reverse('verify_razorpay_payment'),
            data=verify_payload,
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json().get('success'))

        order.refresh_from_db()
        self.assertEqual(order.payment_status, 'paid')
        self.assertEqual(order.status, 'confirmed')

        vo.refresh_from_db()
        self.assertEqual(vo.status, 'confirmed')

        # Check OrderStatusHistory
        history = OrderStatusHistory.objects.filter(order=order)
        self.assertTrue(history.exists())


class DeliveryLocationAndServiceabilityTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.customer = User.objects.create_user(username='cust_loc', password='password123', email='loc@test.com')
        self.vendor_madurai = User.objects.create_user(username='vend_mdu', password='password123', email='vmdu@test.com')
        self.vendor_chennai = User.objects.create_user(username='vend_chn', password='password123', email='vchn@test.com')

        # Vendor Profiles
        p1 = UserProfile.objects.get(user=self.vendor_madurai)
        p1.role = 'vendor'
        p1.save()
        self.vp_madurai = VendorProfile.objects.create(
            user=self.vendor_madurai, shop_name="Madurai Fresh", pincode="625001", status="approved"
        )

        p2 = UserProfile.objects.get(user=self.vendor_chennai)
        p2.role = 'vendor'
        p2.save()
        self.vp_chennai = VendorProfile.objects.create(
            user=self.vendor_chennai, shop_name="Chennai Agro", pincode="600001", status="approved"
        )

        # Active Delivery Areas
        self.area_madurai = DeliveryArea.objects.create(
            pincode="625001", area_name="Madurai Main", city="Madurai", state="Tamil Nadu",
            latitude=9.9252, longitude=78.1198, delivery_fee=30, minimum_order_value=150,
            estimated_delivery_minutes=45, is_active=True
        )
        self.area_pudur = DeliveryArea.objects.create(
            pincode="625020", area_name="K.Pudur", city="Madurai", state="Tamil Nadu",
            latitude=9.9480, longitude=78.1460, delivery_fee=35, minimum_order_value=200,
            estimated_delivery_minutes=50, is_active=True
        )

        # Assign area to Madurai vendor only
        self.vp_madurai.service_areas.add(self.area_madurai)

        # Category and Products
        self.category = Category.objects.create(name="Greens", slug="greens")
        self.prod_mdu = Product.objects.create(
            category=self.category, vendor=self.vendor_madurai, name="Madurai Spinach", slug="madurai-spinach",
            price=40, stock=50, is_active=True
        )
        self.prod_chn = Product.objects.create(
            category=self.category, vendor=self.vendor_chennai, name="Chennai Mangoes", slug="chennai-mangoes",
            price=250, stock=20, is_active=True
        )

    def test_clean_pincode_validation(self):
        from .services.geocoding import clean_pincode
        self.assertEqual(clean_pincode("625001"), "625001")
        self.assertEqual(clean_pincode(" 625020 "), "625020")
        self.assertIsNone(clean_pincode("012345"))  # Indian pincodes start with 1-9
        self.assertIsNone(clean_pincode("12345"))   # 5 digits
        self.assertIsNone(clean_pincode("ABCDEF"))
        self.assertIsNone(clean_pincode(None))

    def test_serviceability_check_active_pincode(self):
        from .services.geocoding import check_pincode_serviceability
        result = check_pincode_serviceability("625001")
        self.assertTrue(result['success'])
        self.assertTrue(result['is_serviceable'])
        self.assertEqual(result['pincode'], "625001")
        self.assertEqual(result['area_name'], "Madurai Main")
        self.assertEqual(result['city'], "Madurai")
        self.assertEqual(result['delivery_fee'], 30)
        self.assertEqual(result['minimum_order_value'], 150)
        self.assertEqual(result['estimated_delivery_minutes'], 45)
        self.assertEqual(result['approved_vendors_count'], 1)

    def test_serviceability_check_dynamic_registration(self):
        from .services.geocoding import check_pincode_serviceability
        result = check_pincode_serviceability("560001", area_name="Indiranagar", city="Bengaluru")
        self.assertTrue(result['success'])
        self.assertTrue(result['is_serviceable'])
        self.assertEqual(result['pincode'], "560001")
        self.assertEqual(result['area_name'], "Indiranagar")

    def test_check_pincode_api(self):
        # Valid active pincode
        res = self.client.get(reverse('check_pincode_api') + '?pincode=625001')
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data['success'])
        self.assertTrue(data['is_serviceable'])
        self.assertEqual(data['area_name'], 'Madurai Main')

        # Invalid pincode format (non-numeric / invalid length)
        res2 = self.client.get(reverse('check_pincode_api') + '?pincode=ABC')
        self.assertEqual(res2.status_code, 400)
        data2 = res2.json()
        self.assertFalse(data2['success'])
        self.assertFalse(data2['is_serviceable'])

    def test_set_location_api(self):
        # Setting valid serviceable location
        res = self.client.post(reverse('set_location'), {'pincode': '625001'})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data['success'])
        self.assertEqual(self.client.session.get('user_pincode'), '625001')
        self.assertEqual(self.client.session.get('delivery_area_id'), self.area_madurai.id)

        # Attempting to set invalid pincode format
        res2 = self.client.post(reverse('set_location'), {'pincode': 'invalid'})
        self.assertEqual(res2.status_code, 400)
        data2 = res2.json()
        self.assertFalse(data2['success'])

    def test_reverse_geocode_out_of_bounds(self):
        from .services.geocoding import reverse_geocode
        res = reverse_geocode(999.0, 999.0)
        self.assertFalse(res['success'])
        self.assertEqual(res['error_type'], 'out_of_bounds')

    def test_location_filtered_products(self):
        # Set session to Madurai 625001
        session = self.client.session
        session['user_pincode'] = '625001'
        session['delivery_area_id'] = self.area_madurai.id
        session.save()

        # Product list view should include Madurai vendor and exclude Chennai vendor
        res = self.client.get(reverse('product_list'))
        self.assertContains(res, 'Madurai Spinach')
        self.assertNotContains(res, 'Chennai Mangoes')

    def test_cart_serviceability_and_minimum_order_validation(self):
        self.client.login(username='cust_loc', password='password123')
        
        # Set delivery location to Madurai Main (min order 150)
        session = self.client.session
        session['user_pincode'] = '625001'
        session['delivery_area_id'] = self.area_madurai.id
        session.save()

        # Add 1 spinach (₹40, below min order of 150)
        self.client.post(reverse('add_to_cart', args=[self.prod_mdu.id]), {'quantity': 1})

        # Checkout should fail due to minimum order value requirement and redirect to cart
        checkout_data = {
            'address': '7 Temple Road',
            'pincode': '625001',
            'city': 'Madurai',
            'phone': '9876543210',
            'payment_method': 'COD',
        }
        res = self.client.post(reverse('checkout'), checkout_data, follow=True)
        self.assertEqual(res.status_code, 200)
        self.assertRedirects(res, reverse('cart'))
        self.assertContains(res, 'The minimum order value')
        self.assertEqual(Order.objects.count(), 0)

    def test_product_and_order_item_image_urls(self):
        """Products and OrderItems must provide image URLs rather than emoji icons."""
        # Check product image url
        self.assertTrue(self.prod_mdu.image_url.startswith('/static/images/'))
        self.assertTrue(self.prod_mdu.image_url.endswith('.svg') or self.prod_mdu.image_url.endswith('.jpg'))

        # Check OrderItem image url
        order = Order.objects.create(
            user=self.customer, address="Test", phone="9876543210",
            subtotal=40, total=70, status="confirmed"
        )
        item = OrderItem.objects.create(
            order=order, product=self.prod_mdu, product_name=self.prod_mdu.name,
            quantity=1, price=40
        )
        self.assertEqual(item.image_url, self.prod_mdu.image_url)


