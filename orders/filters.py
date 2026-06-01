import django_filters as filters
from .models import Order


class OrderFilter(filters.FilterSet):
    # Price filters
    min_price = filters.NumberFilter(field_name='total_price', lookup_expr='gte')
    max_price = filters.NumberFilter(field_name='total_price', lookup_expr='lte')

    # Date filters (using DATE type for compatibility with OpenApiTypes.DATE)
    start_date = filters.DateFilter(field_name='created_at', lookup_expr='gte')
    end_date = filters.DateFilter(field_name='created_at', lookup_expr='lte')

    # Ordering
    ordering = filters.OrderingFilter(
        fields=(
            ('created_at', 'created_at'),
            ('total_price', 'total_price'),
        ),
        field_labels={
            'created_at': 'Created at',
            'total_price': 'Total price',
        }
    )

    class Meta:
        model = Order
        fields = ['min_price', 'max_price', 'start_date', 'end_date']