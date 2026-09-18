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
        """Checkout fails if vendor does not serve customer's pincode."""
        self.client.login(username='customer1', password='password123')
        self.client.post(reverse('add_to_cart', args=[self.product1.id]), {'quantity': 1})

        checkout_data = {
            'address': 'Non-serviced area address',
            'pincode': '999999',  # Unserviced pincode
            'city': 'Unknown',
            'phone': '9876543210',
            'payment_method': 'COD',
        }
        res = self.client.post(reverse('checkout'), checkout_data)
        # Should stay on checkout page with error message
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'does not deliver to pincode 999999')
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
