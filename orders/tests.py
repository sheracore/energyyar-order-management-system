from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from users.models import Role

from .models import Product, Order, OrderItem

User = get_user_model()


class OrderModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.product1 = Product.objects.create(
            name='Product 1',
            price=Decimal('10.00')
        )
        self.product2 = Product.objects.create(
            name='Product 2',
            price=Decimal('25.50')
        )
        self.order = Order.objects.create(user=self.user)

    def test_update_total_price_when_adding_items(self):
        """Test that total_price updates correctly when adding items to order"""
        self.assertEqual(self.order.total_price, Decimal('0.00'))

        # Add first item (quantity 2 of product1: 2 * 10 = 20)
        order_item1 = OrderItem.objects.create(
            order=self.order,
            product=self.product1,
            quantity=2
        )
        self.order.refresh_from_db()
        self.assertEqual(self.order.total_price, Decimal('20.00'))

        # Add second item (quantity 1 of product2: 1 * 25.50 = 25.50)
        OrderItem.objects.create(
            order=self.order,
            product=self.product2,
            quantity=1
        )
        self.order.refresh_from_db()
        self.assertEqual(self.order.total_price, Decimal('45.50'))

        # Add more quantity to existing item (should update total)
        order_item1.quantity = 3
        order_item1.save()
        self.order.refresh_from_db()
        # New total: (3 * 10 = 30) + (1 * 25.50 = 25.50) = 55.50
        self.assertEqual(self.order.total_price, Decimal('55.50'))


class OrderViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.product = Product.objects.create(
            name='Test Product',
            price=Decimal('10.00')
        )
        self.customer = User.objects.create_user(
            username='customer',
            password='pass123',
            role=Role.CUSTOMER
        )
        self.other_customer = User.objects.create_user(
            username='other_customer',
            password='pass123',
            role=Role.CUSTOMER
        )
        self.admin = User.objects.create_user(
            username='admin',
            password='pass123',
            role=Role.ADMIN
        )

    def test_create_order_authentication_and_validation(self):
        """Test order creation: authentication required, success, and validation errors"""

        response = self.client.post(reverse('order-create'), {})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.user)
        valid_data = {
            'items': [
                {
                    'product': self.product.id,
                    'quantity': 2
                }
            ],
        }
        response = self.client.post(reverse('order-create'), valid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(Order.objects.first().user, self.user)

        invalid_data = {
            'items': []
        }
        response = self.client.post(reverse('order-create'), invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_order_retrieve_permissions(self):
        """Test that customers can only get their own orders, admins can get any order"""


        customer_order = Order.objects.create(user=self.customer, total_price=100)
        other_order = Order.objects.create(user=self.other_customer, total_price=200)


        # Test 1: Customer accessing their own order (should succeed)
        self.client.force_authenticate(user=self.customer)
        customer_order_url = reverse('order-detail', kwargs={'order_id': customer_order.id})
        response = self.client.get(customer_order_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Test 2: Customer accessing another customer's order (should fail)
        other_customer_order_url = reverse('order-detail', kwargs={'order_id': other_order.id})
        response = self.client.get(other_customer_order_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Test 3: Admin accessing customer's order (should succeed)
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(customer_order_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Test 4: Unauthenticated user (should fail)
        self.client.force_authenticate(user=None)
        response = self.client.get(customer_order_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_order_list_permissions(self):
        """Test that customers see only their orders, admins see all orders"""

        # Create orders
        customer_order1 = Order.objects.create(user=self.customer, total_price=100)
        customer_order2 = Order.objects.create(user=self.customer, total_price=200)
        other_order = Order.objects.create(user=self.other_customer, total_price=300)

        list_url = reverse('order-list')

        # Test 1: Customer sees only their orders
        self.client.force_authenticate(user=self.customer)
        response = self.client.get(list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # Only customer's 2 orders
        order_ids = [order['id'] for order in response.data]
        self.assertIn(customer_order1.id, order_ids)
        self.assertIn(customer_order2.id, order_ids)
        self.assertNotIn(other_order.id, order_ids)

        # Test 2: Admin sees all orders
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)  # All 3 orders

        # Test 3: Unauthenticated user (should fail)
        self.client.force_authenticate(user=None)
        response = self.client.get(list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_order_update_put(self):
        """Test full update of an order using PUT"""

        # Create order with initial data
        order = Order.objects.create(user=self.customer, total_price=100)

        # Create a product for order items
        product = Product.objects.create(name='Test Product 2', price=Decimal('10.00'))

        detail_url = reverse('order-detail', kwargs={'order_id': order.id})

        # Valid PUT update data (all fields required)
        put_data = {
            'items': [
                {
                    'product': product.id,
                    'quantity': 3
                }
            ],
        }

        # Test 1: Successful PUT update
        self.client.force_authenticate(user=self.customer)
        response = self.client.put(detail_url, put_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Test 2: PUT with invalid data (should fail)
        invalid_data = {'items': []}  # Empty items
        response = self.client.put(detail_url, invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Test 3: PUT on non-existent order (should fail)
        wrong_detail_url = reverse('order-detail', kwargs={'order_id': 9999})
        response = self.client.put(wrong_detail_url, put_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

