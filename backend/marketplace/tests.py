from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from marketplace.models import Cart, Category, CustomerProfile, Order, ProducerProfile, Product


class MarketplaceFlowTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.category = Category.objects.create(name='Vegetables', slug='vegetables')
        self.producer_user = User.objects.create_user(username='producer1', password='Pass1234')
        self.customer_user = User.objects.create_user(username='customer1', password='Pass1234')
        self.staff_user = User.objects.create_user(username='admin1', password='Pass1234', is_staff=True)
        self.producer = ProducerProfile.objects.create(user=self.producer_user, business_name='Bristol Valley Farm', postcode='BS1 4DJ')
        self.customer = CustomerProfile.objects.create(user=self.customer_user, address='45 Park Street, Bristol', postcode='BS1 5JG')
        Cart.objects.create(customer=self.customer)
        self.product = Product.objects.create(
            producer=self.producer,
            category=self.category,
            name='Organic Carrots',
            description='Fresh carrots',
            price=Decimal('2.50'),
            stock_quantity=20,
            availability='available',
        )

    def login_customer(self):
        self.client.force_login(self.customer_user)

    def login_producer(self):
        self.client.force_login(self.producer_user)

    def login_admin(self):
        self.client.force_login(self.staff_user)

    def test_product_browse(self):
        response = self.client.get('/api/products/?visible_only=true')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertTrue(response.json()[0]['is_visible'])

    def test_add_to_cart_and_create_order(self):
        self.login_customer()
        add = self.client.post('/api/cart/add/', {'product_id': self.product.id, 'quantity': 2}, format='json')
        self.assertEqual(add.status_code, 201)
        order = self.client.post('/api/orders/create/', {
            'delivery_address': '45 Park Street, Bristol',
            'delivery_date': str(timezone.localdate() + timedelta(days=3)),
            'payment_method': 'sandbox',
        }, format='json')
        self.assertEqual(order.status_code, 201)
        body = order.json()
        self.assertEqual(body['total_amount'], '5.00')
        self.assertEqual(body['commission_amount'], '0.25')
        self.assertEqual(body['payment_status'], 'succeeded')
        self.assertEqual(len(body['suborders']), 1)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 18)

    def test_producer_can_only_edit_own_product(self):
        self.login_producer()
        response = self.client.patch(f'/api/products/{self.product.id}/', {'stock_quantity': 25}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['stock_quantity'], 25)

    def test_customer_cannot_use_producer_endpoint(self):
        self.login_customer()
        response = self.client.post('/api/products/', {
            'category': self.category.id,
            'name': 'Tomatoes',
            'description': 'Fresh tomatoes',
            'price': '3.00',
            'stock_quantity': 10,
            'availability': 'available',
            'unit': 'kg',
        }, format='json')
        self.assertEqual(response.status_code, 403)

    def test_admin_dashboard_requires_staff(self):
        self.login_customer()
        forbidden = self.client.get('/api/admin-dashboard/')
        self.assertEqual(forbidden.status_code, 403)
        self.client.logout()
        self.login_admin()
        allowed = self.client.get('/api/admin-dashboard/')
        self.assertEqual(allowed.status_code, 200)
        self.assertIn('recent_activity', allowed.json())

    def test_status_progression_is_enforced(self):
        self.login_customer()
        self.client.post('/api/cart/add/', {'product_id': self.product.id, 'quantity': 1}, format='json')
        created = self.client.post('/api/orders/create/', {'delivery_date': str(timezone.localdate() + timedelta(days=3))}, format='json')
        order_id = created.json()['id']
        suborder_id = created.json()['suborders'][0]['id']
        self.client.logout()
        self.login_producer()
        bad = self.client.patch(f'/api/producer-suborders/{suborder_id}/status/', {'status': 'ready'}, format='json')
        self.assertEqual(bad.status_code, 400)
        ok = self.client.patch(f'/api/producer-suborders/{suborder_id}/status/', {'status': 'confirmed'}, format='json')
        self.assertEqual(ok.status_code, 200)
        Order.objects.get(pk=order_id)


class AuthAndPermissionsTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.category = Category.objects.create(name='Dairy', slug='dairy')

    def test_customer_registration_and_login(self):
        register = self.client.post('/api/customers/register/', {
            'username': 'newcustomer',
            'email': 'newcustomer@example.com',
            'password': 'StrongPass123',
            'phone': '07700900123',
            'address': '1 Example Street',
            'postcode': 'BS1 5JG',
        }, format='json')
        self.assertEqual(register.status_code, 201)
        login = self.client.post('/api/auth/login/', {
            'username': 'newcustomer',
            'password': 'StrongPass123',
        }, format='json')
        self.assertEqual(login.status_code, 200)
        self.assertEqual(login.json()['role'], 'customer')

    def test_producer_registration_sets_role_permissions(self):
        register = self.client.post('/api/producers/register/', {
            'username': 'newproducer',
            'email': 'newproducer@example.com',
            'password': 'StrongPass123',
            'business_name': 'North Farm',
            'contact_name': 'Nora',
            'phone': '01179001234',
            'business_address': 'Farm road',
            'postcode': 'BS1 4DJ',
        }, format='json')
        self.assertEqual(register.status_code, 201)
        user = User.objects.get(username='newproducer')
        self.assertTrue(hasattr(user, 'producer_profile'))

    def test_anonymous_user_cannot_create_order(self):
        response = self.client.post('/api/orders/create/', {
            'delivery_address': '45 Park Street, Bristol',
            'delivery_date': str(timezone.localdate() + timedelta(days=3)),
        }, format='json')
        self.assertEqual(response.status_code, 403)
