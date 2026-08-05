from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Category, Product, UserProfile, Wishlist


class UpgradeFlowTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username='customer', password='secret', email='customer@example.com')
        self.vendor = User.objects.create_user(username='vendor', password='secret', email='vendor@example.com')
        self.vendor_profile = UserProfile.objects.get(user=self.vendor)
        self.vendor_profile.role = 'vendor'
        self.vendor_profile.save()

        from .models import VendorProfile
        VendorProfile.objects.create(
            user=self.vendor,
            shop_name="Test Shop",
            shop_address="Test Address",
            pincode="123456",
            status='approved'
        )

        self.category = Category.objects.create(name='Fruits', slug='fruits')
        self.product = Product.objects.create(
            category=self.category,
            name='Apple',
            slug='apple',
            price=10,
            stock=2,
            low_stock_threshold=5,
            vendor=self.vendor,
        )

    def test_low_stock_flag(self):
        self.assertTrue(self.product.is_low_stock)

    def test_wishlist_toggle(self):
        self.client.login(username='customer', password='secret')
        response = self.client.post(reverse('toggle_wishlist', args=[self.product.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Wishlist.objects.filter(user=self.user, product=self.product).exists())

    def test_vendor_dashboard_access(self):
        self.client.login(username='vendor', password='secret')
        response = self.client.get(reverse('vendor_dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_location_session_setting(self):
        response = self.client.post(reverse('set_location'), data='{"pincode": "123456"}', content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.session['user_pincode'], '123456')

    def test_location_filtering_products(self):
        session = self.client.session
        session['user_pincode'] = '123456'
        session.save()
        response = self.client.get(reverse('product_list'))
        self.assertContains(response, 'Apple')

        session = self.client.session
        session['user_pincode'] = '500032'
        session.save()
        response = self.client.get(reverse('product_list'))
        self.assertNotContains(response, 'Apple')

