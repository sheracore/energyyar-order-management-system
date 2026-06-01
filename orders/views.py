from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from .serializers import OrderCreateUpdateSerializer, OrderDetailSerializer
from .permissions import IsOwnerOrAdmin
from .models import Order
from .filters import OrderFilter


class OrderCreateView(APIView):

    permission_classes = [IsAuthenticated]

    @extend_schema(
        description="Retrieve a list of orders. Admin users get all orders, regular users get only their own.",
        request=OrderCreateUpdateSerializer,
        responses={
            201: OrderDetailSerializer(many=True),
            403: OpenApiResponse(description="Permission denied"),
        }
    )
    def post(self, request):
        serializer = OrderCreateUpdateSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        detail_serializer = OrderDetailSerializer(order)
        return Response(detail_serializer.data, status=status.HTTP_201_CREATED)


class OrderDetailView(APIView):
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def get_object(self, order_id):
        """Get order by id or return 404"""
        return get_object_or_404(Order, id=order_id)

    def get(self, request, order_id):
        order = self.get_object(order_id)
        self.check_object_permissions(request, order)

        serializer = OrderDetailSerializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        description="Retrieve a list of orders. Admin users get all orders, regular users get only their own.",
        request=OrderCreateUpdateSerializer,
        responses={
            200: OrderDetailSerializer(many=True),
            403: OpenApiResponse(description="Permission denied"),
        }
    )
    def put(self, request, order_id):
        """Fully update an order"""
        order = self.get_object(order_id)
        self.check_object_permissions(request, order)

        serializer = OrderCreateUpdateSerializer(
            order,
            data=request.data,
            context={'request': request, 'partial': False}
        )
        serializer.is_valid(raise_exception=True)
        updated_order = serializer.save()

        detail_serializer = OrderDetailSerializer(updated_order)
        return Response(detail_serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        description="Retrieve a list of orders. Admin users get all orders, regular users get only their own.",
        request=OrderCreateUpdateSerializer,
        responses={
            200: OrderDetailSerializer(many=True),
            403: OpenApiResponse(description="Permission denied"),
        }
    )
    def patch(self, request, order_id):
        """Partially update an order"""
        order = self.get_object(order_id)
        self.check_object_permissions(request, order)

        serializer = OrderCreateUpdateSerializer(
            order,
            data=request.data,
            context={'request': request, 'partial': True},
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        updated_order = serializer.save()

        detail_serializer = OrderDetailSerializer(updated_order)
        return Response(detail_serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, order_id):
        """Delete an order"""
        order = self.get_object(order_id)
        self.check_object_permissions(request, order)

        order.delete()
        return Response(
            {"message": "Order deleted successfully"},
            status=status.HTTP_204_NO_CONTENT
        )


class OrderListView(APIView):
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    @extend_schema(
        description="Retrieve a list of orders. Admin users get all orders, regular users get only their own.",
        parameters=[
            OpenApiParameter(
                name='start_date',
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description='Filter orders from this date (YYYY-MM-DD)',
                required=False,
            ),
            OpenApiParameter(
                name='end_date',
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description='Filter orders until this date (YYYY-MM-DD)',
                required=False,
            ),
            OpenApiParameter(
                name='min_price',
                type=OpenApiTypes.FLOAT,
                location=OpenApiParameter.QUERY,
                description='Minimum total price for orders',
                required=False,
            ),
            OpenApiParameter(
                name='max_price',
                type=OpenApiTypes.FLOAT,
                location=OpenApiParameter.QUERY,
                description='Maximum total price for orders',
                required=False,
            ),
            OpenApiParameter(
                name='ordering',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Order by field (created_at, total_price, -created_at, -total_price)',
                required=False,
            ),
        ],
        responses={
            200: OrderDetailSerializer(many=True),
            401: OpenApiResponse(description="Authentication credentials were not provided."),
        }
    )
    def get(self, request):
        if request.user.is_admin:
            orders = Order.objects.all().order_by('-created_at')
        else:
            orders = Order.objects.filter(user=request.user).order_by('-created_at')

        filterset = OrderFilter(request.GET, queryset=orders)

        if not filterset.is_valid():
            return Response(
                filterset.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        orders = filterset.qs

        serializer = OrderDetailSerializer(orders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)