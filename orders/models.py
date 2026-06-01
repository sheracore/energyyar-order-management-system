
from django.db import models
from django.conf import settings
from django.db.models import Sum, F
from django.utils import timezone



# It's better to separate product app (for real projects)
class Product(models.Model):
    name = models.CharField(max_length=100, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)


class Order(models.Model):
    # TODO: for completing the project it needs status (pending, waiting, successful, paid ,...)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    # total price is generated from all order item price including their quantities
    total_price = models.DecimalField(max_digits=12, decimal_places=2, default=0, db_index=True)
    products = models.ManyToManyField(Product, through='OrderItem')

    class Meta:
        indexes = [
            models.Index(fields=['created_at', 'total_price']),
            models.Index(fields=['user', 'created_at']),
        ]

    def update_total_price(self):
        total = self.items.aggregate(
            total=Sum(F('quantity') * F('price_at_order'))
        )['total'] or 0
        if self.total_price != total:
            self.total_price = total
            Order.objects.filter(pk=self.pk).update(
                total_price=total,
                updated_at=timezone.now()
            )


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    # It's product price at the time when order created
    price_at_order = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        # Prevent duplicate products in same order (important for data integrity)
        constraints = [
            models.UniqueConstraint(fields=['order', 'product'], name='unique_order_product')
        ]

    def save(self, *args, **kwargs):
        if not self.price_at_order:
            self.price_at_order = self.product.price
        super().save(*args, **kwargs)
        # when an order
        self.order.update_total_price()

    def delete(self, *args, **kwargs):
        order = self.order
        super().delete(*args, **kwargs)
        order.update_total_price()
