from django.db import transaction
from rest_framework import serializers
from .models import Order, Product, OrderItem


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'price']


class OrderItemSerializer(serializers.ModelSerializer):
    product = serializers.IntegerField(write_only=True, required=True)
    subtotal = serializers.SerializerMethodField()  # Calculate subtotal

    class Meta:
        model = OrderItem
        fields = [
            'id',
            'product',
            'product_id',
            'quantity',
            'price_at_order',
            'subtotal'
        ]
        read_only_fields = ['price_at_order']

    def get_subtotal(self, obj):
        return obj.quantity * obj.price_at_order

    def validate_product(self, value):
        """Validate that product exists"""
        try:
            product = Product.objects.get(id=value)
            return product
        except Product.DoesNotExist:
            raise serializers.ValidationError(f"Product with id {value} does not exist")


class OrderCreateUpdateSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, write_only=True)

    class Meta:
        model = Order
        fields = ['id', 'user', 'created_at', 'updated_at', 'total_price', 'items']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at', 'total_price']

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("Order must contain at least one item.")

        # Check for duplicate products
        product_ids = [item['product'] for item in value]
        if len(product_ids) != len(set(product_ids)):
            raise serializers.ValidationError("Duplicate products are not allowed in the same order.")

        return value

    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop('items')
        user = self.context['request'].user
        order = Order.objects.create(user=user, **validated_data)

        # TODO: this creation can be done in bulk approach(for better performance)
        for item_data in items_data:
            product = item_data['product']
            quantity = item_data['quantity']

            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                price_at_order=product.price
            )

        order.update_total_price()
        return order

    @transaction.atomic
    def update(self, instance, validated_data):
        items_data = validated_data.pop('items', None)

        # Update items
        if items_data is not None:
            for item_data in items_data:
                product = item_data['product']
                quantity = item_data['quantity']

                _, _ = OrderItem.objects.update_or_create(
                    order=instance,
                    product=product,
                    defaults={'quantity': quantity, 'price_at_order': product.price}
                )

            # Delete items not in the update
            new_product_ids = [item['product'].id for item in items_data]
            instance.items.exclude(product_id__in=new_product_ids).delete()

            instance.update_total_price()

        return instance


class OrderDetailSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)
    user_role = serializers.IntegerField(source='user.role', read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'user', 'user_name', 'user_role', 'total_price', 'items', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'user_name', 'user_role', 'total_price', 'created_at', 'updated_at']