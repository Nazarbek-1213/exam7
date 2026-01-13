from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from .models import Order
from .serializers import (OrderSerializer, CreateOrderSerializer,
                          UpdateOrderStatusSerializer)
from .services import create_order_from_cart
from core.permissions import IsAdminOrReadOnly, IsOwnerOrAdmin


class CreateOrderView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = CreateOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            order = create_order_from_cart(
                user=request.user,
                shipping_address=serializer.validated_data.get('shipping_address', ''),
                phone_number=serializer.validated_data.get('phone_number', ''),
                notes=serializer.validated_data.get('notes', '')
            )

            return Response({
                'message': 'Buyurtma muvaffaqiyatli yaratildi',
                'order': OrderSerializer(order).data
            }, status=status.HTTP_201_CREATED)

        except ValueError as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class OrderListView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Order.objects.all()
        return Order.objects.filter(user=user)


class OrderDetailView(generics.RetrieveAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsOwnerOrAdmin]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Order.objects.all()
        return Order.objects.filter(user=user)


class UpdateOrderStatusView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def patch(self, request, pk):
        order = get_object_or_404(Order, pk=pk)

        serializer = UpdateOrderStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_status = serializer.validated_data['status']

        # Status o'zgarishini tekshirish
        valid_transitions = {
            'new': ['paid', 'cancelled'],
            'paid': ['shipped', 'cancelled'],
            'shipped': ['delivered'],
            'delivered': [],
            'cancelled': []
        }

        if new_status not in valid_transitions.get(order.status, []):
            return Response({
                'error': f"{order.status} dan {new_status} ga o'tish mumkin emas"
            }, status=status.HTTP_400_BAD_REQUEST)

        order.status = new_status
        order.save()

        return Response({
            'message': 'Buyurtma statusi yangilandi',
            'order': OrderSerializer(order).data
        })


class CancelOrderView(APIView):
    permission_classes = [IsOwnerOrAdmin]

    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk)

        # Faqat egasi yoki admin bekor qilishi mumkin
        if order.user != request.user and not request.user.is_staff:
            return Response({
                'error': 'Ruxsat yo\'q'
            }, status=status.HTTP_403_FORBIDDEN)

        if not order.can_cancel:
            return Response({
                'error': 'Bu buyurtmani bekor qilish mumkin emas'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Mahsulotlarni qaytarish
        for item in order.items.all():
            if item.product:
                item.product.quantity += item.quantity
                item.product.save()

        order.status = 'cancelled'
        order.save()

        return Response({
            'message': 'Buyurtma bekor qilindi'
        })